import discord
from .modal import TextInputModal
# [変更] 正しいクラス名 'DateSelectView' をインポート
from .calendar import DateSelectView

if False:
	from application.controller.GD_bot import GDBotController

class RecruitFormView(discord.ui.View):
	def __init__(self, controller: 'GDBotController'):
		super().__init__(timeout=600)
		self.controller = controller
		self.values = {
			"date": "未設定",
			"time": "未設定",
			"place": "未設定",
			"capacity": "未設定",
			"note": "未設定"
		}
	
	def create_embed(self):
		embed = discord.Embed(title="募集作成フォーム", description="下のボタンを押して各項目を入力してください。")
		
		# 日時が両方設定されるまで「未設定」と表示する
		datetime_val = f"{self.values['date']} {self.values['time']}"
		if "未設定" in datetime_val:
			datetime_val = "未設定"
		
		embed.add_field(name="📅 日時", value=datetime_val, inline=False)
		embed.add_field(name="📍 場所", value=self.values['place'], inline=False)
		embed.add_field(name="👥 定員", value=self.values['capacity'], inline=False)
		embed.add_field(name="📝 備考", value=self.values['note'], inline=False)
		return embed

	async def update_message(self, interaction: discord.Interaction):
		# 必須項目が埋まっているかチェック
		required_filled = all(self.values[key] != "未設定" for key in ["date", "time", "place", "capacity"])
		
		# 「作成」ボタンを探して有効/無効を切り替える
		for item in self.children:
			if isinstance(item, discord.ui.Button) and item.custom_id == "create_recruit":
				item.disabled = not required_filled
				break
		
		embed = self.create_embed()
		# モーダルからの応答の場合は is_done() が True になる
		if interaction.response.is_done():
			# is_done() の場合、元のインタラクションは応答済みなので followup でメッセージを編集
			await interaction.followup.edit_message(embed=embed, view=self, message_id=interaction.message.id)
		else:
			# is_done() でない場合（ボタンクリックなど）、元のインタラクションに直接応答
			await interaction.response.edit_message(embed=embed, view=self)

	@discord.ui.button(label="📅 日時設定", style=discord.ButtonStyle.secondary, row=0)
	async def set_datetime(self, interaction: discord.Interaction, button: discord.ui.Button):
		# [変更] 正しいクラス名 'DateSelectView' を使用
		date_view = DateSelectView(form_view=self)
		await interaction.response.edit_message(content="下のドロップダウンから日時を選択してください:", embed=None, view=date_view)

	@discord.ui.button(label="📍 場所設定", style=discord.ButtonStyle.secondary, row=1)
	async def set_place(self, interaction: discord.Interaction, button: discord.ui.Button):
		modal = TextInputModal(
			title="場所の入力",
			label="開催場所 (Zoomなど)",
			style=discord.TextStyle.short,
			parent_view=self,
			key="place",
			default=self.values["place"]
		)
		await interaction.response.send_modal(modal)

	@discord.ui.button(label="👥 定員設定", style=discord.ButtonStyle.secondary, row=1)
	async def set_capacity(self, interaction: discord.Interaction, button: discord.ui.Button):
		modal = TextInputModal(
			title="定員の入力",
			label="募集人数 (半角数字)",
			style=discord.TextStyle.short,
			parent_view=self,
			key="capacity",
			default=self.values["capacity"]
		)
		await interaction.response.send_modal(modal)

	@discord.ui.button(label="📝 備考設定", style=discord.ButtonStyle.secondary, row=1)
	async def set_note(self, interaction: discord.Interaction, button: discord.ui.Button):
		modal = TextInputModal(
			title="備考の入力",
			label="備考 (任意)",
			style=discord.TextStyle.paragraph,
			parent_view=self,
			key="note",
			default=self.values["note"]
		)
		await interaction.response.send_modal(modal)

	@discord.ui.button(label="✅ 募集を作成", style=discord.ButtonStyle.success, row=2, disabled=True, custom_id="create_recruit")
	async def create_recruit(self, interaction: discord.Interaction, button: discord.ui.Button):
		# 最終的な値のバリデーション
		try:
			date_s = f"{self.values['date']} {self.values['time']}"
			datetime.strptime(date_s, "%Y/%m/%d %H:%M")
			cap_int = int(self.values['capacity'])
			if cap_int <= 0: raise ValueError
		except (ValueError, TypeError):
			await interaction.response.send_message("日時または定員の形式が正しくありません。入力し直してください。", ephemeral=True)
			return

		# 元のメッセージを編集して、処理中であることを伝える
		await interaction.response.edit_message(content="募集を作成しています...", embed=None, view=None)
		
		# コントローラーのメソッドに処理を委譲
		# handle_recruit_submission は followup.send を使うので interaction をそのまま渡す
		await self.controller.handle_recruit_submission(interaction, {
			'date_s': date_s,
			'place': self.values['place'],
			'max_people': cap_int,
			'note': self.values['note'] if self.values['note'] != "未設定" else ""
		})
		self.stop()