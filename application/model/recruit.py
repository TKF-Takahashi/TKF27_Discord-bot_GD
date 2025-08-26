import json
import discord
from typing import Union

from .database_manager import DatabaseManager

class Recruit:
	"""
	GD募集の情報を保持するデータクラス。
	"""
	def __init__(self, rid: int, date_s: str, place: str, cap: int, note: str, thread_id: int,
				 msg_id: Union[int, None] = None, participants: Union[list[discord.Member], None] = None):
		self.id = rid
		self.date = date_s
		self.place = place
		self.max_people = cap
		self.note = note
		self.participants: list[discord.Member] = participants if participants is not None else []
		self.thread_id = thread_id
		self.msg_id = msg_id

	def is_full(self) -> bool:
		return len(self.participants) >= self.max_people

	def is_joined(self, u: discord.Member) -> bool:
		return u and any(p.id == u.id for p in self.participants)

	def block(self) -> str:
		"""募集情報を整形して表示用の文字列を生成する"""
		# [変更] 1. スロット絵文字のロジックを指示通りに修正
		filled_slots = len(self.participants)
		empty_slots = self.max_people - filled_slots
		slot_emojis = '🧑' * filled_slots + '・' * empty_slots

		# --- 備考欄の解析 ---
		note_message = ""
		mentor_on = False
		industry = ""
		if self.note:
			note_parts = self.note.split(' / ')
			remaining_parts = []
			for part in note_parts:
				if part == "メンター希望":
					mentor_on = True
				elif part.startswith("想定業界: "):
					industry = part.replace("想定業界: ", "", 1)
				else:
					remaining_parts.append(part)
			note_message = " ".join(remaining_parts)

		# --- 各行の組み立て ---
		lines = []
		# [変更] slot_emojisの前にあった固定の🧑を削除
		lines.append(f"📅 {self.date}   {filled_slots}/{self.max_people}名 {slot_emojis}")
		lines.append("-----------------------------")
		lines.append(f"[メッセージ]  {note_message}" if note_message else "[メッセージ]  なし")
		lines.append("-----------------------------")
		
		if mentor_on:
			lines.append("🤝メンター希望：ON")
		if industry:
			lines.append(f"🏢想定業界: {industry}")
		
		lines.append("🟡 満員" if self.is_full() else "⬜ 募集中")
		
		participants_text = ", ".join(p.display_name for p in self.participants) if self.participants else "なし"
		lines.append(f"👥 参加者: {participants_text}")

		final_text = "\n".join(lines)
		return f"```\n{final_text}\n```"

class RecruitModel:
	"""
	GD募集データに対するビジネスロジックとデータベース操作を管理するクラス。
	"""
	def __init__(self):
		pass

	async def add_recruit(self, date_s: str, place: str, max_people: int, note: str, thread_id: int) -> Union[int, None]:
		"""新しい募集をデータベースに追加する"""
		query = """
			INSERT INTO recruits (date_s, place, max_people, note, thread_id, participants)
			VALUES (?, ?, ?, ?, ?, ?)
		"""
		participants_json = json.dumps([])
		recruit_id = await DatabaseManager.execute_query(
			query, (date_s, place, max_people, note, thread_id, participants_json)
		)
		return recruit_id

	async def get_all_recruits(self) -> list[dict]:
		"""すべての募集データをデータベースから取得する"""
		query = "SELECT * FROM recruits ORDER BY id ASC"
		rows = await DatabaseManager.fetch_all(query)
		for row in rows:
			row['participants'] = json.loads(row['participants']) if row['participants'] else []
		return rows

	async def get_recruit_by_id(self, recruit_id: int) -> Union[dict, None]:
		"""指定されたIDの募集データをデータベースから取得する"""
		query = "SELECT * FROM recruits WHERE id = ?"
		row = await DatabaseManager.fetch_one(query, (recruit_id,))
		if row:
			row['participants'] = json.loads(row['participants']) if row['participants'] else []
		return row

	async def update_recruit_participants(self, recruit_id: int, participants_list: list[int]):
		"""募集の参加者リストを更新する"""
		participants_json = json.dumps(participants_list)
		query = "UPDATE recruits SET participants = ? WHERE id = ?"
		await DatabaseManager.execute_query(query, (participants_json, recruit_id))

	async def update_recruit_message_id(self, recruit_id: int, message_id: int):
		"""募集メッセージのIDを更新する"""
		query = "UPDATE recruits SET msg_id = ? WHERE id = ?"
		await DatabaseManager.execute_query(query, (message_id, recruit_id))

	async def delete_recruit(self, recruit_id: int):
		"""指定されたIDの募集を削除する"""
		query = "DELETE FROM recruits WHERE id = ?"
		await DatabaseManager.execute_query(query, (recruit_id,))