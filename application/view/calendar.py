import discord
from datetime import datetime
import calendar

# [追加] TextInputModalをインポートして時刻入力に利用
from .modal import TextInputModal

# --- 年を選択するセレクトメニュー ---
class YearSelect(discord.ui.Select):
	def __init__(self, parent_view: discord.ui.View):
		self.parent_view = parent_view
		current_year = datetime.now().year
		options = [discord.SelectOption(label=f"{year}年", value=str(year)) for year in range(current_year, current_year + 5)]
		
		super().__init__(placeholder="年を選択...", min_values=1, max_values=1, options=options)

	async def callback(self, interaction: discord.Interaction):
		self.parent_view.year = int(self.values[0])
		# 月が選択済みであれば、日の選択肢を更新
		if self.parent_view.month:
			await self.parent_view.update_day_options(interaction)
		else:
			await interaction.response.defer()

# --- 月を選択するセレクトメニュー ---
class MonthSelect(discord.ui.Select):
	def __init__(self, parent_view: discord.ui.View):
		self.parent_view = parent_view
		options = [discord.SelectOption(label=f"{month}月", value=str(month)) for month in range(1, 13)]
		super().__init__(placeholder="月を選択...", min_values=1, max_values=1, options=options)
	
	async def callback(self, interaction: discord.Interaction):
		self.parent_view.month = int(self.values[0])
		# 年が選択済みであれば、日の選択肢を更新
		if self.parent_view.year:
			await self.parent_view.update_day_options(interaction)
		else:
			await interaction.response.defer()

# --- 日を選択するセレクトメニュー ---
class DaySelect(discord.ui.Select):
	def __init__(self, parent_view: discord.ui.View):
		self.parent_view = parent_view
		# 初期状態では選択肢は空（年と月が選ばれてから更新される）
		super().__init__(placeholder="日を選択...", min_values=1, max_values=1, options=[discord.SelectOption(label="先に年と月を選択", value="0")], disabled=True)

	async def callback(self, interaction: discord.Interaction):
		self.parent_view.day = int(self.values[0])
		await interaction.response.defer()

# --- 上記のセレクトメニューをまとめるView ---
class DateSelectView(discord.ui.View):
	def __init__(self, form_view: discord.ui.View):
		super().__init__(timeout=300)
		self.form_view = form_view # 親のフォームViewを保持
		self.year = None
		self.month = None
		self.day = None

		# セレクトメニューをViewに追加
		self.year_select = YearSelect(self)
		self.month_select = MonthSelect(self)
		self.day_select = DaySelect(self)
		self.add_item(self.year_select)
		self.add_item(self.month_select)
		self.add_item(self.day_select)

	# 日の選択肢を動的に更新する関数
	async def update_day_options(self, interaction: discord.Interaction):
		# 選択された年月の最終日を取得
		_, last_day = calendar.monthrange(self.year, self.month)
		options = [discord.SelectOption(label=f"{day}日", value=str(day)) for day in range(1, last_day + 1)]
		self.day_select.options = options
		self.day_select.disabled = False
		await interaction.response.edit_message(view=self)

	@discord.ui.button(label="✅ 日付を確定", style=discord.ButtonStyle.success)
	async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.year and self.month and self.day:
			self.form_view.values["date"] = f"{self.year}/{self.month:02}/{self.day:02}"
			
			# 時刻入力用のモーダルを呼び出す
			modal = TextInputModal(
				title="時刻の入力",
				label="時刻 (HH:MM 形式)",
				style=discord.TextStyle.short,
				parent_view=self.form_view, # 戻り先はフォームView
				key="time",
				default=self.form_view.values.get("time")
			)
			await interaction.response.send_modal(modal)
			self.stop()
		else:
			await interaction.response.send_message("年・月・日をすべて選択してください。", ephemeral=True)

	@discord.ui.button(label="↩️ フォームに戻る", style=discord.ButtonStyle.grey)
	async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
		# 親Viewの表示を更新してカレンダーを閉じる
		await self.form_view.update_message(interaction)
		self.stop()