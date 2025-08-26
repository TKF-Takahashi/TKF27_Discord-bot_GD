import discord
import asyncio
from discord.ext import commands
from typing import Union
from datetime import datetime
import pytz

# 変更: モデルとビューのインポートパス
from application.model.recruit import RecruitModel, Recruit
from application.view.recruit import HeaderView, JoinLeaveButtons
# [変更] 不要になったRecruitModalのインポートを削除
from application.view.form_view import RecruitFormView
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
		self.recruit_model = RecruitModel()
		self.header_msg_id: Union[int, None] = None

		# Botイベントのリスナーを登録
		self.bot.event(self.on_ready)
		self.bot.event(self.on_interaction)

	async def _ensure_header(self, ch: Union[discord.TextChannel, discord.Thread]):
		"""ヘッダーメッセージの有無を確認し、必要に応じて更新/削除する"""
		current_recruits = await self.recruit_model.get_all_recruits()

		if current_recruits and self.header_msg_id:
			try:
				header_msg = await ch.fetch_message(self.header_msg_id)
				await header_msg.delete()
				self.header_msg_id = None
			except discord.NotFound:
				self.header_msg_id = None
				print("⚠ ヘッダーメッセージが見つかりませんでしたが、IDをリセットしました。")
			except discord.Forbidden:
				print("⚠ ヘッダーメッセージ削除権限がありません。")
			except Exception as e:
				print(f"ヘッダーメッセージ削除中に予期せぬエラー: {e}")
		elif not current_recruits and self.header_msg_id is None:
			try:
				msg = await ch.send("📢 ボタンはこちら", view=HeaderView())
				self.header_msg_id = msg.id
			except discord.Forbidden:
				print("⚠ ヘッダーメッセージ送信権限がありません。")
			except Exception as e:
				print(f"ヘッダーメッセージ送信中に予期せぬエラー: {e}")


	async def _send_or_update_recruit_message(self, ch: Union[discord.TextChannel, discord.Thread], recruit_data: dict):
		"""
		募集メッセージを送信または更新する。
		"""
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

		content = rc.block()
		view = JoinLeaveButtons(rc.id)

		view.add_item(
			discord.ui.Button(
				label="スレッドへ",
				style=discord.ButtonStyle.link,
				url=f"https://discord.com/channels/{ch.guild.id}/{rc.thread_id}"
			)
		)
		# [削除] 「新たな募集を追加」ボタンの追加処理を削除
		view.add_item(
			discord.ui.Button(
				label="test",
				style=discord.ButtonStyle.primary,
				custom_id="test"
			)
		)

		if rc.msg_id:
			try:
				message = await ch.fetch_message(rc.msg_id)
				await message.edit(content=content, view=view)
				return
			except discord.NotFound:
				print(f"募集メッセージID {rc.msg_id} が見つかりません。新規送信します。")
			except discord.Forbidden:
				print(f"⚠ メッセージ編集権限がありません。メッセージID: {rc.msg_id}")
			except Exception as e:
				print(f"メッセージ編集中に予期せぬエラー ({rc.msg_id}): {e}")

		try:
			msg = await ch.send(content, view=view)
			await self.recruit_model.update_recruit_message_id(rc.id, msg.id)
			rc.msg_id = msg.id
			await asyncio.sleep(0.5)
		except discord.Forbidden:
			print("⚠ メッセージ送信権限がありません。")
		except Exception as e:
			print(f"メッセージ送信中に予期せぬエラー: {e}")


	# ───────────────── BOT イベント ─────────────────
	async def on_ready(self):
		"""ボットが起動した際に実行される処理"""
		await self.bot.tree.sync()
		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			print(f"エラー: CHANNEL_ID {self.channel_id} はテキストチャンネルまたはスレッドではありません。")
			return

		try:
			await ch.edit(topic=TOPIC_TEXT)
		except discord.Forbidden:
			print("⚠ チャンネルトピック設定権限がありません。")
		except Exception as e:
			print(f"チャンネルトピック設定中に予期せぬエラー: {e}")

		all_recruits = await self.recruit_model.get_all_recruits()
		for recruit_data in all_recruits:
			await self._send_or_update_recruit_message(ch, recruit_data)

		await self._ensure_header(ch)
		print("✅ ready")

	async def on_interaction(self, it: discord.Interaction):
		"""インタラクション（ボタンクリック、モーダル送信など）を処理"""
		if it.type.name != "component":
			return

		custom_id = it.data.get("custom_id")
		
		# [削除] custom_id == "make" の処理ブロックを削除
		if custom_id == "test":
			form_view = RecruitFormView(self)
			embed = form_view.create_embed()
			await it.response.send_message(embed=embed, view=form_view, ephemeral=True)
			return

		if ":" not in custom_id:
			return

		action, recruit_id_str = custom_id.split(":", 1)
		if not recruit_id_str.isdigit():
			return
		
		recruit_id = int(recruit_id_str)

		if not it.response.is_done():
			try:
				await it.response.defer(thinking=False, ephemeral=True)
			except discord.HTTPException:
				pass
			except Exception as e:
				print(f"インタラクション defer 中に予期せぬエラー: {e}")

		recruit_data = await self.recruit_model.get_recruit_by_id(recruit_id)
		if not recruit_data:
			await it.followup.send("エラー: その募集は存在しないか、削除されました。", ephemeral=True)
			return
			
		if action == "event":
			try:
				event_name = f"{recruit_data['date_s']} GD練習会"
				
				jst = pytz.timezone('Asia/Tokyo')
				start_time_naive = datetime.strptime(recruit_data['date_s'], '%Y/%m/%d %H:%M')
				start_time_aware = jst.localize(start_time_naive)

				location_str = recruit_data['place']
				entity_type = discord.ScheduledEventEntityType.external
				event_location = location_str
				event_channel = None

				vc = discord.utils.get(it.guild.voice_channels, name=location_str)
				if vc:
					entity_type = discord.ScheduledEventEntityType.voice
					event_channel = vc
					event_location = None

				await it.guild.create_scheduled_event(
					name=event_name,
					start_time=start_time_aware,
					entity_type=entity_type,
					channel=event_channel,
					location=event_location,
					description=recruit_data['note']
				)
				await it.followup.send(f"イベント「{event_name}」を作成しました。", ephemeral=True)

			except ValueError:
				await it.followup.send("エラー: 募集の日時フォーマットが不正です。`YYYY/MM/DD HH:MM` 形式である必要があります。", ephemeral=True)
			except Exception as e:
				await it.followup.send(f"イベント作成中にエラーが発生しました: {e}", ephemeral=True)
			return

		user_id = it.user.id
		participants = recruit_data.get('participants', [])

		response_message = ""

		if action == "join":
			if user_id not in participants and len(participants) < recruit_data['max_people']:
				participants.append(user_id)
				response_message = "参加予定に追加しました。"
			elif user_id in participants:
				response_message = "あなたは既にこの募集に参加しています。"
			else:
				response_message = "この募集は満員です。"
		elif action == "leave":
			if user_id in participants:
				participants.remove(user_id)
				response_message = "参加予定から削除しました。"
			else:
				response_message = "あなたはまだこの募集に参加していません。"
		
		if response_message in ["参加予定に追加しました。", "参加予定から削除しました。"]:
			await self.recruit_model.update_recruit_participants(recruit_id, participants)
		
		await it.followup.send(response_message, ephemeral=True)

		updated_recruit_data = await self.recruit_model.get_recruit_by_id(recruit_id)
		channel = self.bot.get_channel(self.channel_id)
		if isinstance(channel, (discord.TextChannel, discord.Thread)):
			await self._send_or_update_recruit_message(channel, updated_recruit_data)
		
		await self._ensure_header(channel)


	async def handle_recruit_submission(self, interaction: discord.Interaction, data: dict):
		"""
		RecruitModalから募集データが送信された際の処理
		"""
		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			# is_done() のチェックを追加
			if not interaction.response.is_done():
				await interaction.response.send_message("エラー: チャンネルが見つからないか、不適切なタイプです。", ephemeral=True)
			else:
				await interaction.followup.send("エラー: チャンネルが見つからないか、不適切なタイプです。", ephemeral=True)
			return

		thread_name = f"🗨 {data['date_s']} GD練習について"
		try:
			th = await ch.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
			await remove_thread_system_msg(ch)
		except discord.Forbidden:
			await interaction.followup.send("エラー: スレッド作成権限がありません。", ephemeral=True)
			return
		except Exception as e:
			await interaction.followup.send(f"エラー: スレッド作成中に問題が発生しました: {e}", ephemeral=True)
			return

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

		new_recruit_data = await self.recruit_model.get_recruit_by_id(new_recruit_id)
		if new_recruit_data:
			await self._send_or_update_recruit_message(ch, new_recruit_data)
		else:
			await interaction.followup.send("エラー: 保存された募集データの取得に失敗しました。", ephemeral=True)
			
		await self._ensure_header(ch)
		await interaction.followup.send("募集が作成されました！", ephemeral=True)