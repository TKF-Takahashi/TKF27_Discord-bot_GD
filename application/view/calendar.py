import discord
import calendar
from datetime import datetime

# [追加] TextInputModalをインポートして時刻入力に利用
from .modal import TextInputModal

class CalendarView(discord.ui.View):
	def __init__(self, parent_view: discord.ui.View):
		super().__init__(timeout=180)
		self.parent_view = parent_view
		self.year = datetime.now().year
		self.month = datetime.now().month
		self.generate_buttons()

	def generate_buttons(self):
		self.clear_items()
		
		# --- 1行目: 年月とナビゲーション ---
		self.add_item(discord.ui.Button(label="<", custom_id="prev_month", row=0))
		self.add_item(discord.ui.Button(label=f"{self.year}年 {self.month}月", disabled=True, row=0))
		self.add_item(discord.ui.Button(label=">", custom_id="next_month", row=0))

		# --- [修正] 2行目以降: rowパラメータを削除し、自動レイアウトに任せる ---
		for day in ["月", "火", "水", "木", "金", "土", "日"]:
			self.add_item(discord.ui.Button(label=day, style=discord.ButtonStyle.secondary, disabled=True))

		cal = calendar.Calendar(firstweekday=0) # 月曜日始まり
		for day in cal.itermonthdays(self.year, self.month):
			if day == 0:
				self.add_item(discord.ui.Button(label="\u200b", style=discord.ButtonStyle.secondary, disabled=True))
			else:
				self.add_item(discord.ui.Button(label=str(day), custom_id=f"day_{day}"))
		
		# --- 最終行: 戻るボタンを明示的に配置 ---
		# (自動レイアウトのため、row番号は大きめの値を指定して最後にくるようにする)
		self.add_item(discord.ui.Button(label="フォームに戻る", style=discord.ButtonStyle.danger, custom_id="back_to_form", row=4))

	async def interaction_check(self, interaction: discord.Interaction):
		custom_id = interaction.data["custom_id"]
		
		if custom_id == "prev_month":
			self.month -= 1
			if self.month == 0:
				self.month = 12
				self.year -= 1
			self.generate_buttons()
			await interaction.response.edit_message(view=self)
		
		elif custom_id == "next_month":
			self.month += 1
			if self.month == 13:
				self.month = 1
				self.year += 1
			self.generate_buttons()
			await interaction.response.edit_message(view=self)
		
		elif custom_id.startswith("day_"):
			day = int(custom_id.split("_")[1])
			self.parent_view.values["date"] = f"{self.year}/{self.month:02}/{day:02}"
			# 日付選択後、時刻入力用のモーダルを呼び出す
			modal = TextInputModal(
				title="時刻の入力",
				label="時刻 (HH:MM 形式)",
				style=discord.TextStyle.short,
				parent_view=self.parent_view,
				key="time",
				default=self.parent_view.values.get("time") # 既存の値があれば引き継ぐ
			)
			await interaction.response.send_modal(modal)
			self.stop()

		elif custom_id == "back_to_form":
			# 親Viewの表示を更新してカレンダーを閉じる
			await self.parent_view.update_message(interaction)
			self.stop()
			
		return True # interaction_check内で応答するためTrueを返す