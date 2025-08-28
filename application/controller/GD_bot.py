# application/controller/GD_bot.py
import discord
import asyncio
from discord.ext import commands
from typing import Union, Set
from datetime import datetime, timedelta
import pytz

# 実際のプロジェクト構造に合わせてインポートパスを修正してください
from application.model.recruit import RecruitModel, Recruit
from application.view.recruit import HeaderView, JoinLeaveButtons
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
		# 編集権限を持つロールのIDをここに設定してください
		self.EDIT_ROLE_ID = 123456789012345678 # 例：実際のロールIDに置き換えてください

		# Botイベントのリスナーを登録
		self.bot.event(self.on_ready)
		self.bot.event(self.on_interaction)

		# データベースからメンターロールIDを読み込む
		async def _load_mentor_role_id():
			self.MENTOR_ROLE_ID = int(await self.recruit_model.get_setting('mentor_role_id')) if await self.recruit_model.get_setting('mentor_role_id') else None
		self.bot.loop.create_task(_load_mentor_role_id())

	async def _ensure_header(self, ch: Union[discord.TextChannel, discord.Thread]):
		"""ヘッダーメッセージの有無を確認し、必要に応じて更新/削除する"""
		current_recruits = await self.recruit_model.get_all_recruits()
		
		jst = pytz.timezone('Asia/Tokyo')
		now_jst = datetime.now(jst)
		
		# 終了した募集をフィルタリング
		active_recruits = [
			r for r in current_recruits
			if jst.localize(datetime.strptime(r['date_s'], "%Y/%m/%d %H:%M")) >= now_jst - timedelta(hours=1)
		]

		if active_recruits and self.header_msg_id:
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
		elif not active_recruits and self.header_msg_id is None:
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

		author_member = None
		if recruit_data.get('author_id'):
			try:
				author_member = await guild.fetch_member(recruit_data['author_id'])
			except discord.NotFound:
				print(f"警告: 募集者ID {recruit_data['author_id']} のメンバーが見つかりません。")

		rc = Recruit(
			rid=recruit_data['id'],
			date_s=recruit_data['date_s'],
			place=recruit_data['place'],
			cap=recruit_data['max_people'],
			message=recruit_data['message'],
			mentor_needed=bool(recruit_data['mentor_needed']),
			industry=recruit_data['industry'],
			thread_id=recruit_data['thread_id'],
			msg_id=recruit_data['msg_id'],
			participants=participants_members,
			author=author_member,
		)

		content = rc.block()

		if rc.mentor_needed and self.MENTOR_ROLE_ID:
			mentor_role = ch.guild.get_role(self.MENTOR_ROLE_ID)
			if mentor_role:
				content = f"{mentor_role.mention}\n\n" + content
		
		# 終了した募集と、通常の募集でビューを分ける
		if rc.is_expired():
			view = discord.ui.View(timeout=None)
			view.add_item(
				discord.ui.Button(
					label="スレッドへ",
					style=discord.ButtonStyle.link,
					url=f"https://discord.com/channels/{ch.guild.id}/{rc.thread_id}"
				)
			)
			view.add_item(
				discord.ui.Button(
					label="新たな募集を追加",
					style=discord.ButtonStyle.primary,
					custom_id="test"
				)
			)
		else:
			view = JoinLeaveButtons(self, rc.id)
			view.add_item(
				discord.ui.Button(
					label="スレッドへ",
					style=discord.ButtonStyle.link,
					url=f"https://discord.com/channels/{ch.guild.id}/{rc.thread_id}"
				)
			)
			view.add_item(
				discord.ui.Button(
					label="新たな募集を追加",
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
		if it.type == discord.InteractionType.component and it.data.get("custom_id", "").startswith(("join:", "leave:", "edit:")):
			return

		if it.type.name != "component":
			return

		custom_id = it.data.get("custom_id")
		
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

	async def handle_recruit_submission(self, interaction: discord.Interaction, data: dict, message_to_delete: discord.Message):
		"""
		募集データが送信された際の処理 (新しいフォームから呼び出される)
		"""
		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
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

		author_id = interaction.user.id
		initial_participants = [author_id]

		new_recruit_id = await self.recruit_model.add_recruit(
			date_s=data['date_s'],
			place=data['place'],
			max_people=data['max_people'],
			message=data['message'],
			mentor_needed=data['mentor_needed'],
			industry=data['industry'],
			thread_id=th.id,
			author_id=author_id,
			participants=initial_participants,
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
		
		await message_to_delete.delete()

	async def handle_recruit_update(self, interaction: discord.Interaction, recruit_id: int, data: dict, message_to_delete: discord.Message):
		"""
		編集フォームから送信されたデータで既存の募集を更新する
		"""
		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			await interaction.followup.send("エラー: チャンネルが見つかりません。", ephemeral=True)
			return
		
		await self.recruit_model.update_recruit(recruit_id, data)

		updated_recruit_data = await self.recruit_model.get_recruit_by_id(recruit_id)
		if updated_recruit_data:
			await self._send_or_update_recruit_message(ch, updated_recruit_data)
		else:
			await interaction.followup.send("エラー: 募集の更新に失敗しました。", ephemeral=True)
		
		await message_to_delete.delete()