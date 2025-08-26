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

# [新規追加] 定員を選択するセレクトメニュー
class CapacitySelect(discord.ui.Select):
	def __init__(self):
		options = [discord.SelectOption(label=f"{i}人", value=str(i)) for i in range(3, 11)]
		super().__init__(placeholder="定員を選択...", options=options)
	
	async def callback(self, interaction: discord.Interaction):
		selected_capacity = self.values[0]
		self.view.values["capacity"] = selected_capacity

		for option in self.options:
			option.default = option.value == selected_capacity
		
		# [変更] 親Viewのupdate_messageではなく、メインフォームに戻る処理を直接呼び出す
		self.view.is_selecting_capacity = False
		self.view.add_main_buttons()
		await self.view.update_message(interaction)


class RecruitFormView(discord.ui.View):
	def __init__(self, controller: 'GDBotController'):
		super().__init__(timeout=600)
		self.controller = controller
		self.is_selecting_time = False
		self.is_selecting_capacity = False # 定員選択中かどうかのフラグを追加
		self.values = {
			"date": "未設定",
			"time_hour": "未設定",
			"time_minute": "未設定",
			"place": "未設定",
			"capacity": "未設定",
			"note": "未設定"
		}
		self.add_main_buttons()

	def add_main_buttons(self):
		self.clear_items()
		self.add_item(discord.ui.Button(label="📅 日付設定", style=discord.ButtonStyle.secondary, custom_id="set_date", row=0))
		self.add_item(discord.ui.Button(label="📍 場所設定", style=discord.ButtonStyle.secondary, custom_id="set_place", row=0))
		self.add_item(discord.ui.Button(label="👥 定員設定", style=discord.ButtonStyle.secondary, custom_id="set_capacity", row=0))
		self.add_item(discord.ui.Button(label="📝 備考設定", style=discord.ButtonStyle.secondary, custom_id="set_note", row=0))
		self.add_item(discord.ui.Button(label="✅ 募集を作成", style=discord.ButtonStyle.success, custom_id="create_recruit", row=1, disabled=True))

	def create_embed(self):
		embed = discord.Embed(title="募集作成フォーム", description="下のボタンを押して各項目を入力してください。")
		datetime_val = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
		if "未設定" in datetime_val:
			datetime_val = "未設定"
		embed.add_field(name="📅 日時", value=datetime_val, inline=False)
		embed.add_field(name="📍 場所", value=self.values['place'], inline=False)
		embed.add_field(name="👥 定員", value=self.values['capacity'], inline=False)
		embed.add_field(name="📝 備考", value=self.values['note'], inline=False)
		return embed

	async def update_message(self, interaction: discord.Interaction):
		if self.is_selecting_time:
			time_filled = all(self.values[key] != "未設定" for key in ["time_hour", "time_minute"])
			for item in self.children:
				if isinstance(item, discord.ui.Button) and item.custom_id == "confirm_time":
					item.disabled = not time_filled
					break
		# [追加] 定員選択画面用のボタン状態更新ロジックは不要 (選択と同時に画面が戻るため)
		elif not self.is_selecting_capacity: # 定員選択中でない場合のみメインフォームのボタンを更新
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
		self.is_selecting_time = True
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
		# [変更] 定員設定ボタンの処理をモーダルからプルダウン表示に変更
		elif custom_id == "set_capacity":
			self.is_selecting_capacity = True
			self.clear_items()
			self.add_item(CapacitySelect())
			self.add_item(discord.ui.Button(label="↩️ フォームに戻る", style=discord.ButtonStyle.grey, custom_id="back_to_main_form"))
			await interaction.response.edit_message(view=self)
		elif custom_id == "set_note":
			modal = TextInputModal(title="備考の入力", label="備考 (任意)", style=discord.TextStyle.paragraph, parent_view=self, key="note", default=self.values["note"])
			await interaction.response.send_modal(modal)
		elif custom_id == "create_recruit":
			try:
				date_s = f"{self.values['date']} {self.values['time_hour']}:{self.values['time_minute']}"
				datetime.strptime(date_s, "%Y/%m/%d %H:%M")
				cap_int = int(self.values['capacity'])
				if cap_int <= 0: raise ValueError
			except (ValueError, TypeError):
				await interaction.response.send_message("日時または定員の形式が正しくありません。入力し直してください。", ephemeral=True)
				return True

			await interaction.response.edit_message(content="募集を作成しています...", embed=None, view=None)
			await self.controller.handle_recruit_submission(interaction, {
				'date_s': date_s,
				'place': self.values['place'],
				'max_people': cap_int,
				'note': self.values['note'] if self.values['note'] != "未設定" else ""
			})
			self.stop()
		elif custom_id == "reset_date":
			modal = DateInputModal(parent_view=self)
			await interaction.response.send_modal(modal)
		# [変更] 「時間を登録」と、定員選択画面の「フォームに戻る」ボタンの処理をまとめる
		elif custom_id == "confirm_time" or custom_id == "back_to_main_form":
			self.is_selecting_time = False
			self.is_selecting_capacity = False
			self.add_main_buttons()
			await self.update_message(interaction)

		return True