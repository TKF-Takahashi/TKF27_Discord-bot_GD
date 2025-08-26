import discord
import asyncio
from discord.ext import commands
from typing import Union, Set
from datetime import datetime
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
		# [追加] 処理済みインタラクションIDを記録するセット
		self.processed_interactions: Set[int] = set()

		# Botイベントのリスナーを登録
		self.bot.event(self.on_ready)
		self.bot.event(self.on_interaction)

	# (_ensure_header, _send_or_update_recruit_message, on_ready の各メソッドは変更なし)
	# ... (変更のないメソッドは省略) ...

	async def on_interaction(self, it: discord.Interaction):
		"""インタラクション（ボタンクリック、モーダル送信など）を処理"""
		# [追加] 処理が2重に実行されることを防ぐためのチェック
		if it.id in self.processed_interactions:
			return # 既に処理済みの場合はここで終了
		self.processed_interactions.add(it.id)
		# 古いIDをセットから削除する後処理（メモリリーク対策）
		# 600秒(10分)以上前のインタラクションIDを削除
		async def cleanup_interactions():
			await asyncio.sleep(600)
			self.processed_interactions.discard(it.id)
		self.bot.loop.create_task(cleanup_interactions())
		
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

		new_recruit_id = await self.recruit_model.add_recruit(
			date_s=data['date_s'],
			place=data['place'],
			max_people=data['max_people'],
			note=data['note'],
			thread_id=th.id,
			author_id=author_id
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