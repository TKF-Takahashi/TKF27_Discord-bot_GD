# application/model/recruit.py
import json
import discord
from typing import Union
from datetime import datetime, timedelta
import pytz

from .database_manager import DatabaseManager

class Recruit:
	"""
	GD募集の情報を保持するデータクラス。
	"""
	def __init__(self, rid: int, date_s: str, place: str, cap: int, message: str, mentor_needed: bool, industry: str,
					thread_id: int,
					author: Union[discord.Member, None],
					msg_id: Union[int, None] = None, 
					participants: Union[list[discord.Member], None] = None,
					mentors: Union[list[discord.Member], None] = None,
					is_deleted: bool = False):
		self.id = rid
		self.date_str = date_s
		self.place = place
		self.max_people = cap
		self.message = message
		self.mentor_needed = mentor_needed
		self.industry = industry
		self.participants: list[discord.Member] = participants if participants is not None else []
		self.mentors: list[discord.Member] = mentors if mentors is not None else []
		self.thread_id = thread_id
		self.msg_id = msg_id
		self.author = author
		self.is_deleted = is_deleted

	def is_full(self) -> bool:
		return len(self.participants) >= self.max_people

	def is_joined(self, u: discord.Member) -> bool:
		is_participant = any(p.id == u.id for p in self.participants)
		is_mentor = any(m.id == u.id for m in self.mentors)
		return u and (is_participant or is_mentor)

	def is_expired(self) -> bool:
		try:
			jst = pytz.timezone('Asia/Tokyo')
			recruit_datetime_naive = datetime.strptime(self.date_str, "%Y/%m/%d %H:%M")
			recruit_datetime = jst.localize(recruit_datetime_naive)
			now_jst = datetime.now(jst)
			return recruit_datetime < now_jst - timedelta(hours=1)
		except (ValueError, pytz.UnknownTimeZoneError):
			return True # 日付形式が不正な場合は終了と見なす

	def block(self) -> str:
		"""募集情報を整形して表示用の文字列を生成する"""
		filled_slots = len(self.participants)
		empty_slots = self.max_people - filled_slots
		slot_emojis = '🧑' * filled_slots + '・' * empty_slots
		
		state_label = ""
		if self.is_deleted:
			state_label = "【削除】"
		elif self.is_expired():
			state_label = "【終了】"

		# 終了または削除された募集の表示
		if state_label:
			header_line = f"{state_label}📅 {self.date_str}"
			info_lines = []
			info_lines.append(f"({filled_slots}/{self.max_people}名)")
			info_lines.append("-----------------------------")
			if self.author:
				info_lines.append(f"👤 募集者：{self.author.display_name}")
			else:
				info_lines.append(f"👤 募集者：不明なユーザー")
			info_lines.append("-----------------------------")
			info_lines.append("【場所】")
			info_lines.append(self.place)
			info_lines.append("-----------------------------")
			info_lines.append("【メッセージ】")
			info_lines.append(self.message if self.message else "なし")
			info_lines.append("-----------------------------")
			info_block = "```\n" + "\n".join(info_lines) + "\n```"
			return f"> {header_line}\n{info_block}"
		
		# 通常の募集の表示
		header_line = f"# 📅 {self.date_str}"
		info_lines = []
		info_lines.append(f"({filled_slots}/{self.max_people}名)  [{slot_emojis}]")
		info_lines.append("-----------------------------")
		if self.author:
			info_lines.append(f"👤 募集者：{self.author.display_name}")
		else:
			info_lines.append(f"👤 募集者：不明なユーザー")
		info_lines.append("-----------------------------")
		info_lines.append("【場所】")
		info_lines.append(self.place)
		info_lines.append("-----------------------------")
		info_lines.append("【メッセージ】")
		info_lines.append(self.message if self.message else "なし")
		info_lines.append("-----------------------------")

		if self.mentor_needed:
			info_lines.append("🤝メンター希望：ON")
		if self.industry:
			info_lines.append(f"🏢想定業界: {self.industry}")
		
		info_lines.append("🟡 満員" if self.is_full() else "⬜ 募集中")
		
		participants_text = ", ".join(p.display_name for p in self.participants) if self.participants else "なし"
		info_lines.append(f"👥 参加者：{participants_text}")

		mentors_text = ", ".join(m.display_name for m in self.mentors) if self.mentors else "なし"
		info_lines.append(f"🤝 メンター：{mentors_text}")
		
		info_block = "```\n" + "\n".join(info_lines) + "\n```"

		return f"{header_line}\n{info_block}"


class RecruitModel:
	"""
	GD募集データに対するビジネスロジックとデータベース操作を管理するクラス。
	"""
	def __init__(self):
		pass

	async def get_setting(self, key: str) -> Union[str, None]:
		from .database_manager import DatabaseManager
		return await DatabaseManager.get_setting(key)

	async def add_recruit(self, date_s: str, place: str, max_people: int, message: str, mentor_needed: bool, industry: str, thread_id: int, author_id: int, participants: list[int]) -> Union[int, None]:
		query = """
			INSERT INTO recruits (date_s, place, max_people, message, mentor_needed, industry, thread_id, author_id, participants, mentors)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		"""
		participants_json = json.dumps(participants)
		mentors_json = json.dumps([]) # 新規作成時はメンターは空
		recruit_id = await DatabaseManager.execute_query(
			query, (date_s, place, max_people, message, int(mentor_needed), industry, thread_id, author_id, participants_json, mentors_json)
		)
		return recruit_id

	async def update_recruit(self, recruit_id: int, data: dict):
		"""指定されたIDの募集データを更新する"""
		query = """
			UPDATE recruits SET date_s = ?, place = ?, max_people = ?, message = ?, mentor_needed = ?, industry = ? WHERE id = ?
		"""
		await DatabaseManager.execute_query(
			query, (data['date_s'], data['place'], data['max_people'], data['message'], int(data['mentor_needed']), data['industry'], recruit_id)
		)

	async def get_all_recruits(self) -> list[dict]:
		query = "SELECT * FROM recruits ORDER BY id ASC"
		rows = await DatabaseManager.fetch_all(query)
		for row in rows:
			row['participants'] = json.loads(row['participants']) if row['participants'] else []
			row['mentors'] = json.loads(row.get('mentors', '[]')) if row.get('mentors') else []
			row['mentor_needed'] = bool(row.get('mentor_needed'))
			row['notification_sent'] = bool(row.get('notification_sent', 0))
			row['is_deleted'] = bool(row.get('is_deleted', 0))
		return rows

	async def get_recruit_by_id(self, recruit_id: int) -> Union[dict, None]:
		query = "SELECT * FROM recruits WHERE id = ?"
		row = await DatabaseManager.fetch_one(query, (recruit_id,))
		if row:
			row['participants'] = json.loads(row['participants']) if row['participants'] else []
			row['mentors'] = json.loads(row.get('mentors', '[]')) if row.get('mentors') else []
			row['mentor_needed'] = bool(row.get('mentor_needed'))
			row['notification_sent'] = bool(row.get('notification_sent', 0))
			row['is_deleted'] = bool(row.get('is_deleted', 0))
		return row

	async def update_recruit_participants(self, recruit_id: int, participants_list: list[int]):
		query = "UPDATE recruits SET participants = ? WHERE id = ?"
		participants_json = json.dumps(participants_list)
		await DatabaseManager.execute_query(query, (participants_json, recruit_id))

	async def update_recruit_mentors(self, recruit_id: int, mentors_list: list[int]):
		query = "UPDATE recruits SET mentors = ? WHERE id = ?"
		mentors_json = json.dumps(mentors_list)
		await DatabaseManager.execute_query(query, (mentors_json, recruit_id))

	async def update_recruit_message_id(self, recruit_id: int, message_id: int):
		query = "UPDATE recruits SET msg_id = ? WHERE id = ?"
		await DatabaseManager.execute_query(query, (message_id, recruit_id))
		
	async def mark_notification_as_sent(self, recruit_id: int):
		"""[修正点] 通知フラグを立てる"""
		query = "UPDATE recruits SET notification_sent = 1 WHERE id = ?"
		await DatabaseManager.execute_query(query, (recruit_id,))

	async def mark_as_deleted(self, recruit_id: int):
		"""募集を削除済みにマークする"""
		query = "UPDATE recruits SET is_deleted = 1 WHERE id = ?"
		await DatabaseManager.execute_query(query, (recruit_id,))

	async def delete_recruit(self, recruit_id: int):
		query = "DELETE FROM recruits WHERE id = ?"
		await DatabaseManager.execute_query(query, (recruit_id,))