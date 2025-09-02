# application/view/recruit.py
import discord
from datetime import datetime, timedelta
import pytz

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from application.controller.GD_bot import GDBotController
	from application.model.recruit import Recruit

class MentorJoinChoiceView(discord.ui.View):
	"""メンターが参加方法を選択するためのボタンビュー"""
	def __init__(self, controller: 'GDBotController', recruit_id: int):
		super().__init__(timeout=180) # 3分でタイムアウト
		self.controller = controller
		self.recruit_id = recruit_id

	async def update_main_message(self):
		"""募集メッセージを更新する共通処理"""
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)

	@discord.ui.button(label="FB要員として参加", style=discord.ButtonStyle.primary, custom_id="join_as_mentor")
	async def join_as_mentor_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.response.edit_message(content="エラー: 募集が存在しません。", view=None)
			return

		user_id = interaction.user.id
		mentors = recruit_data.get('mentors', [])
		participants = recruit_data.get('participants', [])

		if user_id in mentors:
			await interaction.response.edit_message(content="あなたは既にFB要員として参加しています。", view=None)
			return
		if user_id in participants:
			await interaction.response.edit_message(content="あなたは既にGDメンバーとして参加しています。一度参加を取り消してから再度お試しください。", view=None)
			return

		mentors.append(user_id)
		await self.controller.recruit_model.update_recruit_mentors(self.recruit_id, mentors)
		await self.update_main_message()
		
		# [修正点2] 元のメッセージを編集して、ボタンを消す
		await interaction.response.edit_message(content="FB要員として参加しました。", view=None)
		self.stop()

	@discord.ui.button(label="GDメンバーとして参加", style=discord.ButtonStyle.secondary, custom_id="join_as_member")
	async def join_as_member_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		# [修正点2] 元のメッセージを編集して、ボタンを消す
		await interaction.response.edit_message(content="GDメンバーとして参加処理中です...", view=None)
		# JoinLeaveButtonsの通常の参加処理を呼び出す
		await JoinLeaveButtons(self.controller, self.recruit_id)._perform_join(interaction)
		self.stop()
	
	async def on_timeout(self):
		# on_timeoutではephemeralなメッセージは編集できないため、何もしない
		self.stop()

class JoinLeaveButtons(discord.ui.View):
	"""
	各募集メッセージに付与される「参加予定に追加」「参加予定を削除」「編集」ボタンのビュー。
	"""
	def __init__(self, controller: 'GDBotController', recruit: 'Recruit'):
		super().__init__(timeout=None)
		self.controller = controller
		self.recruit_id = recruit.id

		# 満員の場合、参加ボタンを無効化しスタイルを変更
		join_button = discord.ui.Button(
			label="参加予定に追加",
			style=discord.ButtonStyle.secondary if recruit.is_full() else discord.ButtonStyle.success,
			custom_id=f"join:{self.recruit_id}",
			disabled=recruit.is_full()
		)
		join_button.callback = self.join_callback
		self.add_item(join_button)

		leave_button = discord.ui.Button(label="参加予定を削除", style=discord.ButtonStyle.secondary, custom_id=f"leave:{self.recruit_id}")
		leave_button.callback = self.leave_callback
		self.add_item(leave_button)

		edit_button = discord.ui.Button(label="編集", style=discord.ButtonStyle.primary, custom_id=f"edit:{self.recruit_id}")
		edit_button.callback = self.edit_callback
		self.add_item(edit_button)

		delete_button = discord.ui.Button(label="募集を削除", style=discord.ButtonStyle.danger, custom_id=f"delete:{self.recruit_id}")
		delete_button.callback = self.delete_callback
		self.add_item(delete_button)

	async def _perform_join(self, interaction: discord.Interaction):
		"""GDメンバーとして参加する共通ロジック"""
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user_id = interaction.user.id
		participants = recruit_data.get('participants', [])
		mentors = recruit_data.get('mentors', [])

		if user_id in participants:
			await interaction.followup.send("あなたは既にGDメンバーとして参加しています。", ephemeral=True)
			return
		
		if user_id in mentors:
			await interaction.followup.send("あなたは既にFB要員として参加しています。一度参加を取り消してから再度お試しください。", ephemeral=True)
			return

		if len(participants) >= recruit_data['max_people']:
			await interaction.followup.send("この募集は満員です。", ephemeral=True)
			return

		participants.append(user_id)
		await self.controller.recruit_model.update_recruit_participants(self.recruit_id, participants)
		
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)
		
		await interaction.followup.send("GDメンバーとして参加しました。", ephemeral=True)


	async def join_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)

		mentor_role_id = self.controller.MENTOR_ROLE_ID
		user_has_mentor_role = False
		if mentor_role_id and isinstance(interaction.user, discord.Member):
			user_has_mentor_role = any(role.id == mentor_role_id for role in interaction.user.roles)

		if user_has_mentor_role:
			view = MentorJoinChoiceView(self.controller, self.recruit_id)
			await interaction.followup.send("参加方法を選択してください。", view=view, ephemeral=True)
		else:
			await self._perform_join(interaction)

	async def leave_callback(self, interaction: discord.Interaction):
		# [修正点1, 4] 不要なログをなくし、処理をシンプルにする
		await interaction.response.defer(ephemeral=True)
		
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			return # 募集がない場合は何もせず終了

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
		
		# 参加者リストまたはメンターリストから削除された場合のみメッセージを更新
		if removed:
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

	async def delete_callback(self, interaction: discord.Interaction):
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
			await interaction.followup.send("あなたには、この募集を削除する権限がありません。", ephemeral=True)
			return

		# 参加者またはメンターがいる場合は削除不可
		if recruit_data.get('participants') or recruit_data.get('mentors'):
			await interaction.followup.send("参加者またはメンターがいるため、この募集を削除できません。", ephemeral=True)
			return
		
		# 募集を削除済みにマーク
		await self.controller.recruit_model.mark_as_deleted(self.recruit_id)
		
		# メッセージを更新
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)
		
		await interaction.followup.send("募集を削除しました。", ephemeral=True)

class HeaderView(discord.ui.View):
	"""
	チャンネルのヘッダーに表示される「募集を作成」と「最新状況を反映」ボタンのビュー。
	"""
	def __init__(self):
		super().__init__(timeout=None)
		self.add_item(discord.ui.Button(label="募集を作成", style=discord.ButtonStyle.primary, custom_id="test"))