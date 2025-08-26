import re
import discord
from datetime import datetime

if False:
	from application.controller.GD_bot import GDBotController
	from application.view.form_view import RecruitFormView

# [削除] RecruitModalクラスを削除

class TextInputModal(discord.ui.Modal):
	def __init__(self, title: str, label: str, style: discord.TextStyle, parent_view: discord.ui.View, key: str, default: str = None):
		super().__init__(title=title)
		self.parent_view = parent_view
		self.key = key
		
		self.text_input = discord.ui.TextInput(
			label=label,
			style=style,
			default=default if default != "未設定" else None
		)
		self.add_item(self.text_input)

	async def on_submit(self, interaction: discord.Interaction):
		self.parent_view.values[self.key] = self.text_input.value
		await self.parent_view.update_message(interaction)

class DateInputModal(discord.ui.Modal, title="日付入力"):
	def __init__(self, parent_view: 'RecruitFormView'):
		super().__init__()
		self.parent_view = parent_view

	month_input = discord.ui.TextInput(
		label="月 (1-12の数字)",
		placeholder="例: 8",
		required=True,
		max_length=2
	)
	day_input = discord.ui.TextInput(
		label="日 (1-31の数字)",
		placeholder="例: 26",
		required=True,
		max_length=2
	)

	async def on_submit(self, interaction: discord.Interaction):
		try:
			month = int(self.month_input.value)
			day = int(self.day_input.value)
			
			now = datetime.now()
			year = now.year
			
			event_dt_this_year = datetime(year, month, day)

			if event_dt_this_year < now:
				year += 1

		except (ValueError, TypeError):
			await interaction.response.send_message("月または日が数字でないか、存在しない日付です。", ephemeral=True)
			return
		
		self.parent_view.values["date"] = f"{year}/{month:02}/{day:02}"
		await self.parent_view.add_time_selectors(interaction)