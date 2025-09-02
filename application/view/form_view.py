# application/view/form_view.py
import discord
from datetime import datetime
from .modal import TextInputModal, DateInputModal
import re

if False:
	from application.controller.GD_bot import GDBotController

class HourSelect(discord.ui.Select):
	def __init__(self, default_hour: str = None):
		hours = [f"{h:02}" for h in range(8, 24)] + [f"{h:02}" for h in range(0, 8)]
		options = [discord.SelectOption(label=f"{h}時", value=h) for h in hours]
		if default_hour and default_hour != "未設定":
			for option in options:
				if option.value == default_hour:
					option.default = True
					break
		super().__init__(placeholder="時を選択...", options=options)

	async def callback(self, interaction: discord.Interaction):
		selected_hour = self.values[0]
		self.view.values["time_hour"] = selected_hour
		await self.view.update_message(interaction)

class MinuteSelect(discord.ui.Select):
	def __init__(self, default_minute: str = None):
		options = [discord.SelectOption(label=f"{m:02}分", value=f"{m:02}") for m in range(0, 60, 5)]
		if default_minute and default_minute != "未設定":
			for option in options:
				if option.value == default_minute:
					option.default = True
					break
		super().__init__(placeholder="分を選択...", options=options)
	
	async def callback(self, interaction: discord.Interaction):
		selected_minute = self.values[0]
		self.view.values["time_minute"] = selected_minute
		await self.view.update_message(interaction)

class IndustrySelect(discord.ui.Select):
	def __init__(self, default_industry: str = None):
		options = [
			discord.SelectOption(label="メーカー", value="メーカー"),
			discord.SelectOption(label="コンサル", value="コンサル"),
			discord.SelectOption(label="インフラ", value="インフラ"),
			discord.SelectOption(label="金融", value="金融"),
			discord.SelectOption(label="人材", value="人材"),
			discord.SelectOption(label="官公庁", value="官公庁"),
			discord.SelectOption(label="IT/通信", value="IT/通信"),
			discord.SelectOption(label="総合商社・専門商社", value="総合商社・専門商社"),
			discord.SelectOption(label="広告・出版・マスコミ", value="広告・出版・マスコミ"),
			discord.SelectOption(label="デベロッパー・不動産・建築", value="デベロッパー・不動産・建築"),
			discord.SelectOption(label="航空・鉄道・海運・その他運輸", value="航空・鉄道・海運・その他運輸"),
			discord.SelectOption(label="保険会社", value="保険会社"),
		]
		if default_industry and default_industry != "未設定":
			for option in options:
				if option.value == default_industry:
					option.default = True
					break
		super().__init__(placeholder="想定業界を選択...", options=options)
	
	async def callback(self, interaction: discord.Interaction):
		self.view.values["industry"] = self.values[0]
		for option in self.options:
			option.default = option.value == self.values[0]
		await self.view.update_message(interaction)

class CapacitySelect(discord.ui.Select):
	def __init__(self, default_capacity: str = None):
		options = [discord.SelectOption(label=f"{i}人", value=str(i)) for i in range(3, 11)]
		if default_capacity and default_capacity != "未設定":
			for option in options:
				if option.value == default_capacity:
					option.default = True
					break
		super().__init__(placeholder="定員を選択...", options=options)
	
	async def callback(self, interaction: discord.Interaction):
		self.view.values["capacity"] = self.values[0]
		await self.view.show_main_screen(interaction)

# ▼▼▼【修正】Viewの構造を全面的に見直し、ボタンごとにコールバックを定義 ▼▼▼
class RecruitFormView(discord.ui.View):
	def __init__(self, controller: 'GDBotController', initial_data: dict = None, recruit_id: int = None):
		super().__init__(timeout=600)
		self.controller = controller
		self.recruit_id = recruit_id
		self.message_to_delete: discord.Message = None
		self.values = {
			"date": "未設定",
			"time_hour": "未設定",
			"time_minute": "未設定",
			"place": "未設定",
			"capacity": "未設定",
			"note_message": "未設定",
			"mentor_needed": False,
			"industry": "未設定"
		}

		if initial_data:
			self.populate_initial_data(initial_data)
		
		self.show_main_screen()

	def populate_initial_data(self, data: dict):
		self.values["place"] = data.get("place", "未設定")
		self.values["capacity"] = str(data.get("max_people", "未設定"))
		if data.get("date_s"):
			try:
				dt_obj = datetime.strptime(data["date_s"], "%Y/%m/%d %H:%M")
				self.values["date"] = dt_obj.strftime("%Y/%m/%d")
				self.values["time_hour"] = dt_obj.strftime("%H")
				self.values["time_minute"] = dt_obj.strftime("%M")
			except ValueError:
				pass
		self.values["note_message"] = data.get("message", "未設定")
		self.values["mentor_needed"] = data.get("mentor_needed", 0) == 1
		self.values["industry"] = data.get("industry", "未設定")
	
	def clear_and_set_screen(self, screen_name: str):
		self.clear_items()
		self.current_screen = screen_name

	async def update_message(self, interaction: discord.Interaction):
		embed = self.create_embed()
		kwargs = {'embed': embed, 'view': self}
		if interaction.response.is_done():
			await interaction.followup.edit_message(message_id=interaction.message.id, **kwargs)
		else:
			await interaction.response.edit_message(**kwargs)

	def create_embed(self):
		embed = discord.Embed(title="募集作成フォーム")
		embed.description = "下のボタンを押して各項目を入力してください。"
		
		datetime_val = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
		if "未設定" in datetime_val:
			datetime_val = "未設定"
		
		mentor_status = "呼ぶ" if self.values['mentor_needed'] else "呼ばない"
		
		embed.add_field(name="📅 日時", value=datetime_val, inline=False)
		embed.add_field(name="📍 場所", value=self.values['place'], inline=False)
		embed.add_field(name="👥 定員", value=self.values['capacity'], inline=False)
		embed.add_field(name="📝 備考", value=f"メッセージ: {self.values['note_message']}\nメンター: {mentor_status}\n想定業界: {self.values['industry']}", inline=False)
		return embed

	def add_back_button(self):
		back_button = discord.ui.Button(label="↩️ フォームに戻る", style=discord.ButtonStyle.grey, custom_id="back_to_main")
		back_button.callback = self.show_main_screen
		self.add_item(back_button)

	def show_main_screen(self, interaction: discord.Interaction = None):
		self.clear_and_set_screen("main")
		
		# ボタンの追加
		date_button = discord.ui.Button(label="📅 日付設定", style=discord.ButtonStyle.secondary, custom_id="set_date")
		date_button.callback = self.on_set_date
		self.add_item(date_button)

		place_button = discord.ui.Button(label="📍 場所設定", style=discord.ButtonStyle.secondary, custom_id="set_place")
		place_button.callback = self.on_set_place
		self.add_item(place_button)
		
		capacity_button = discord.ui.Button(label="👥 定員設定", style=discord.ButtonStyle.secondary, custom_id="set_capacity")
		capacity_button.callback = self.on_set_capacity
		self.add_item(capacity_button)

		note_button = discord.ui.Button(label="📝 備考設定", style=discord.ButtonStyle.secondary, custom_id="set_note")
		note_button.callback = self.on_set_note
		self.add_item(note_button)

		required_filled = all(self.values[key] != "未設定" for key in ["date", "time_hour", "time_minute", "place", "capacity"])
		
		if self.recruit_id:
			submit_button = discord.ui.Button(label="✅ 募集を更新", style=discord.ButtonStyle.success, custom_id="update_recruit")
			submit_button.callback = self.on_submit
		else:
			submit_button = discord.ui.Button(label="✅ 募集を作成", style=discord.ButtonStyle.success, custom_id="create_recruit", disabled=not required_filled)
			submit_button.callback = self.on_submit
		self.add_item(submit_button)
		
		if interaction:
			return self.update_message(interaction)

	async def on_set_date(self, interaction: discord.Interaction):
		modal = DateInputModal(parent_view=self)
		await interaction.response.send_modal(modal)

	async def on_set_place(self, interaction: discord.Interaction):
		modal = TextInputModal(title="場所の入力", label="開催場所 (Zoomなど)", style=discord.TextStyle.short, parent_view=self, key="place", default=self.values["place"])
		await interaction.response.send_modal(modal)

	async def on_set_capacity(self, interaction: discord.Interaction):
		self.clear_and_set_screen("capacity")
		self.add_item(CapacitySelect(default_capacity=self.values["capacity"]))
		self.add_back_button()
		await self.update_message(interaction)
	
	async def on_set_note(self, interaction: discord.Interaction):
		self.clear_and_set_screen("note")
		
		message_button = discord.ui.Button(label="✉️ メッセージ", style=discord.ButtonStyle.secondary, custom_id="set_note_message")
		message_button.callback = self.on_set_note_message
		self.add_item(message_button)
		
		mentor_label = "メンター: ON" if self.values["mentor_needed"] else "メンター: OFF"
		mentor_style = discord.ButtonStyle.success if self.values["mentor_needed"] else discord.ButtonStyle.danger
		mentor_button = discord.ui.Button(label=mentor_label, style=mentor_style, custom_id="toggle_mentor")
		mentor_button.callback = self.on_toggle_mentor
		self.add_item(mentor_button)

		self.add_item(IndustrySelect(default_industry=self.values["industry"]))
		self.add_back_button()
		await self.update_message(interaction)
	
	async def on_set_note_message(self, interaction: discord.Interaction):
		modal = TextInputModal(title="備考メッセージ入力", label="メッセージ", style=discord.TextStyle.paragraph, parent_view=self, key="note_message", default=self.values["note_message"])
		await interaction.response.send_modal(modal)

	async def on_toggle_mentor(self, interaction: discord.Interaction):
		self.values["mentor_needed"] = not self.values["mentor_needed"]
		await self.on_set_note(interaction)

	async def on_submit(self, interaction: discord.Interaction):
		try:
			date_s = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
			datetime.strptime(date_s, "%Y/%m/%d %H:%M")
			cap_int = int(self.values['capacity'])
			if cap_int <= 0: raise ValueError
			
			data_payload = {
				'date_s': date_s,
				'place': self.values['place'],
				'max_people': cap_int,
				'message': self.values['note_message'] if self.values['note_message'] != "未設定" else None,
				'mentor_needed': self.values['mentor_needed'],
				'industry': self.values['industry'] if self.values['industry'] != "未設定" else None
			}
		except (ValueError, TypeError):
			if not interaction.response.is_done():
				await interaction.response.send_message("日時または定員の形式が正しくありません。入力し直してください。", ephemeral=True)
			return

		await interaction.response.edit_message(content="処理中です...", embed=None, view=None)
		self.message_to_delete = await interaction.original_response()

		if self.recruit_id:
			await self.controller.handle_recruit_update(interaction, self.recruit_id, data_payload, self.message_to_delete)
		else:
			await self.controller.handle_recruit_submission(interaction, data_payload, self.message_to_delete)
		
		self.stop()

	async def show_time_selectors(self, interaction: discord.Interaction):
		self.clear_and_set_screen("time")
		self.add_item(HourSelect(default_hour=self.values["time_hour"]))
		self.add_item(MinuteSelect(default_minute=self.values["time_minute"]))
		
		confirm_button = discord.ui.Button(label="✅ 時間を登録", style=discord.ButtonStyle.success, custom_id="confirm_time")
		confirm_button.callback = self.on_confirm_time
		self.add_item(confirm_button)

		await self.update_message(interaction)

	async def on_confirm_time(self, interaction: discord.Interaction):
		if all(self.values[key] != "未設定" for key in ["time_hour", "time_minute"]):
			await self.show_main_screen(interaction)
		else:
			# 本来はここに到達しないはずだが、念のため
			await interaction.response.send_message("時間と分を選択してください。", ephemeral=True, delete_after=5)