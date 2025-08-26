import discord

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from application.controller.GD_bot import GDBotController

class JoinLeaveButtons(discord.ui.View):
	"""
	各募集メッセージに付与される「参加予定に追加」「参加予定を削除」ボタンのビュー。
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

	async def join_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)
		
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user_id = interaction.user.id
		participants = recruit_data.get('participants', [])
		response_message = ""

		if user_id not in participants and len(participants) < recruit_data['max_people']:
			participants.append(user_id)
			response_message = "参加予定に追加しました。"
			await self.controller.recruit_model.update_recruit_participants(self.recruit_id, participants)
		elif user_id in participants:
			response_message = "あなたは既にこの募集に参加しています。"
		else:
			response_message = "この募集は満員です。"
		
		await interaction.followup.send(response_message, ephemeral=True)
		
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)

	async def leave_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)
		
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user_id = interaction.user.id
		participants = recruit_data.get('participants', [])
		response_message = ""

		if user_id in participants:
			participants.remove(user_id)
			response_message = "参加予定から削除しました。"
			await self.controller.recruit_model.update_recruit_participants(self.recruit_id, participants)
		else:
			response_message = "あなたはまだこの募集に参加していません。"

		await interaction.followup.send(response_message, ephemeral=True)
		
		updated_recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		channel = self.controller.bot.get_channel(self.controller.channel_id)
		if updated_recruit_data and channel:
			await self.controller._send_or_update_recruit_message(channel, updated_recruit_data)


class MakeButton(discord.ui.Button):
	"""ヘッダービュー用の「募集を作成」ボタン。"""
	def __init__(self):
		super().__init__(label="募集を作成",
						 style=discord.ButtonStyle.primary,
						 custom_id="make")

class RefreshButton(discord.ui.Button):
	"""ヘッダービュー用の「最新状況を反映」ボタン。"""
	def __init__(self):
		super().__init__(label="最新状況を反映",
						 style=discord.ButtonStyle.secondary,
						 custom_id="refresh")

	async def callback(self, it: discord.Interaction):
		from application.model.recruit import RecruitModel
		
		await it.response.defer(ephemeral=True)
		recruit_model = RecruitModel()
		all_recruits_data = await recruit_model.get_all_recruits()

		blocks = []
		for r_data in all_recruits_data:
			participants_display = [f"<@{uid}>" for uid in r_data['participants']] if r_data['participants'] else []
			is_full = len(r_data['participants']) >= r_data['max_people']
			
			l1 = f"\U0001F4C5 {r_data['date_s']}   \U0001F9D1 {len(r_data['participants'])}/{r_data['max_people']}名"
			l2 = f"{r_data['place']}"
			l3 = f"{r_data['note']}" if r_data['note'] else ""
			l4 = "\U0001F7E8 満員" if is_full else "⬜ 募集中"
			l5 = "👥 参加者: " + (", ".join(participants_display) if participants_display else "なし")
			blocks.append(f"```\n{l1}\n{l2}\n{l3}\n{l4}\n{l5}\n```")

		content = "\n".join(blocks) if blocks else "現在募集はありません。"
		await it.followup.send(content, ephemeral=True)


class HeaderView(discord.ui.View):
	"""
	チャンネルのヘッダーに表示される「募集を作成」と「最新状況を反映」ボタンのビュー。
	"""
	def __init__(self):
		super().__init__(timeout=None)
		# [変更] custom_id="make"は旧モーダル用のため、新しいフォームを呼び出す"test"に変更
		# self.add_item(MakeButton()) 
		self.add_item(discord.ui.Button(label="募集を作成", style=discord.ButtonStyle.primary, custom_id="test"))
		self.add_item(RefreshButton())