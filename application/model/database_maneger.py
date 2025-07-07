# application/model/database_manager.py
import mysql.connector
import os
from dotenv import load_dotenv # 環境変数をここで読み込む

# 環境変数をロード
load_dotenv()

# MySQL接続情報
# .envファイルからこれらの情報を取得
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

class DatabaseManager:
    """
    MySQLデータベースへの接続と基本的な操作を管理するクラス。
    """

    @staticmethod
    def _get_connection():
        """データベース接続を返す"""
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            return conn
        except mysql.connector.Error as err:
            print(f"データベース接続エラー: {err}")
            # 本番環境では、ここで適切なロギングや再試行ロジックを追加
            raise err

    @staticmethod
    def initialize_db():
        """データベースとテーブルを初期化する"""
        conn = None
        try:
            conn = DatabaseManager._get_connection()
            cursor = conn.cursor()

            # participants はJSON文字列として保存するためTEXT型
            # MySQLのJSON型も利用可能ですが、ここでは互換性のためTEXTで扱います
            # DiscordのIDは大きい数値になるため BIGINT を使用
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recruits (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date_s VARCHAR(255) NOT NULL,
                    place VARCHAR(255) NOT NULL,
                    max_people INT NOT NULL,
                    note TEXT,
                    thread_id BIGINT NOT NULL,
                    msg_id BIGINT,
                    participants TEXT DEFAULT '[]' -- JSON配列として保存
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """) # 日本語対応のため文字コード指定
            conn.commit()
            print(f"MySQLデータベース '{DB_NAME}' のテーブルが初期化されました。")
        except mysql.connector.Error as e:
            print(f"データベースの初期化中にエラーが発生しました: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    @staticmethod
    async def execute_query(query: str, params: tuple = ()) -> int | None:
        """INSERT, UPDATE, DELETE クエリを実行し、lastrowid を返す（もしあれば）"""
        conn = None
        try:
            conn = DatabaseManager._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid # MySQLでは `lastrowid` が `cursor.lastrowid` で取得できる
        except mysql.connector.Error as e:
            print(f"MySQLクエリ実行中にエラーが発生しました: {query} - {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    async def fetch_one(query: str, params: tuple = ()) -> dict | None:
        """単一の結果を取得するクエリを実行し、辞書として返す"""
        conn = None
        try:
            conn = DatabaseManager._get_connection()
            cursor = conn.cursor(dictionary=True) # 辞書形式で結果を取得するよう設定
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row
        except mysql.connector.Error as e:
            print(f"MySQLクエリ実行中にエラーが発生しました: {query} - {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    async def fetch_all(query: str, params: tuple = ()) -> list[dict]:
        """複数の結果を取得するクエリを実行し、辞書のリストとして返す"""
        conn = None
        try:
            conn = DatabaseManager._get_connection()
            cursor = conn.cursor(dictionary=True) # 辞書形式で結果を取得するよう設定
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return rows
        except mysql.connector.Error as e:
            print(f"MySQLクエリ実行中にエラーが発生しました: {query} - {e}")
            return []
        finally:
            if conn:
                conn.close()