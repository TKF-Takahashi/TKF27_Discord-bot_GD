# application/view/recruit.py
import discord
from datetime import datetime, timedelta
import pytz

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from application.controller.GD_bot import GDBotController

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

	async def join_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)
		
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user_id = interaction.user.id
		participants = recruit_data.get('participants', [])
		if user_id in participants:
			await interaction.followup.send("あなたは既にこの募集に参加しています。", ephemeral=True)
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

	async def leave_callback(self, interaction: discord.Interaction):
		await interaction.response.defer(ephemeral=True)
		
		recruit_data = await self.controller.recruit_model.get_recruit_by_id(self.recruit_id)
		if not recruit_data:
			await interaction.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		user_id = interaction.user.id
		participants = recruit_data.get('participants', [])

		if user_id in participants:
			participants.remove(user_id)
			await self.controller.recruit_model.update_recruit_participants(self.recruit_id, participants)
		else:
			await interaction.followup.send("あなたはまだこの募集に参加していません。", ephemeral=True)
		
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

		has_role = any(role.id == edit_role_id for role in user.roles)
		is_author = user.id == author_id

		if not is_author and not has_role:
			await interaction.followup.send("あなたには、この募集を編集する権限がありません。", ephemeral=True)
			return
		
		from application.view.form_view import RecruitFormView
		form_view = RecruitFormView(self.controller, initial_data=recruit_data, recruit_id=self.recruit_id)
		embed = form_view.create_embed()
		await interaction.followup.send(embed=embed, view=form_view, ephemeral=True)


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
		
		jst = pytz.timezone('Asia/Tokyo')
		now_jst = datetime.now(jst)

		blocks = []
		for r_data in all_recruits_data:
			try:
				# 募集日時をdatetimeオブジェクトに変換し、タイムゾーン情報を持たせる
				recruit_datetime_naive = datetime.strptime(r_data['date_s'], "%Y/%m/%d %H:%M")
				recruit_datetime = jst.localize(recruit_datetime_naive)
				
				# 1時間以上経過しているかを確認
				if recruit_datetime < now_jst - timedelta(hours=1):
					# 終了した募集の表示形式
					l1 = f"【終了】{r_data['date_s']}"
					l2 = f"{r_data['place']}"
					l3 = f"{r_data['note']}" if r_data['note'] else ""
					l4 = "" # 終了した募集のためステータスを非表示
					l5 = "" # 参加者リストを非表示
					# ブロック引用符で囲み、灰色っぽく表示
					blocks.append(f"> ```\n> {l1}\n> {l2}\n> {l3}\n> {l4}\n> {l5}\n> ```")
					continue
				
				# 1時間未満の過去の募集、または未来の募集は通常通り表示
				participants_display = [f"<@{uid}>" for uid in r_data['participants']] if r_data['participants'] else []
				is_full = len(r_data['participants']) >= r_data['max_people']
				
				l1 = f"\U0001F4C5 {r_data['date_s']}   \U0001F9D1 {len(r_data['participants'])}/{r_data['max_people']}名"
				l2 = f"{r_data['place']}"
				l3 = f"{r_data['note']}" if r_data['note'] else ""
				l4 = "\U0001F7E8 満員" if is_full else "⬜ 募集中"
				l5 = "👥 参加者: " + (", ".join(participants_display) if participants_display else "なし")
				blocks.append(f"```\n{l1}\n{l2}\n{l3}\n{l4}\n{l5}\n```")

			except (ValueError, KeyError, pytz.UnknownTimeZoneError):
				# 日付のパースまたはタイムゾーン設定に失敗した場合もスキップ
				continue

		content = "\n".join(blocks) if blocks else "現在募集はありません。"
		await it.followup.send(content, ephemeral=True)


class HeaderView(discord.ui.View):
	"""
	チャンネルのヘッダーに表示される「募集を作成」と「最新状況を反映」ボタンのビュー。
	"""
	def __init__(self):
		super().__init__(timeout=None)
		# custom_id="make"は旧モーダル用のため、新しいフォームを呼び出す"test"に変更
		self.add_item(discord.ui.Button(label="募集を作成", style=discord.ButtonStyle.primary, custom_id="test"))
		self.add_item(RefreshButton())