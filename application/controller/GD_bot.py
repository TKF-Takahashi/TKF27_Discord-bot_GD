# application/controller/GD_bot.py
import discord
import asyncio
from discord.ext import commands
from typing import Union # この行を追加
from datetime import datetime

# 変更: モデルとビューのインポートパス
from application.model.recruit import RecruitModel, Recruit
from application.view.recruit import HeaderView, JoinLeaveButtons
from application.view.modal import RecruitModal
from application.library.helper import remove_thread_system_msg

# GD 練習チャンネルのトピックテキスト
TOPIC_TEXT = ("📌 **GD 練習チャンネル案内**\n"
			  "・新規募集はボタンから作成してください。\n"
			  "・各募集のボタンで参加/取り消しができます。")

class GDBotController:
	"""
	Discordボットのイベント処理とロジックの制御を行うクラス。
	ModelとViewを連携させる。
	"""
	def __init__(self, bot: commands.Bot, channel_id: int):
		self.bot = bot
		self.channel_id = channel_id
		self.recruit_model = RecruitModel() # モデルのインスタンス化
		self.header_msg_id: Union[int, None] = None # 変更: ヘッダーメッセージIDの管理

		# Botイベントのリスナーを登録
		self.bot.event(self.on_ready)
		self.bot.event(self.on_interaction)

	async def _ensure_header(self, ch: Union[discord.TextChannel, discord.Thread]): # 変更
		"""ヘッダーメッセージの有無を確認し、必要に応じて更新/削除する"""
		current_recruits = await self.recruit_model.get_all_recruits()

		if current_recruits and self.header_msg_id:
			try:
				# 募集がある場合はヘッダーメッセージを削除
				header_msg = await ch.fetch_message(self.header_msg_id)
				await header_msg.delete()
				self.header_msg_id = None
			except discord.NotFound:
				self.header_msg_id = None # メッセージが見つからない場合はIDをリセット
				print("⚠ ヘッダーメッセージが見つかりませんでしたが、IDをリセットしました。")
			except discord.Forbidden:
				print("⚠ ヘッダーメッセージ削除権限がありません。")
			except Exception as e:
				print(f"ヘッダーメッセージ削除中に予期せぬエラー: {e}")
		elif not current_recruits and self.header_msg_id is None:
			# 募集がなく、ヘッダーメッセージもない場合は新規作成
			try:
				msg = await ch.send("📢 ボタンはこちら", view=HeaderView())
				self.header_msg_id = msg.id
			except discord.Forbidden:
				print("⚠ ヘッダーメッセージ送信権限がありません。")
			except Exception as e:
				print(f"ヘッダーメッセージ送信中に予期せぬエラー: {e}")


	async def _send_or_update_recruit_message(self, ch: Union[discord.TextChannel, discord.Thread], recruit_data: dict): # 変更
		"""
		募集メッセージを送信または更新する。
		recruit_dataはRecruitModelから取得した辞書形式のデータ。
		"""
		# RecruitModelから取得した辞書データをRecruitオブジェクトに変換
		# 参加者IDリストはMemberオブジェクトに変換する必要がある
		participants_members: list[discord.Member] = []
		guild = ch.guild
		for user_id in recruit_data['participants']:
			try:
				member = await guild.fetch_member(user_id)
				participants_members.append(member)
			except discord.NotFound:
				print(f"警告: 参加者ID {user_id} のメンバーが見つかりません。")
			except Exception as e:
				print(f"メンバー取得中に予期せぬエラー ({user_id}): {e}")

		rc = Recruit(
			rid=recruit_data['id'],
			date_s=recruit_data['date_s'],
			place=recruit_data['place'],
			cap=recruit_data['max_people'],
			note=recruit_data['note'],
			thread_id=recruit_data['thread_id'],
			msg_id=recruit_data['msg_id'],
			participants=participants_members
		)

		content = rc.block() # Recruitクラスのblock()メソッドで表示テキストを生成
		view = JoinLeaveButtons(rc.id)

		# スレッドへボタン
		view.add_item(
			discord.ui.Button(
				label="スレッドへ",
				style=discord.ButtonStyle.link,
				url=f"https://discord.com/channels/{ch.guild.id}/{rc.thread_id}"
			)
		)
		# 新たな募集を追加ボタン（スレッドへボタンの右側）
		view.add_item(
			discord.ui.Button(
				label="新たな募集を追加",
				style=discord.ButtonStyle.primary,
				custom_id="make"
			)
		)
		view.add_item(
			discord.ui.Button(
				label="test",
				style=discord.ButtonStyle.primary,
				custom_id="event"
			)
		)

		if rc.msg_id:
			try:
				message = await ch.fetch_message(rc.msg_id)
				await message.edit(content=content, view=view)
				return
			except discord.NotFound:
				# メッセージが見つからない場合は新規送信
				print(f"募集メッセージID {rc.msg_id} が見つかりません。新規送信します。")
			except discord.Forbidden:
				print(f"⚠ メッセージ編集権限がありません。メッセージID: {rc.msg_id}")
			except Exception as e:
				print(f"メッセージ編集中に予期せぬエラー ({rc.msg_id}): {e}")

		# 新規送信
		try:
			msg = await ch.send(content, view=view)
			# DBにメッセージIDを保存
			await self.recruit_model.update_recruit_message_id(rc.id, msg.id)
			rc.msg_id = msg.id # Recruitオブジェクトにも設定
			await asyncio.sleep(0.5) # Discord APIのレートリミット対策
		except discord.Forbidden:
			print("⚠ メッセージ送信権限がありません。")
		except Exception as e:
			print(f"メッセージ送信中に予期せぬエラー: {e}")


	# ───────────────── BOT イベント ─────────────────
	async def on_ready(self):
		"""ボットが起動した際に実行される処理"""
		await self.bot.tree.sync() # スラッシュコマンドの同期
		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			print(f"エラー: CHANNEL_ID {self.channel_id} はテキストチャンネルまたはスレッドではありません。")
			return

		try:
			await ch.edit(topic=TOPIC_TEXT) # チャンネルトピックの更新
		except discord.Forbidden:
			print("⚠ チャンネルトピック設定権限がありません。")
		except Exception as e:
			print(f"チャンネルトピック設定中に予期せぬエラー: {e}")


		# 既存の募集メッセージをすべて更新（起動時にDBからロードして表示を同期）
		all_recruits = await self.recruit_model.get_all_recruits()
		for recruit_data in all_recruits:
			await self._send_or_update_recruit_message(ch, recruit_data)

		await self._ensure_header(ch) # ヘッダーメッセージの管理
		print("✅ ready")

	async def on_interaction(self, it: discord.Interaction):
		"""インタラクション（ボタンクリック、モーダル送信など）を処理"""
		if it.type.name != "component":
			return # コンポーネントインタラクション以外は無視

		custom_id = it.data.get("custom_id")

		# 「募集を作成」ボタンがクリックされた場合
		if custom_id == "make":
			# 変更: モーダルビューのインポートパスと、コントローラー自身を渡す
			await it.response.send_modal(RecruitModal(self)) # モーダルを表示
			return
		
		# 「イベント作成フォームテスト用」
		if custom_id == "event":
			# 以下のコードは、ボタンが押された際のInteraction内で実行されることを想定しています。
			# 'interaction'変数は、このコンテキストで利用可能である必要があります。
			try:
				await interaction.response.send_modal(EventCreationModal())
				return
			except NameError:
				# EventCreationModalクラスが定義されていない場合のフォールバック
				return
		
		# 「最新状況を反映」ボタンはView内で完結するため、ここでは処理しない
		if custom_id == "refresh":
			return

		# 「参加予定に追加」「参加予定を削除」ボタンがクリックされた場合
		if ":" not in custom_id:
			return # フォーマットが異なるカスタムIDは無視

		action, recruit_id_str = custom_id.split(":", 1)
		if not recruit_id_str.isdigit():
			return # IDが数値でない場合は無視

		recruit_id = int(recruit_id_str)

		# 募集の存在確認
		recruit_data = await self.recruit_model.get_recruit_by_id(recruit_id)
		if not recruit_data:
			await it.response.send_message("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return

		# 処理中の表示
		if not it.response.is_done():
			try:
				await it.response.defer(thinking=False, ephemeral=True)
			except discord.HTTPException:
				pass # 既に応答済みの場合など
			except Exception as e:
				print(f"インタラクション defer 中に予期せぬエラー: {e}")

		user_id = it.user.id
		participants = recruit_data.get('participants', []) # DBからはリストとして取得される

		response_message = ""

		if action == "join":
			# 参加済みでない & 満員でない
			if user_id not in participants and len(participants) < recruit_data['max_people']:
				participants.append(user_id)
				response_message = "参加予定に追加しました。"
			elif user_id in participants:
				response_message = "あなたは既にこの募集に参加しています。"
			elif len(participants) >= recruit_data['max_people']:
				response_message = "この募集は満員です。"
		elif action == "leave":
			if user_id in participants:
				participants.remove(user_id)
				response_message = "参加予定から削除しました。"
			else:
				response_message = "あなたはまだこの募集に参加していません。"
		
		# 参加者リストが変更された場合のみDBを更新
		if response_message in ["参加予定に追加しました。", "参加予定から削除しました。"]:
			await self.recruit_model.update_recruit_participants(recruit_id, participants)
		
		await it.followup.send(response_message, ephemeral=True)

		# 参加者リストが更新されたので、メッセージを再更新
		updated_recruit_data = await self.recruit_model.get_recruit_by_id(recruit_id)
		channel = self.bot.get_channel(self.channel_id)
		if isinstance(channel, (discord.TextChannel, discord.Thread)):
			await self._send_or_update_recruit_message(channel, updated_recruit_data)
		
		# ヘッダーメッセージも更新
		await self._ensure_header(channel)


	async def handle_recruit_submission(self, interaction: discord.Interaction, data: dict):
		"""
		RecruitModalから募集データが送信された際の処理
		モーダルからのコールバックなので、GDBotControllerが持つメソッドとして定義
		"""
		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			await interaction.followup.send("エラー: チャンネルが見つからないか、不適切なタイプです。", ephemeral=True)
			return

		# スレッドの作成
		thread_name = f"🗨 {data['date_s']} GD練習について"
		try:
			th = await ch.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
			await remove_thread_system_msg(ch) # システムメッセージ削除
		except discord.Forbidden:
			await interaction.followup.send("エラー: スレッド作成権限がありません。", ephemeral=True)
			return
		except Exception as e:
			await interaction.followup.send(f"エラー: スレッド作成中に問題が発生しました: {e}", ephemeral=True)
			return

		# データベースに募集データを保存
		new_recruit_id = await self.recruit_model.add_recruit(
			date_s=data['date_s'],
			place=data['place'],
			max_people=data['max_people'],
			note=data['note'],
			thread_id=th.id
		)

		if new_recruit_id is None:
			await interaction.followup.send("エラー: 募集の保存に失敗しました。", ephemeral=True)
			return

		# 保存した募集データを取得してメッセージを送信
		new_recruit_data = await self.recruit_model.get_recruit_by_id(new_recruit_id)
		if new_recruit_data:
			await self._send_or_update_recruit_message(ch, new_recruit_data)
		else:
			await interaction.followup.send("エラー: 保存された募集データの取得に失敗しました。", ephemeral=True)
			
		await self._ensure_header(ch) # ヘッダーメッセージも更新
		await interaction.followup.send("募集が作成されました！", ephemeral=True)






# Discord botのセットアップ
# intents = discord.Intents.default()
# intents.message_content = True
# intents.scheduled_events = True
# bot = commands.Bot(command_prefix="!", intents=intents)

# Discord APIの仕様変更により、必要なインテントは適宜追加してください。
# また、イベント作成にはGUILD_SCHEDULED_EVENTS_CREATEの権限が必要です。

class EventCreationModal(discord.ui.Modal, title="イベント作成フォーム"):
	event_name = discord.ui.TextInput(
		label="イベント名",
		placeholder="GD募集",
		default="GD募集",  # 初期値を設定
		required=True,
	)

	event_date = discord.ui.TextInput(
		label="開催日 (例: 7/10)",
		placeholder="7/10",
		required=True,
	)

	event_desc = discord.ui.TextInput(
		label="イベントの説明",
		placeholder="詳細な説明を入力してください",
		required=False,
		style=discord.TextStyle.long,
	)

	event_location = discord.ui.TextInput(
		label="イベントの場所（ボイスch名やURL）",
		placeholder="vc名",
		required=True,
	)

	async def on_submit(self, interaction: discord.Interaction):
		# イベント名の動的な変更
		final_event_name = f"{self.event_date.value}:{self.event_name.value}"

		# イベントの場所を特定
		# ボイスチャンネル名でチャンネルを取得する例
		location_channel = discord.utils.get(
			interaction.guild.voice_channels,
			name=self.event_location.value
		)
		if location_channel is None:
			await interaction.response.send_message(
				"指定されたボイスチャンネルが見つかりませんでした。",
				ephemeral=True
			)
			return

		# ここでイベント作成APIを呼び出す
		# Discord APIでは、ISO 8601形式のタイムスタンプが必要です。
		# ユーザー入力からdatetimeオブジェクトを生成する必要がありますが、
		# 厳密な日付フォーマットを求めるか、より柔軟な入力を受け付けるかによって実装は変わります。
		# 以下はあくまで例です。
		try:
			# ユーザー入力から日付を解析
			current_year = datetime.now().year
			# 例として、7/10を2025/7/10として解析
			event_start_time = datetime.strptime(
				f"{current_year}/{self.event_date.value}", "%Y/%m/%d"
			)

			# イベントの作成
			await interaction.guild.create_scheduled_event(
				name=final_event_name,
				scheduled_start_time=event_start_time,
				description=self.event_desc.value,
				channel=location_channel,
				entity_type=discord.EntityType.voice
			)

			await interaction.response.send_message(
				f"イベント「**{final_event_name}**」が作成されました！"
			)

		except ValueError:
			await interaction.response.send_message(
				"日付の形式が正しくありません。例: 7/10",
				ephemeral=True
			)
			return


class EventButtonView(discord.ui.View):
	@discord.ui.button(
		label="イベント作成",
		style=discord.ButtonStyle.primary,
		custom_id="create_event_button",
	)
	async def create_event_button(
		self, interaction: discord.Interaction, button: discord.ui.Button
	):
		await interaction.response.send_modal(EventCreationModal())


@bot.command()
async def create_event_command(ctx):
	await ctx.send("ボタンを押してイベントを作成してください", view=EventButtonView())