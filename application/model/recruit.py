# application/model/recruit.py
import json
import discord # Recruitクラスでdiscord.Memberを使うため

from application.model.database_manager import DatabaseManager

class Recruit:
    """
    GD募集の情報を保持するデータクラス。
    これはデータベースから読み込んだり、DBに書き込む前のデータを一時的に保持したりするのに使われます。
    DBに保存されるデータ形式とは異なる場合があります。
    """
    def __init__(self, rid: int, date_s: str, place: str, cap: int, note: str, thread_id: int,
                 msg_id: int | None = None, participants: list[discord.Member] | None = None):
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
        l1 = f"\U0001F4C5 {self.date}   \U0001F9D1 {len(self.participants)}/{self.max_people}名"
        l2 = f"{self.place}"
        l3 = f"{self.note}" if self.note else ""
        l4 = "\U0001F7E8 満員" if self.is_full() else "⬜ 募集中"
        l5 = "👥 参加者: " + (", ".join(
            p.display_name
            for p in self.participants) if self.participants else "なし")
        return f"```\n{l1}\n{l2}\n{l3}\n{l4}\n{l5}\n```"

class RecruitModel:
    """
    GD募集データに対するビジネスロジックとデータベース操作を管理するクラス。
    """
    def __init__(self):
        pass # DatabaseManagerはstaticなのでインスタンスは不要

    async def add_recruit(self, date_s: str, place: str, max_people: int, note: str, thread_id: int) -> int | None:
        """新しい募集をデータベースに追加する"""
        query = """
            INSERT INTO recruits (date_s, place, max_people, note, thread_id, participants)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # participants は初期状態では空のJSON配列として保存
        participants_json = json.dumps([])
        recruit_id = await DatabaseManager.execute_query(
            query, (date_s, place, max_people, note, thread_id, participants_json)
        )
        return recruit_id

    async def get_all_recruits(self) -> list[dict]:
        """すべての募集データをデータベースから取得する"""
        query = "SELECT * FROM recruits ORDER BY id ASC" # ID順で取得
        rows = await DatabaseManager.fetch_all(query)
        # 参加者リストはJSON文字列からPythonリストに変換
        for row in rows:
            # MySQLのTEXT型に保存されたJSONは、mysql.connectorで読み込むと文字列のままなので、
            # ここで手動でjson.loads()する必要がある。
            row['participants'] = json.loads(row['participants']) if row['participants'] else []
        return rows

    async def get_recruit_by_id(self, recruit_id: int) -> dict | None:
        """指定されたIDの募集データをデータベースから取得する"""
        query = "SELECT * FROM recruits WHERE id = %s"
        row = await DatabaseManager.fetch_one(query, (recruit_id,))
        if row:
            # 参加者リストはJSON文字列からPythonリストに変換
            row['participants'] = json.loads(row['participants']) if row['participants'] else []
        return row

    async def update_recruit_participants(self, recruit_id: int, participants_list: list[int]):
        """募集の参加者リストを更新する"""
        participants_json = json.dumps(participants_list)
        query = "UPDATE recruits SET participants = %s WHERE id = %s"
        await DatabaseManager.execute_query(query, (participants_json, recruit_id))

    async def update_recruit_message_id(self, recruit_id: int, message_id: int):
        """募集メッセージのIDを更新する"""
        query = "UPDATE recruits SET msg_id = %s WHERE id = %s"
        await DatabaseManager.execute_query(query, (message_id, recruit_id))

    async def delete_recruit(self, recruit_id: int):
        """指定されたIDの募集を削除する"""
        query = "DELETE FROM recruits WHERE id = %s"
        await DatabaseManager.execute_query(query, (recruit_id,))

    # その他のCRUD操作（募集情報の編集など）もここに追加可能