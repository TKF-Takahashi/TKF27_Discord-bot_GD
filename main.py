# main.py
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

# 変更: コントローラーのインポートパス
from application.controller.GD_bot import GDBotController
from application.model.database_manager import DatabaseManager # DB初期化用

# .envファイルを読み込む
load_dotenv()

# 環境変数からDiscordボットトークンを取得
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if TOKEN is None:
    print("エラー: DISCORD_BOT_TOKEN 環境変数が設定されていません。")
    exit(1)

# ▼▼▼【削除】CHANNEL_IDを.envから読み込む処理を削除 ▼▼▼
# try:
#     CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
# except (TypeError, ValueError):
#     print("エラー: CHANNEL_ID 環境変数が不正、または設定されていません。")
#     exit(1)
# ▲▲▲【削除】ここまで ▲▲▲

# Discord Intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

# Botインスタンスの作成
bot = commands.Bot(command_prefix="!", intents=intents)

# データベースの初期化（テーブル作成など）
DatabaseManager.initialize_db()

# ▼▼▼【修正】Controllerの初期化時にCHANNEL_IDを渡さないように変更 ▼▼▼
# Controllerが全てのロジックとイベントハンドリングを担う
GDBotController(bot)
# ▲▲▲【修正】ここまで ▲▲▲

# ボットを起動
bot.run(TOKEN)