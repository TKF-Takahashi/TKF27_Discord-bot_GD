# application/view/recruit.py
import discord
from typing import TYPE_CHECKING
from application.model.recruit import Recruit
from application.view.modal import RecruitEditModal, ConfirmModal

if TYPE_CHECKING:
	from application.controller.GD_bot import GDBotController

class HeaderView(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@discord.ui.button(label="新規募集", style=discord.ButtonStyle.primary, custom_id="test")
	async def new_recruit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		pass

class MentorJoinChoiceView(discord.ui.View):
	def __init__(self, controller: "GDBotController", recruit_id: int):
		super().__init__(timeout=180)
		self.controller = controller
		self.recruit_id = recruit_id
		self.message: discord.Message = None

	@discord.ui.button(label="メンターとして参加", style=discord.ButtonStyle.success)
	async def join_as_mentor_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		await JoinLeaveButtons(self.controller, self.recruit_id)._perform_join(interaction, as_mentor=True)
		self.stop()
		if self.message:
			await self.message.delete()

	@discord.ui.button(label="GDメンバーとして参加", style=discord.ButtonStyle.secondary)
	async def join_as_member_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		await JoinLeaveButtons(self.controller, self.recruit_id)._perform_join(interaction)
		self.stop()
		if self.message:
			await self.message.delete()
			
	async def on_timeout(self):
		if self.message:
			try:
				await self.message.delete()
			except discord.NotFound:
				pass

class JoinLeaveButtons(discord.ui.View):
	def __init__(self, controller: "GDBotController", recruit: 'Recruit'):
		super().__init__(timeout=None)
		self.controller = controller
		# ▼▼▼【修正】オブジェクトとID（数値）の両方に対応 ▼▼▼
		if isinstance(recruit, int):
			self.recruit_id = recruit
		else:
			self.recruit_id = recruit.id
		# ▲▲▲【修正】ここまで ▲▲▲

	async def _perform_join(self, interaction: discord.Interaction, as_mentor: bool = False):
		user = interaction.user
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		
		if not recruit_data:
			await interaction.followup.send("エラー: 募集が見つかりません。", ephemeral=True)
			return
			
		participants = set(recruit_data.get('participants', []))
		mentors = set(recruit_data.get('mentors', []))

		if user.id in participants or user.id in mentors:
			await interaction.followup.send("すでに追加されています。", ephemeral=True)
			return
			
		if len(participants) >= recruit_data['max_people'] and not as_mentor:
			await interaction.followup.send("この募集は満員です。", ephemeral=True)
			return

		if as_mentor:
			await self.controller.recruit_model.add_mentor(self.recruit_id, user.id)
		else:
			await self.controller.recruit_model.add_participant(self.recruit_id, user.id)

		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		ch = self.controller.bot.get_channel(self.controller.channel_id)
		
		if ch:
			await self.controller._send_or_update_recruit_message(ch, updated_recruit_data)
			await interaction.followup.send(f"{'メンターとして' if as_mentor else ''}参加登録しました。", ephemeral=True)
		else:
			await interaction.followup.send("エラー: チャンネルが見つかりません。", ephemeral=True)

	async def _perform_leave(self, interaction: discord.Interaction):
		await self.controller.recruit_model.remove_participant(self.recruit_id, interaction.user.id)
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		ch = self.controller.bot.get_channel(self.controller.channel_id)
		
		if ch:
			await self.controller._send_or_update_recruit_message(ch, updated_recruit_data)
			await interaction.followup.send("参加を取り消しました。", ephemeral=True)
		else:
			await interaction.followup.send("エラー: チャンネルが見つかりません。", ephemeral=True)

	@discord.ui.button(label="参加予定に追加", style=discord.ButtonStyle.success)
	async def join_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		# ▼▼▼【修正】不要なdeferを削除 ▼▼▼
		# await interaction.response.defer(ephemeral=True)
		# ▲▲▲【修正】ここまで ▲▲▲
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if recruit_data.get('mentor_needed'):
			view = MentorJoinChoiceView(self.controller, self.recruit_id)
			msg = await interaction.followup.send("参加種別を選択してください。", view=view, ephemeral=True)
			view.message = msg
		else:
			await self._perform_join(interaction)

	@discord.ui.button(label="参加を取り消す", style=discord.ButtonStyle.danger)
	async def leave_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self._perform_leave(interaction)
		
	@discord.ui.button(label="編集", style=discord.ButtonStyle.secondary, emoji="✏️")
	async def edit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		author_id = recruit_data.get('author_id')
		
		is_admin = False
		if self.controller.ADMIN_ROLE_ID:
			admin_role = interaction.guild.get_role(self.controller.ADMIN_ROLE_ID)
			if admin_role and admin_role in interaction.user.roles:
				is_admin = True
		
		if interaction.user.id == author_id or is_admin:
			modal = RecruitEditModal(self.controller, recruit_data)
			await interaction.response.send_modal(modal)
		else:
			await interaction.followup.send("募集者ご本人か、管理者のみ編集できます。", ephemeral=True)

	@discord.ui.button(label="削除", style=discord.ButtonStyle.secondary, emoji="🗑️")
	async def delete_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		author_id = recruit_data.get('author_id')
		
		is_admin = False
		if self.controller.ADMIN_ROLE_ID:
			admin_role = interaction.guild.get_role(self.controller.ADMIN_ROLE_ID)
			if admin_role and admin_role in interaction.user.roles:
				is_admin = True

		if interaction.user.id == author_id or is_admin:
			async def on_confirm(confirm_interaction: discord.Interaction):
				await self.controller.recruit_model.mark_as_deleted(self.recruit_id)
				updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
				ch = self.controller.bot.get_channel(self.controller.channel_id)
				if ch:
					await self.controller._send_or_update_recruit_message(ch, updated_recruit_data)
				await confirm_interaction.response.send_message("募集を削除しました。", ephemeral=True)
			
			confirm_modal = ConfirmModal(
				title="募集の削除確認",
				label="本当にこの募集を削除しますか？",
				on_confirm=on_confirm
			)
			await interaction.response.send_message(view=confirm_modal, ephemeral=True)
		else:
			await interaction.followup.send("募集者ご本人か、管理者のみ削除できます。", ephemeral=True)
			
	@discord.ui.button(label="イベント作成", style=discord.ButtonStyle.secondary, emoji="🗓️", custom_id="event")
	async def create_event_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		button.custom_id=f"event:{self.recruit_id}"