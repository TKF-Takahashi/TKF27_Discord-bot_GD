# application/model/database_manager.py
import sqlite3
import os
from dotenv import load_dotenv # 環境変数をここで読み込む
from typing import Union # この行を追加

# 環境変数をロード
load_dotenv()

# .envファイルからデータベースのファイルパスを取得（例: DB_NAME=mydatabase.db）
DB_NAME = os.getenv('DB_NAME', 'recruits.db') # .envになければデフォルト値を使用

class DatabaseManager:
	"""
	SQLiteデータベースへの接続と基本的な操作を管理するクラス。
	"""

	@staticmethod
	def _get_connection():
		"""データベース接続を返す"""
		try:
			# sqlite3.connect はDBファイルへのパスを指定
			conn = sqlite3.connect(DB_NAME)
			# 結果を辞書形式で受け取るための設定
			conn.row_factory = sqlite3.Row
			return conn
		except sqlite3.Error as err:
			print(f"データベース接続エラー: {err}")
			raise err

	@staticmethod
	def initialize_db():
		"""データベースとテーブルを初期化する"""
		conn = None
		try:
			conn = DatabaseManager._get_connection()
			cursor = conn.cursor()

			# SQLite 用の CREATE TABLE 文
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS recruits (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					date_s TEXT NOT NULL,
					place TEXT NOT NULL,
					max_people INTEGER NOT NULL,
					note TEXT,
					thread_id INTEGER NOT NULL,
					msg_id INTEGER,
					participants TEXT DEFAULT '[]'
				)
			""")
			conn.commit()
			print(f"SQLiteデータベース '{DB_NAME}' のテーブルが初期化されました。")
		except sqlite3.Error as e:
			print(f"データベースの初期化中にエラーが発生しました: {e}")
			if conn:
				conn.rollback()
		finally:
			if conn:
				conn.close()

	@staticmethod
	async def execute_query(query: str, params: tuple = ()) -> Union[int, None]: # 変更
		"""INSERT, UPDATE, DELETE クエリを実行し、lastrowid を返す"""
		conn = None
		try:
			conn = DatabaseManager._get_connection()
			cursor = conn.cursor()
			cursor.execute(query, params)
			conn.commit()
			return cursor.lastrowid
		except sqlite3.Error as e:
			print(f"SQLiteクエリ実行中にエラーが発生しました: {query} - {e}")
			if conn:
				conn.rollback()
			return None
		finally:
			if conn:
				conn.close()

	@staticmethod
	async def fetch_one(query: str, params: tuple = ()) -> Union[dict, None]: # 変更
		"""単一の結果を取得するクエリを実行し、辞書として返す"""
		conn = None
		try:
			conn = DatabaseManager._get_connection()
			cursor = conn.cursor()
			cursor.execute(query, params)
			row = cursor.fetchone()
			return dict(row) if row else None
		except sqlite3.Error as e:
			print(f"SQLiteクエリ実行中にエラーが発生しました: {query} - {e}")
			return None
		finally:
			if conn:
				conn.close()

	@staticmethod
	async def fetch_all(query: str, params: tuple = ()) -> list[dict]: # list[dict] は変更不要
		"""複数の結果を取得するクエリを実行し、辞書のリストとして返す"""
		conn = None
		try:
			conn = DatabaseManager._get_connection()
			cursor = conn.cursor()
			cursor.execute(query, params)
			rows = cursor.fetchall()
			return [dict(row) for row in rows]
		except sqlite3.Error as e:
			print(f"SQLiteクエリ実行中にエラーが発生しました: {query} - {e}")
			return []
		finally:
			if conn:
				conn.close()