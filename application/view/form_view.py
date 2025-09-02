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
		# 編集モード用にデフォルト値を設定
		if default_hour and default_hour != "未設定":
			for option in options:
				if option.value == default_hour:
					option.default = True
					break
		super().__init__(placeholder="時を選択...", options=options)

	async def callback(self, interaction: discord.Interaction):
		selected_hour = self.values[0]
		self.view.values["time_hour"] = selected_hour
		for option in self.options:
			option.default = option.value == selected_hour
		await self.view.update_message(interaction)

class MinuteSelect(discord.ui.Select):
	def __init__(self, default_minute: str = None):
		options = [discord.SelectOption(label=f"{m:02}分", value=f"{m:02}") for m in range(0, 60, 5)]
		# 編集モード用にデフォルト値を設定
		if default_minute and default_minute != "未設定":
			for option in options:
				if option.value == default_minute:
					option.default = True
					break
		super().__init__(placeholder="分を選択...", options=options)
	
	async def callback(self, interaction: discord.Interaction):
		selected_minute = self.values[0]
		self.view.values["time_minute"] = selected_minute
		for option in self.options:
			option.default = option.value == selected_minute
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
		self.view.add_main_buttons()
		await self.view.update_message(interaction)

class RecruitFormView(discord.ui.View):
	def __init__(self, controller: 'GDBotController', initial_data: dict = None, recruit_id: int = None):
		super().__init__(timeout=600)
		self.controller = controller
		self.current_screen = "main"
		self.recruit_id = recruit_id
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
			self.values["place"] = initial_data.get("place", "未設定")
			self.values["capacity"] = str(initial_data.get("max_people", "未設定"))
			
			if initial_data.get("date_s"):
				try:
					dt_obj = datetime.strptime(initial_data["date_s"], "%Y/%m/%d %H:%M")
					self.values["date"] = dt_obj.strftime("%Y/%m/%d")
					self.values["time_hour"] = dt_obj.strftime("%H")
					self.values["time_minute"] = dt_obj.strftime("%M")
				except ValueError:
					pass # パース失敗時は未設定のまま

			# 修正: 既存のnoteカラムから、新しい個別のカラムにデータをマッピング
			note = initial_data.get("note", "")
			if note:
				note_parts = note.split(' / ')
				for part in note_parts:
					if part == "メンター希望":
						self.values["mentor_needed"] = True
					elif part.startswith("想定業界: "):
						self.values["industry"] = part.replace("想定業界: ", "", 1)
					else:
						self.values["note_message"] = part
			
			self.values["note_message"] = initial_data.get("message", "未設定")
			self.values["mentor_needed"] = initial_data.get("mentor_needed", 0) == 1
			self.values["industry"] = initial_data.get("industry", "未設定")
		
		self.add_main_buttons()

	def add_main_buttons(self):
		self.clear_items()
		self.current_screen = "main"
		self.add_item(discord.ui.Button(label="📅 日付設定", style=discord.ButtonStyle.secondary, custom_id="set_date", row=0))
		self.add_item(discord.ui.Button(label="📍 場所設定", style=discord.ButtonStyle.secondary, custom_id="set_place", row=0))
		self.add_item(discord.ui.Button(label="👥 定員設定", style=discord.ButtonStyle.secondary, custom_id="set_capacity", row=0))
		self.add_item(discord.ui.Button(label="📝 備考設定", style=discord.ButtonStyle.secondary, custom_id="set_note", row=0))
		
		if self.recruit_id:
			self.add_item(discord.ui.Button(label="✅ 募集を更新", style=discord.ButtonStyle.success, custom_id="update_recruit", row=1))
		else:
			self.add_item(discord.ui.Button(label="✅ 募集を作成", style=discord.ButtonStyle.success, custom_id="create_recruit", row=1, disabled=True))

	def add_note_buttons(self):
		self.clear_items()
		self.current_screen = "note"
		self.add_item(discord.ui.Button(label="↩️ フォームに戻る", style=discord.ButtonStyle.grey, custom_id="back_to_main_form"))
		self.add_item(discord.ui.Button(label="✉️ メッセージ", style=discord.ButtonStyle.secondary, custom_id="set_note_message"))
		
		mentor_label = "メンター: OFF" if not self.values["mentor_needed"] else "メンター: ON"
		mentor_style = discord.ButtonStyle.danger if not self.values["mentor_needed"] else discord.ButtonStyle.success
		self.add_item(discord.ui.Button(label=mentor_label, style=mentor_style, custom_id="toggle_mentor"))
		
		self.add_item(IndustrySelect(default_industry=self.values["industry"]))

	def create_embed(self):
		embed = discord.Embed(title="募集作成フォーム")
		
		if self.current_screen == "note":
			embed.description = "備考の各項目を設定してください。"
			embed.add_field(name="✉️ メッセージ", value=self.values['note_message'], inline=False)
			embed.add_field(name="🤝 メンター有無", value="呼ぶ" if self.values['mentor_needed'] else "呼ばない", inline=False)
			embed.add_field(name="🏢 想定業界", value=self.values['industry'], inline=False)
		else:
			embed.description = "下のボタンを押して各項目を入力してください。"
			datetime_val = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
			if "未設定" in datetime_val:
				datetime_val = "未設定"
			
			mentor_status = "呼ぶ" if self.values['mentor_needed'] else "呼ばない"

			place_val = self.values['place'] if self.values['place'] is not None else "未設定"
			capacity_val = self.values['capacity'] if self.values['capacity'] is not None else "未設定"
			message_val = self.values['note_message'] if self.values['note_message'] is not None else "未設定"
			industry_val = self.values['industry'] if self.values['industry'] is not None else "未設定"

			embed.add_field(name="📅 日時", value=datetime_val, inline=False)
			embed.add_field(name="📍 場所", value=place_val, inline=False)
			embed.add_field(name="👥 定員", value=capacity_val, inline=False)
			embed.add_field(name="✉️ メッセージ", value=message_val, inline=False)
			embed.add_field(name="🤝 メンター有無", value=mentor_status, inline=False)
			embed.add_field(name="🏢 想定業界", value=industry_val, inline=False)
		return embed

	async def update_message(self, interaction: discord.Interaction):
		if self.current_screen == "time":
			time_filled = all(self.values[key] != "未設定" for key in ["time_hour", "time_minute"])
			for item in self.children:
				if isinstance(item, discord.ui.Button) and item.custom_id == "confirm_time":
					item.disabled = not time_filled
					break
		elif self.current_screen == "main":
			required_filled = all(self.values[key] != "未設定" for key in ["date", "time_hour", "time_minute", "place", "capacity"])
			# 新規作成の場合のみボタンを無効化
			if not self.recruit_id:
				for item in self.children:
					if isinstance(item, discord.ui.Button) and item.custom_id == "create_recruit":
						item.disabled = not required_filled
						break
		
		embed = self.create_embed()
		if interaction.response.is_done():
			await interaction.followup.edit_message(embed=embed, view=self, message_id=interaction.message.id)
		else:
			await interaction.response.edit_message(embed=embed, view=self)

	async def add_time_selectors(self, interaction: discord.Interaction):
		self.current_screen = "time"
		self.clear_items()
		self.add_item(HourSelect(default_hour=self.values["time_hour"]))
		self.add_item(MinuteSelect(default_minute=self.values["time_minute"]))
		self.add_item(discord.ui.Button(label="↩️ 日付を再入力", style=discord.ButtonStyle.grey, custom_id="reset_date"))
		self.add_item(discord.ui.Button(label="✅ 時間を登録", style=discord.ButtonStyle.success, custom_id="confirm_time", disabled=True))
		await self.update_message(interaction)
	
	async def interaction_check(self, interaction: discord.Interaction):
		custom_id = interaction.data.get("custom_id")

		if custom_id == "set_date":
			modal = DateInputModal(parent_view=self)
			await interaction.response.send_modal(modal)
		elif custom_id == "set_place":
			modal = TextInputModal(title="場所の入力", label="開催場所 (Zoomなど)", style=discord.TextStyle.short, parent_view=self, key="place", default=self.values["place"])
			await interaction.response.send_modal(modal)
		elif custom_id == "set_capacity":
			self.current_screen = "capacity"
			self.clear_items()
			self.add_item(CapacitySelect(default_capacity=self.values["capacity"]))
			self.add_item(discord.ui.Button(label="↩️ フォームに戻る", style=discord.ButtonStyle.grey, custom_id="back_to_main_form"))
			await interaction.response.edit_message(view=self)
		elif custom_id == "set_note":
			self.add_note_buttons()
			await self.update_message(interaction)
		elif custom_id == "create_recruit" or custom_id == "update_recruit":
			try:
				date_s = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
				datetime.strptime(date_s, "%Y/%m/%d %H:%M")
				cap_int = int(self.values['capacity'])
				if cap_int <= 0: raise ValueError
				
				# 修正: 新しいカラムに対応したデータペイロードを構築
				data_payload = {
					'date_s': date_s,
					'place': self.values['place'],
					'max_people': cap_int,
					'message': self.values['note_message'] if self.values['note_message'] != "未設定" else None,
					'mentor_needed': self.values['mentor_needed'],
					'industry': self.values['industry'] if self.values['industry'] != "未設定" else None
				}
			except (ValueError, TypeError):
				await interaction.response.send_message("日時または定員の形式が正しくありません。入力し直してください。", ephemeral=True)
				return True

			if self.recruit_id:
				await interaction.response.edit_message(content="募集を更新しています...", embed=None, view=None)
				message_to_delete = await interaction.original_response()
				await self.controller.handle_recruit_update(interaction, self.recruit_id, data_payload, message_to_delete)
			else:
				await interaction.response.edit_message(content="募集を作成しています...", embed=None, view=None)
				message_to_delete = await interaction.original_response()
				await self.controller.handle_recruit_submission(interaction, data_payload, message_to_delete)
			
			self.stop()
		elif custom_id == "reset_date":
			modal = DateInputModal(parent_view=self)
			await interaction.response.send_modal(modal)
		elif custom_id == "confirm_time" or custom_id == "back_to_main_form":
			self.add_main_buttons()
			await self.update_message(interaction)
		elif custom_id == "set_note_message":
			modal = TextInputModal(title="備考メッセージ入力", label="メッセージ", style=discord.TextStyle.paragraph, parent_view=self, key="note_message", default=self.values["note_message"])
			await interaction.response.send_modal(modal)
		elif custom_id == "toggle_mentor":
			self.values["mentor_needed"] = not self.values["mentor_needed"]
			self.add_note_buttons()
			await self.update_message(interaction)

		return True