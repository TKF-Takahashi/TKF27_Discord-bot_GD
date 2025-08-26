import discord
from datetime import datetime
from .modal import TextInputModal, DateInputModal

if False:
	from application.controller.GD_bot import GDBotController

class HourSelect(discord.ui.Select):
	def __init__(self):
		hours = [f"{h:02}" for h in range(8, 24)] + [f"{h:02}" for h in range(0, 8)]
		options = [discord.SelectOption(label=f"{h}時", value=h) for h in hours]
		super().__init__(placeholder="時を選択...", options=options)

	async def callback(self, interaction: discord.Interaction):
		selected_hour = self.values[0]
		self.view.values["time_hour"] = selected_hour

		for option in self.options:
			option.default = option.value == selected_hour
		
		await self.view.update_message(interaction)

class MinuteSelect(discord.ui.Select):
	def __init__(self):
		options = [discord.SelectOption(label=f"{m:02}分", value=f"{m:02}") for m in range(0, 60, 5)]
		super().__init__(placeholder="分を選択...", options=options)
	
	async def callback(self, interaction: discord.Interaction):
		selected_minute = self.values[0]
		self.view.values["time_minute"] = selected_minute

		for option in self.options:
			option.default = option.value == selected_minute

		await self.view.update_message(interaction)

# [新規追加] 想定業界を選択するセレクトメニュー
class IndustrySelect(discord.ui.Select):
	def __init__(self):
		options = [
			discord.SelectOption(label="IT/通信", value="IT/通信"),
			discord.SelectOption(label="コンサル", value="コンサル")
		]
		super().__init__(placeholder="想定業界を選択...", options=options)
	
	async def callback(self, interaction: discord.Interaction):
		self.view.values["industry"] = self.values[0]
		await self.view.update_message(interaction)


class RecruitFormView(discord.ui.View):
	def __init__(self, controller: 'GDBotController'):
		super().__init__(timeout=600)
		self.controller = controller
		self.current_screen = "main" # 現在の画面を管理するフラグ
		self.values = {
			"date": "未設定",
			"time_hour": "未設定",
			"time_minute": "未設定",
			"place": "未設定",
			"capacity": "未設定",
			"note_message": "未設定", # [変更] noteを分割
			"mentor_needed": False,      # [追加] メンター有無
			"industry": "未設定"         # [追加] 想定業界
		}
		self.add_main_buttons()

	def add_main_buttons(self):
		self.clear_items()
		self.current_screen = "main"
		self.add_item(discord.ui.Button(label="📅 日付設定", style=discord.ButtonStyle.secondary, custom_id="set_date", row=0))
		self.add_item(discord.ui.Button(label="📍 場所設定", style=discord.ButtonStyle.secondary, custom_id="set_place", row=0))
		self.add_item(discord.ui.Button(label="👥 定員設定", style=discord.ButtonStyle.secondary, custom_id="set_capacity", row=0))
		self.add_item(discord.ui.Button(label="📝 備考設定", style=discord.ButtonStyle.secondary, custom_id="set_note", row=0))
		self.add_item(discord.ui.Button(label="✅ 募集を作成", style=discord.ButtonStyle.success, custom_id="create_recruit", row=1, disabled=True))

	# [新規追加] 備考設定画面のボタンを追加するメソッド
	def add_note_buttons(self):
		self.clear_items()
		self.current_screen = "note"
		self.add_item(discord.ui.Button(label="↩️ フォームに戻る", style=discord.ButtonStyle.grey, custom_id="back_to_main_form"))
		self.add_item(discord.ui.Button(label="✉️ メッセージ", style=discord.ButtonStyle.secondary, custom_id="set_note_message"))
		
		mentor_label = "メンター: OFF" if not self.values["mentor_needed"] else "メンター: ON"
		mentor_style = discord.ButtonStyle.danger if not self.values["mentor_needed"] else discord.ButtonStyle.success
		self.add_item(discord.ui.Button(label=mentor_label, style=mentor_style, custom_id="toggle_mentor"))
		
		self.add_item(IndustrySelect())

	def create_embed(self):
		embed = discord.Embed(title="募集作成フォーム")
		
		if self.current_screen == "note":
			embed.description = "備考の各項目を設定してください。"
			embed.add_field(name="✉️ メッセージ", value=self.values['note_message'], inline=False)
			embed.add_field(name="🤝 メンター有無", value="呼ぶ" if self.values['mentor_needed'] else "呼ばない", inline=False)
			embed.add_field(name="🏢 想定業界", value=self.values['industry'], inline=False)
		else: # main screen
			embed.description = "下のボタンを押して各項目を入力してください。"
			datetime_val = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
			if "未設定" in datetime_val:
				datetime_val = "未設定"
			
			# [変更] noteの表示を結合
			note_parts = []
			if self.values['note_message'] != "未設定": note_parts.append(self.values['note_message'])
			if self.values['mentor_needed']: note_parts.append("メンター希望")
			if self.values['industry'] != "未設定": note_parts.append(f"想定業界: {self.values['industry']}")
			note_full = " / ".join(note_parts) if note_parts else "未設定"

			embed.add_field(name="📅 日時", value=datetime_val, inline=False)
			embed.add_field(name="📍 場所", value=self.values['place'], inline=False)
			embed.add_field(name="👥 定員", value=self.values['capacity'], inline=False)
			embed.add_field(name="📝 備考", value=note_full, inline=False)
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
		self.add_item(HourSelect())
		self.add_item(MinuteSelect())
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
			self.add_item(CapacitySelect())
			self.add_item(discord.ui.Button(label="↩️ フォームに戻る", style=discord.ButtonStyle.grey, custom_id="back_to_main_form"))
			await interaction.response.edit_message(view=self)
		# [変更] 備考設定ボタンの処理
		elif custom_id == "set_note":
			self.add_note_buttons()
			await self.update_message(interaction)
		elif custom_id == "create_recruit":
			try:
				date_s = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
				datetime.strptime(date_s, "%Y/%m/%d %H:%M")
				cap_int = int(self.values['capacity'])
				if cap_int <= 0: raise ValueError
				
				# [変更] noteの値を結合して渡す
				note_parts = []
				if self.values['note_message'] != "未設定": note_parts.append(self.values['note_message'])
				if self.values['mentor_needed']: note_parts.append("メンター希望")
				if self.values['industry'] != "未設定": note_parts.append(f"想定業界: {self.values['industry']}")
				note_full = " / ".join(note_parts)

			except (ValueError, TypeError):
				await interaction.response.send_message("日時または定員の形式が正しくありません。入力し直してください。", ephemeral=True)
				return True

			await interaction.response.edit_message(content="募集を作成しています...", embed=None, view=None)
			await self.controller.handle_recruit_submission(interaction, {
				'date_s': date_s,
				'place': self.values['place'],
				'max_people': cap_int,
				'note': note_full
			})
			self.stop()
		elif custom_id == "reset_date":
			modal = DateInputModal(parent_view=self)
			await interaction.response.send_modal(modal)
		elif custom_id == "confirm_time" or custom_id == "back_to_main_form":
			self.add_main_buttons()
			await self.update_message(interaction)
		# [新規追加] 備考設定画面のボタン処理
		elif custom_id == "set_note_message":
			modal = TextInputModal(title="備考メッセージ入力", label="メッセージ", style=discord.TextStyle.paragraph, parent_view=self, key="note_message", default=self.values["note_message"])
			await interaction.response.send_modal(modal)
		elif custom_id == "toggle_mentor":
			self.values["mentor_needed"] = not self.values["mentor_needed"]
			self.add_note_buttons() # ボタンのラベルを更新するために再描画
			await self.update_message(interaction)

		return True