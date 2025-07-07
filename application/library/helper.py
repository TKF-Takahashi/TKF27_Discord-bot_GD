# application/library/helpers.py
import asyncio
import discord

async def remove_thread_system_msg(ch: discord.TextChannel | discord.Thread):
    """
    スレッド作成時にDiscordが自動で投稿するシステムメッセージを削除する。
    """
    await asyncio.sleep(0.5) # スレッド作成後のメッセージが読み込まれるのを待つ
    async for m in ch.history(limit=1): # 最新のメッセージ1件を取得
        if m.type is discord.MessageType.thread_created: # スレッド作成メッセージか確認
            try:
                await m.delete()
                print(f"システムメッセージを削除しました: {m.id}")
            except discord.Forbidden:
                print(f"⚠ システムメッセージの削除権限がありません: {m.id}")
            except discord.NotFound:
                print(f"⚠ システムメッセージが見つかりません: {m.id}")
            except Exception as e:
                print(f"システムメッセージ削除中に予期せぬエラー ({m.id}): {e}")
            break # 最初のシステムメッセージを見つけたら終了