# -*- coding: utf-8 -*-
# 変更点: 「新たな募集を追加」ボタンをスレッドへボタンの右側に配置
# → JoinLeaveButtons から “新たな募集を追加” を外し
#   send_recruit() でスレッドボタンの直後に追加する

import asyncio, re, discord
import os
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

recruit_data: list["Recruit"] = []
header_msg_id: int | None = None

# .envファイルを読み込む
load_dotenv()

# 環境変数からDiscordボットトークンを取得
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if TOKEN is None:
    print("エラー: DISCORD_BOT_TOKEN 環境変数が設定されていません。")
    exit(1)

# 環境変数からCHANNEL_IDを取得し、int型に変換
# チャンネルIDは数値なので、int() で変換しておく
try:
    CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
except (TypeError, ValueError):
    print("エラー: CHANNEL_ID 環境変数が不正、または設定されていません。")
    exit(1)

TOPIC_TEXT = ("📌 **GD 練習チャンネル案内**\n"
              "・新規募集はボタンから作成してください。\n"
              "・各募集のボタンで参加/取り消しができます。")


# ───────── ヘルパ ─────────
async def remove_thread_system_msg(ch):
    await asyncio.sleep(0.5)
    async for m in ch.history(limit=1):
        if m.type is discord.MessageType.thread_created:
            try:
                await m.delete()
            except discord.Forbidden:
                pass


# ─────────────────────────


class Recruit:

    def __init__(self, rid, date_s, place, cap, note, thread_id):
        self.id = rid
        self.date = date_s
        self.place = place
        self.max_people = cap
        self.note = note
        self.participants: list[discord.Member] = []
        self.thread_id = thread_id
        self.msg_id: int | None = None

    def is_full(self):
        return len(self.participants) >= self.max_people

    def is_joined(self, u):
        return u and any(p.id == u.id for p in self.participants)

    def block(self):
        l1 = f"\U0001F4C5 {self.date}   \U0001F9D1 {len(self.participants)}/{self.max_people}名"
        l2 = f"{self.place}"
        l3 = f"{self.note}" if self.note else ""
        l4 = "\U0001F7E8 満員" if self.is_full() else "⬜ 募集中"
        l5 = "👥 参加者: " + (", ".join(
            p.display_name
            for p in self.participants) if self.participants else "なし")
        return f"```\n{l1}\n{l2}\n{l3}\n{l4}\n{l5}\n```"


# ───────── ボタンビュー ─────────
class JoinLeaveButtons(discord.ui.View):

    def __init__(self, rid):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(label="参加予定に追加",
                              style=discord.ButtonStyle.success,
                              custom_id=f"join:{rid}"))
        self.add_item(
            discord.ui.Button(label="参加予定を削除",
                              style=discord.ButtonStyle.secondary,
                              custom_id=f"leave:{rid}"))


# ───────── ヘッダビュー ─────────
class MakeButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="募集を作成",
                         style=discord.ButtonStyle.primary,
                         custom_id="make")

    async def callback(self, it):
        await it.response.send_modal(RecruitModal())


class RefreshButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="最新状況を反映",
                         style=discord.ButtonStyle.secondary,
                         custom_id="refresh")

    async def callback(self, it):
        blocks = "\n".join(r.block() for r in recruit_data) or "現在募集はありません。"
        await it.response.send_message(blocks, ephemeral=True)


class HeaderView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MakeButton())
        self.add_item(RefreshButton())


# ───────── 送信ユーティリティ ─────────
async def ensure_header(ch):
    global header_msg_id
    if recruit_data and header_msg_id:
        try:
            await (await ch.fetch_message(header_msg_id)).delete()
        except discord.NotFound:
            pass
        header_msg_id = None
    elif not recruit_data and header_msg_id is None:
        header_msg_id = (await ch.send("📢 ボタンはこちら", view=HeaderView())).id


async def send_recruit(ch, rc: Recruit):
    content = rc.block()
    view = JoinLeaveButtons(rc.id)
    # スレッドへボタン
    view.add_item(
        discord.ui.Button(
            label="スレッドへ",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{ch.guild.id}/{rc.thread_id}"))
    # 新たな募集を追加（スレッドへボタンの右側）
    view.add_item(
        discord.ui.Button(label="新たな募集を追加",
                          style=discord.ButtonStyle.primary,
                          custom_id="make"))

    if rc.msg_id:
        try:
            await (await ch.fetch_message(rc.msg_id)).edit(content=content,
                                                           view=view)
            return
        except discord.NotFound:
            pass

    msg = await ch.send(content, view=view)
    rc.msg_id = msg.id
    await asyncio.sleep(0.5)
    try:
        await msg.edit(content=content, view=view)
    except discord.NotFound:
        pass


# ───────── モーダル ─────────
class RecruitModal(discord.ui.Modal, title="GD練習 募集作成フォーム"):
    md = discord.ui.TextInput(label="日付 (MM/DD)",
                              placeholder="06/30",
                              max_length=5,
                              required=True)
    hm = discord.ui.TextInput(label="時刻 (HH:MM)",
                              placeholder="18:00",
                              max_length=5,
                              required=True)
    place = discord.ui.TextInput(label="場所（Zoomなど）", required=True)
    cap = discord.ui.TextInput(label="募集人数",
                               placeholder="4",
                               max_length=3,
                               required=True)
    note = discord.ui.TextInput(label="備考（任意）", required=False)

    async def on_submit(self, it):
        await it.response.defer(ephemeral=True)
        if not re.fullmatch(r"\d{1,2}/\d{1,2}",
                            self.md.value) or not re.fullmatch(
                                r"\d{1,2}:\d{1,2}", self.hm.value):
            return await it.followup.send("日付は MM/DD、時刻は HH:MM 形式で入力してください。",
                                          ephemeral=True)
        m, d = map(int, self.md.value.split("/"))
        h, mi = map(int, self.hm.value.split(":"))
        if not (1 <= m <= 12 and 1 <= d <= 31 and 0 <= h <= 23
                and 0 <= mi <= 59):
            return await it.followup.send("日付または時刻が範囲外です。", ephemeral=True)
        try:
            cap_int = int(self.cap.value)
        except ValueError:
            return await it.followup.send("募集人数は数値で入力してください。", ephemeral=True)

        date_s = f"{m:02}/{d:02} {h:02}:{mi:02}"
        ch = bot.get_channel(CHANNEL_ID)
        th = await ch.create_thread(name=f"🗨 {date_s} GD練習について",
                                    type=discord.ChannelType.public_thread)
        await remove_thread_system_msg(ch)

        rc = Recruit(len(recruit_data), date_s, self.place.value, cap_int,
                     self.note.value, th.id)
        recruit_data.append(rc)
        await send_recruit(ch, rc)
        await ensure_header(ch)


# ───────── BOT イベント ─────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    ch = bot.get_channel(CHANNEL_ID)
    try:
        await ch.edit(topic=TOPIC_TEXT)
    except discord.Forbidden:
        print("⚠ トピック権限なし")
    await ensure_header(ch)
    print("✅ ready")


@bot.event
async def on_interaction(it: discord.Interaction):
    if it.type.name != "component": return
    cid = it.data.get("custom_id")
    # make: new modal
    if cid == "make":
        return await it.response.send_modal(RecruitModal())
    if cid == "refresh": return  # refresh は view 内で完結

    # join/leave
    if ":" not in cid: return
    act, rid_str = cid.split(":", 1)
    if not rid_str.isdigit(): return
    rid = int(rid_str)
    if not 0 <= rid < len(recruit_data): return

    if not it.response.is_done():
        try:
            await it.response.defer(thinking=False)
        except discord.HTTPException:
            pass

    rc = recruit_data[rid]
    u = it.user
    if act == "join" and not rc.is_joined(u) and not rc.is_full():
        rc.participants.append(u)
    elif act == "leave":
        rc.participants = [p for p in rc.participants if p.id != u.id]

    await send_recruit(bot.get_channel(CHANNEL_ID), rc)
    await ensure_header(bot.get_channel(CHANNEL_ID))


bot.run(
    "test")
