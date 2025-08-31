# application/view/recruit.py
import discord
from datetime import datetime, timedelta
import pytz

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from application.controller.GD_bot import GDBotController

class MentorJoinChoiceView(discord.ui.View):
	"""メンターが参加方法を選択するためのボタンビュー"""
	def __init__(self, controller: 'GDBotController', recruit_id: int):
		super().__init__(timeout=180) # 3分でタイムアウト
		self.controller = controller
		self.recruit_id = recruit_id

	@discord.ui.button(label="FB要員として参加", style=discord.ButtonStyle.primary, custom_id="join_as_mentor")
	async def join_as_mentor_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.response.send_message("エラー: 募集が存在しません。", ephemeral=True)
			return

		user_id = interaction.user.id
		mentors = recruit_data.get('mentors', [])
		participants = recruit_data.get('participants', [])

		if user_id in mentors:
			await interaction.response.send_message("あなたは既にFB要員として参加しています。", ephemeral=True)
			return
		if user_id in participants:
			await interaction.response.send_message("あなたは既にGDメンバーとして参加しています。一度参加を取り消してから再度お試しください。", ephemeral=True)
			return

		mentors.append(user_id)
		await self.controller.recruit_model.update_recruit_mentors(self.recruit_id, mentors)
		
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)
		
		await interaction.response.send_message("FB要員として参加しました。", ephemeral=True)
		self.stop()

	@discord.ui.button(label="GDメンバーとして参加", style=discord.ButtonStyle.secondary, custom_id="join_as_member")
	async def join_as_member_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		# JoinLeaveButtonsの通常の参加処理を呼び出す
		await JoinLeaveButtons(self.controller, self.recruit_id)._perform_join(interaction)
		await interaction.response.send_message("GDメンバーとして参加しました。", ephemeral=True)
		self.stop()
	
	async def on_timeout(self):
		# タイムアウトした場合、ボタンを無効化する
		for item in self.children:
			item.disabled = True
		# 元のメッセージを編集してボタンを無効化
		# このビューはephemeralなので、interaction.edit_original_response()は使えない
		pass

class JoinLeaveButtons(discord.ui.View):
	"""
	各募集メッセージに付与される「参加予定に追加」「参加予定を削除」「編集」ボタンのビュー。
	"""
	def __init__(self, controller: 'GDBotController', recruit_id: int):
		super().__init__(timeout=None)
		self.controller = controller
		self.recruit_id = recruit_id

		join_button = discord.ui.Button(label="参加予定に追加", style=discord.ButtonStyle.success, custom_id=f"join:{self.recruit_id}")
		join_button.callback = self.join_callback
		self.add_item(join_button)

		leave_button = discord.ui.Button(label="参加予定を削除", style=discord.ButtonStyle.secondary, custom_id=f"leave:{self.recruit_id}")
		leave_button.callback = self.leave_callback
		self.add_item(leave_button)

		edit_button = discord.ui.Button(label="編集", style=discord.ButtonStyle.primary, custom_id=f"edit:{self.recruit_id}")
		edit_button.callback = self.edit_callback
		self.add_item(edit_button)

	async def _perform_join(self, interaction: discord.Interaction):
		"""GDメンバーとして参加する共通ロジック"""
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			if not interaction.response.is_done():
				await interaction.response.send_message("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			else:
				await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user_id = interaction.user.id
		participants = recruit_data.get('participants', [])
		mentors = recruit_data.get('mentors', [])

		if user_id in participants:
			if not interaction.response.is_done():
				await interaction.response.send_message("あなたは既にGDメンバーとして参加しています。", ephemeral=True)
			else:
				await interaction.followup.send("あなたは既にGDメンバーとして参加しています。", ephemeral=True)
			return
		
		if user_id in mentors:
			if not interaction.response.is_done():
				await interaction.response.send_message("あなたは既にFB要員として参加しています。一度参加を取り消してから再度お試しください。", ephemeral=True)
			else:
				await interaction.followup.send("あなたは既にFB要員として参加しています。一度参加を取り消してから再度お試しください。", ephemeral=True)
			return

		if len(participants) >= recruit_data['max_people']:
			if not interaction.response.is_done():
				await interaction.response.send_message("この募集は満員です。", ephemeral=True)
			else:
				await interaction.followup.send("この募集は満員です。", ephemeral=True)
			return

		participants.append(user_id)
		await self.controller.recruit_model.update_recruit_participants(self.recruit_id, participants)
		
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)

	async def join_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)

		mentor_role_id = self.controller.MENTOR_ROLE_ID
		user_has_mentor_role = False
		if mentor_role_id and isinstance(interaction.user, discord.Member):
			user_has_mentor_role = any(role.id == mentor_role_id for role in interaction.user.roles)

		if user_has_mentor_role:
			# メンターロールを持っている場合、選択肢を提示
			view = MentorJoinChoiceView(self.controller, self.recruit_id)
			await interaction.followup.send("参加方法を選択してください。", view=view, ephemeral=True)
		else:
			# 持っていない場合、通常の参加処理
			await self._perform_join(interaction)
			await interaction.followup.send("参加しました。", ephemeral=True)


	async def leave_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)
		
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user_id = interaction.user.id
		participants = recruit_data.get('participants', [])
		mentors = recruit_data.get('mentors', [])
		
		removed = False
		if user_id in participants:
			participants.remove(user_id)
			await self.controller.recruit_model.update_recruit_participants(self.recruit_id, participants)
			removed = True
		elif user_id in mentors:
			mentors.remove(user_id)
			await self.controller.recruit_model.update_recruit_mentors(self.recruit_id, mentors)
			removed = True
		else:
			await interaction.followup.send("あなたはこの募集に参加していません。", ephemeral=True)
			return
		
		if removed:
			await interaction.followup.send("参加を取り消しました。", ephemeral=True)

		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)

	async def edit_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)

		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user = interaction.user
		author_id = recruit_data.get('author_id')
		edit_role_id = self.controller.EDIT_ROLE_ID

		is_authorized = False
		if isinstance(user, discord.Member):
			is_authorized = user.id == author_id or any(role.id == edit_role_id for role in user.roles)

		if not is_authorized:
			await interaction.followup.send("あなたには、この募集を編集する権限がありません。", ephemeral=True)
		else:
			from application.view.form_view import RecruitFormView
			form_view = RecruitFormView(self.controller, initial_data=recruit_data, recruit_id=self.recruit_id)
			embed = form_view.create_embed()
			await interaction.followup.send(embed=embed, view=form_view, ephemeral=True)

class HeaderView(discord.ui.View):
	"""
	チャンネルのヘッダーに表示される「募集を作成」と「最新状況を反映」ボタンのビュー。
	"""
	def __init__(self):
		super().__init__(timeout=None)
		self.add_item(discord.ui.Button(label="募集を作成", style=discord.ButtonStyle.primary, custom_id="test"))