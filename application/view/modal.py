# application/view/modal.py
import re
import discord

# 変更: コントローラーのインポートパス
# GD_bot_controllerのインスタンスを保持するため、型ヒントを遅延評価
# 循環参照を避けるため、直接インポートせず文字列として指定
if False: # 実行時には評価されないようにダミーの条件
	from application.controller.GD_bot import GDBotController # 型ヒントのためだけに定義

class RecruitModal(discord.ui.Modal, title="GD練習 募集作成フォーム"):
	"""募集作成のためのモーダルフォーム"""
	md = discord.ui.TextInput(label="日付 (MM/DD)",
							placeholder="06/30",
							max_length=5,
							required=True)
	hm = discord.ui.TextInput(label="時刻 (HH:MM)",
							placeholder="18:00",
							max_length=5,
							required=True)
	place = discord.ui.TextInput(label="場所（Zoomなど）", required=True)
	cap = discord.ui.TextInput(label="募集人数",
							placeholder="4",
							max_length=3,
							required=True)
	note = discord.ui.TextInput(label="備考（任意）", required=False, style=discord.TextStyle.paragraph)

	def __init__(self, controller: 'GDBotController'): # 遅延評価の型ヒント
		super().__init__()
		self.controller = controller # コントローラーインスタンスを保持

	async def on_submit(self, it: discord.Interaction):
		await it.response.defer(ephemeral=True) # 応答を遅延

		# 入力値のバリデーション
		if not re.fullmatch(r"\d{1,2}/\d{1,2}", self.md.value) or \
			not re.fullmatch(r"\d{1,2}:\d{1,2}", self.hm.value):
			return await it.followup.send("日付は MM/DD、時刻は HH:MM 形式で入力してください。", ephemeral=True)
		
		try:
			m, d = map(int, self.md.value.split("/"))
			h, mi = map(int, self.hm.value.split(":"))
		except ValueError:
			return await it.followup.send("日付または時刻の形式が正しくありません。", ephemeral=True)

		if not (1 <= m <= 12 and 1 <= d <= 31 and 0 <= h <= 23 and 0 <= mi <= 59):
			return await it.followup.send("日付または時刻が範囲外です。", ephemeral=True)
		
		try:
			cap_int = int(self.cap.value)
			if cap_int <= 0:
				return await it.followup.send("募集人数は1以上の数値で入力してください。", ephemeral=True)
		except ValueError:
			return await it.followup.send("募集人数は数値で入力してください。", ephemeral=True)

		date_s = f"2024/{m:02}/{d:02} {h:02}:{mi:02}" # [注意] 年を現在の年に固定しています
		
		# コントローラーのメソッドを呼び出し、実際の募集作成処理を委譲
		await self.controller.handle_recruit_submission(it, {
			'date_s': date_s,
			'place': self.place.value,
			'max_people': cap_int,
			'note': self.note.value
		})

# [追加] フォーム機能から呼び出すための、汎用的なテキスト入力モーダル
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

# [新規追加] 新しい日時入力用モーダル
class DateTimeModal(discord.ui.Modal, title="日時入力"):
	def __init__(self, parent_view: 'RecruitFormView'):
		super().__init__()
		self.parent_view = parent_view

	md_input = discord.ui.TextInput(
		label="月/日 (MM/DD形式)",
		placeholder="例: 8/26",
		required=True,
		max_length=5
	)
	hm_input = discord.ui.TextInput(
		label="時刻 (HH:MM形式)",
		placeholder="例: 19:00",
		required=True,
		max_length=5
	)

	async def on_submit(self, interaction: discord.Interaction):
		# 入力値のパースとバリデーション
		try:
			month_str, day_str = self.md_input.value.split('/')
			hour_str, minute_str = self.hm_input.value.split(':')
			
			month, day = int(month_str), int(day_str)
			hour, minute = int(hour_str), int(minute_str)
			
			# 日付・時刻の範囲チェック
			if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59):
				raise ValueError("Date or time out of range")

			now = datetime.now()
			year = now.year
			
			# 指定された日付が現在の日付より過去の場合、年を1つ進める
			# (例: 現在が12月で、入力が1月の場合)
			event_dt_this_year = datetime(year, month, day)
			if event_dt_this_year < now:
				year += 1

		except (ValueError, TypeError):
			await interaction.response.send_message("日付または時刻の形式が正しくありません。(例: 8/26, 19:00)", ephemeral=True)
			return
		
		# 親Viewの値を更新
		self.parent_view.values["date"] = f"{year}/{month:02}/{day:02}"
		self.parent_view.values["time"] = f"{hour:02}:{minute:02}"
		
		# フォームの表示を更新
		await self.parent_view.update_message(interaction)