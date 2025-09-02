# application/controller/GD_bot.py
import discord
import asyncio
from discord.ext import commands, tasks
from typing import Union, Set
from datetime import datetime, timedelta
import pytz

# ... (import文は変更なし) ...
from application.model.recruit import RecruitModel, Recruit
from application.view.recruit import HeaderView, JoinLeaveButtons
from application.view.form_view import RecruitFormView
from application.library.helper import remove_thread_system_msg

TOPIC_TEXT = ("📌 **GD 練習チャンネル案内**\n"
			"・新規募集はボタンから作成してください。\n"
			"・各募集のボタンで参加/取り消しができます。")

class GDBotController:
	"""
	Discordボットのイベント処理とロジックの制御を行うクラス。
	ModelとViewを連携させる。
	"""
	# ▼▼▼【修正】__init__の引数からchannel_idを削除 ▼▼▼
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.channel_id: Union[int, None] = None # DBから読み込むためNoneで初期化
		# ▲▲▲【修正】ここまで ▲▲▲
		self.recruit_model = RecruitModel()
		self.header_msg_id: Union[int, None] = None
		self.ADMIN_ROLE_ID: Union[int, None] = None 
		self.MENTOR_ROLE_ID: Union[int, None] = None

		# Botイベントのリスナーを登録
		self.bot.event(self.on_ready)
		self.bot.event(self.on_interaction)

	# ... (check_expired_recruitsなどのタスク関数は変更なし) ...
	@tasks.loop(minutes=5)
	async def check_expired_recruits(self):
		if not self.channel_id: return
		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			print("定期チェックエラー: チャンネルが見つかりません。")
			return
		all_recruits = await self.recruit_model.get_all_recruits()
		jst = pytz.timezone('Asia/Tokyo')
		now_jst = datetime.now(jst)
		for recruit_data in all_recruits:
			try:
				recruit_datetime_naive = datetime.strptime(recruit_data['date_s'], "%Y/%m/%d %H:%M")
				recruit_datetime_jst = jst.localize(recruit_datetime_naive)
				if recruit_datetime_jst < now_jst - timedelta(hours=1):
					await self._send_or_update_recruit_message(ch, recruit_data)
			except (ValueError, KeyError) as e:
				print(f"定期チェック中にエラーが発生しました (募集ID: {recruit_data.get('id')}): {e}")
				continue

	@tasks.loop(minutes=5)
	async def check_upcoming_recruits(self):
		if not self.channel_id: return
		all_recruits = await self.recruit_model.get_all_recruits()
		jst = pytz.timezone('Asia/Tokyo')
		now_jst = datetime.now(jst)
		in_55_minutes = now_jst + timedelta(minutes=55)
		in_60_minutes = now_jst + timedelta(minutes=60)
		for r in all_recruits:
			if not r.get('notification_sent'):
				try:
					recruit_dt_naive = datetime.strptime(r['date_s'], "%Y/%m/%d %H:%M")
					recruit_dt_jst = jst.localize(recruit_dt_naive)
					if in_55_minutes < recruit_dt_jst <= in_60_minutes:
						all_user_ids = r.get('participants', []) + r.get('mentors', [])
						ch = self.bot.get_channel(self.channel_id)
						thread_url = f"https://discord.com/channels/{ch.guild.id}/{r['thread_id']}" if ch else "スレッドが見つかりません"
						message = (f"📢 **１時間後にGD練習会が始まります**\n" f"-----------------------------\n" f"**日時:** {r['date_s']}\n" f"**場所:** {r['place']}\n" f"**スレッド:** {thread_url}\n" f"-----------------------------\n" f"準備をお願いします！")
						for user_id in all_user_ids:
							try:
								user = await self.bot.fetch_user(user_id)
								await user.send(message)
							except discord.Forbidden:
								print(f"警告: ユーザーID {user_id} にDMを送信できませんでした（ブロックされている可能性があります）。")
							except Exception as e:
								print(f"DM送信中に予期せぬエラー (ユーザーID: {user_id}): {e}")
						await self.recruit_model.mark_notification_as_sent(r['id'])
				except (ValueError, KeyError) as e:
					print(f"通知チェック中にエラー (募集ID: {r.get('id')}): {e}")
					continue

	async def _ensure_header(self, ch: Union[discord.TextChannel, discord.Thread]):
		current_recruits = await self.recruit_model.get_all_recruits()
		jst = pytz.timezone('Asia/Tokyo')
		now_jst = datetime.now(jst)
		active_recruits = [r for r in current_recruits if jst.localize(datetime.strptime(r['date_s'], "%Y/%m/%d %H:%M")) >= now_jst - timedelta(hours=1) and not r.get('is_deleted', False)]
		if active_recruits and self.header_msg_id:
			try:
				header_msg = await ch.fetch_message(self.header_msg_id)
				await header_msg.delete()
				self.header_msg_id = None
			except discord.NotFound:
				self.header_msg_id = None
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
		guild = ch.guild
		participants_members: list[discord.Member] = [await self._safe_fetch_member(guild, user_id) for user_id in recruit_data.get('participants', [])]
		mentors_members: list[discord.Member] = [await self._safe_fetch_member(guild, user_id) for user_id in recruit_data.get('mentors', [])]
		author_member = await self._safe_fetch_member(guild, recruit_data.get('author_id'))
		
		rc = Recruit(
			rid=recruit_data['id'], date_s=recruit_data['date_s'], place=recruit_data['place'], cap=recruit_data['max_people'], message=recruit_data['message'], mentor_needed=bool(recruit_data['mentor_needed']), industry=recruit_data['industry'], thread_id=recruit_data['thread_id'], msg_id=recruit_data['msg_id'], participants=[m for m in participants_members if m], mentors=[m for m in mentors_members if m], author=author_member, is_deleted=recruit_data.get('is_deleted', False)
		)

		content = rc.block()
		if rc.mentor_needed and self.MENTOR_ROLE_ID and not rc.is_expired() and not rc.is_deleted:
			mentor_role = ch.guild.get_role(self.MENTOR_ROLE_ID)
			if mentor_role: content = f"{mentor_role.mention}\n" + content
		
		view = discord.ui.View(timeout=None)
		view.add_item(discord.ui.Button(label="スレッドへ", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{ch.guild.id}/{rc.thread_id}"))
		view.add_item(discord.ui.Button(label="新たな募集を追加", style=discord.ButtonStyle.primary, custom_id="test"))
		if not rc.is_expired() and not rc.is_deleted:
			view = JoinLeaveButtons(self, rc)
		
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
		except discord.Forbidden:
			print("⚠ メッセージ送信権限がありません。")
		except Exception as e:
			print(f"メッセージ送信中に予期せぬエラー: {e}")

	async def _safe_fetch_member(self, guild, user_id):
		if not user_id: return None
		try:
			return await guild.fetch_member(user_id)
		except discord.NotFound:
			print(f"警告: メンバーID {user_id} が見つかりません。")
			return None
		except Exception as e:
			print(f"メンバー取得中に予期せぬエラー ({user_id}): {e}")
			return None

	async def on_ready(self):
		"""ボットが起動した際に実行される処理"""
		await self.bot.tree.sync()

		# ▼▼▼【修正】データベースから各種IDを読み込む ▼▼▼
		try:
			# チャンネルID
			channel_id_str = await self.recruit_model.get_setting('channel_id')
			if not channel_id_str:
				print("エラー: チャンネルIDがデータベースに設定されていません。管理者画面から設定してください。")
				return
			self.channel_id = int(channel_id_str)

			# メンターロールID
			mentor_role_id_str = await self.recruit_model.get_setting('mentor_role_id')
			self.MENTOR_ROLE_ID = int(mentor_role_id_str) if mentor_role_id_str else None
			
			# 管理者ロールID
			admin_role_id_str = await self.recruit_model.get_setting('admin_role_id')
			self.ADMIN_ROLE_ID = int(admin_role_id_str) if admin_role_id_str else None

		except (ValueError, TypeError) as e:
			print(f"IDの読み込み中にエラーが発生しました: {e}")
			return
		# ▲▲▲【修正】ここまで ▲▲▲

		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			print(f"エラー: チャンネルID {self.channel_id} は不正です。")
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

		if not self.check_expired_recruits.is_running():
			self.check_expired_recruits.start()
		
		if not self.check_upcoming_recruits.is_running():
			self.check_upcoming_recruits.start()

		print("✅ ready")

	# ... (on_interaction, handle_recruit_submission, handle_recruit_update 関数は変更なし) ...
	async def on_interaction(self, it: discord.Interaction):
		"""インタラクション（ボタンクリック、モーダル送信など）を処理"""
		if it.type == discord.InteractionType.component and it.data.get("custom_id", "").startswith(("join:", "leave:", "edit:", "delete:", "join_as_mentor", "join_as_member")):
			return

		if it.type.name != "component":
			return

		custom_id = it.data.get("custom_id")
		
		if custom_id == "test":
			if not self.channel_id:
				await it.response.send_message("エラー: Botのチャンネルが設定されていません。", ephemeral=True)
				return
			form_view = RecruitFormView(self)
			embed = form_view.create_embed()
			try:
				await it.response.send_message(embed=embed, view=form_view, ephemeral=True)
			except discord.errors.NotFound:
				print(f"インタラクションエラー: 'Unknown interaction' - custom_id: {custom_id}")
				return
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
					description=recruit_data.get('message', '')
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
		try:
			jst = pytz.timezone('Asia/Tokyo')
			now_jst = datetime.now(jst)
			recruit_datetime_naive = datetime.strptime(data['date_s'], "%Y/%m/%d %H:%M")
			recruit_datetime_jst = jst.localize(recruit_datetime_naive)
			if recruit_datetime_jst < now_jst:
				await interaction.followup.send("エラー: 過去の日時を登録することはできません。", ephemeral=True)
				return
		except ValueError:
			await interaction.followup.send("エラー: 日時の形式が正しくありません。", ephemeral=True)
			return

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
		try:
			jst = pytz.timezone('Asia/Tokyo')
			now_jst = datetime.now(jst)
			recruit_datetime_naive = datetime.strptime(data['date_s'], "%Y/%m/%d %H:%M")
			recruit_datetime_jst = jst.localize(recruit_datetime_naive)
			if recruit_datetime_jst < now_jst:
				await interaction.followup.send("エラー: 過去の日時を登録することはできません。", ephemeral=True)
				return
		except ValueError:
			await interaction.followup.send("エラー: 日時の形式が正しくありません。", ephemeral=True)
			return

		ch = self.bot.get_channel(self.channel_id)
		if not isinstance(ch, (discord.TextChannel, discord.Thread)):
			await interaction.followup.send("エラー: チャンネルが見つかりません。", ephemeral=True)
			return
		
		await self.recruit_model.update_recruit(recruit_id, data)

		updated_recruit_data = await self.recruit_model.get_recruit_by_id(recruit_id)
		if updated_recruit_data:
			try:
				thread = await self.bot.fetch_channel(updated_recruit_data['thread_id'])
				if isinstance(thread, discord.Thread):
					new_thread_name = f"🗨 {updated_recruit_data['date_s']} GD練習について"
					await thread.edit(name=new_thread_name)
			except discord.NotFound:
				print(f"警告: スレッドID {updated_recruit_data['thread_id']} が見つかりません。名前の更新をスキップします。")
			except discord.Forbidden:
				print(f"警告: スレッドID {updated_recruit_data['thread_id']} の名前を変更する権限がありません。")
			except Exception as e:
				print(f"スレッド名の編集中に予期せぬエラー: {e}")

			await self._send_or_update_recruit_message(ch, updated_recruit_data)
		else:
			await interaction.followup.send("エラー: 募集の更新に失敗しました。", ephemeral=True)
		
		await message_to_delete.delete()