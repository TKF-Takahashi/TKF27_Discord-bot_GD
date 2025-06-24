import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
recruit_data = []  # 各募集情報を記録

CHANNEL_ID = 123456789012345678  # ← #gd-募集状況 のチャンネルIDに置き換えてください

class Recruit:
    def __init__(self, id, date, place, max_people, note, thread_id):
        self.id = id
        self.date = date
        self.place = place
        self.max_people = max_people
        self.note = note
        self.participants = []
        self.thread_id = thread_id

    def is_full(self):
        return len(self.participants) >= self.max_people

    def is_joined(self, user):
        return user.id in [u.id for u in self.participants]

    def status_block(self, user=None):
        line1 = f"\U0001F4C5 {self.date}   \U0001F9D1 {len(self.participants)}/{self.max_people}名"
        line2 = f"{self.place}"
        line3 = f"{self.note}" if self.note else ""

        if self.is_joined(user):
            line4 = "\u2705 あなたは参加予定"
            buttons = [JoinLeaveButtons(self.id, joined=True)]
        elif self.is_full():
            line4 = "\U0001F7E8 満員"
            buttons = []
        else:
            line4 = "⬜ 募集中"
            buttons = [JoinLeaveButtons(self.id, joined=False)]

        return f"```\n{line1}\n{line2}\n{line3}\n{line4}\n```", buttons

class JoinLeaveButtons(discord.ui.View):
    def __init__(self, rid, joined):
        super().__init__(timeout=None)
        self.rid = rid
        self.joined = joined
        if joined:
            self.add_item(discord.ui.Button(label="戻る", style=discord.ButtonStyle.secondary, custom_id=f"leave:{rid}"))
        else:
            self.add_item(discord.ui.Button(label="参加予定に追加", style=discord.ButtonStyle.success, custom_id=f"join:{rid}"))

class RecruitModal(discord.ui.Modal, title="GD練習 募集作成フォーム"):
    date = discord.ui.TextInput(label="開催日時", placeholder="6/26 18:00～", required=True)
    place = discord.ui.TextInput(label="場所（Zoomなど）", placeholder="Zoomリンクなど", required=True)
    max_people = discord.ui.TextInput(label="募集人数", placeholder="4", required=True)
    note = discord.ui.TextInput(label="備考（任意）", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_people = int(self.max_people.value)
        except ValueError:
            await interaction.response.send_message("人数は数値で入力してください。", ephemeral=True)
            return

        channel = bot.get_channel(CHANNEL_ID)
        thread = await channel.create_thread(name=f"🗨 {self.date.value} GD練習について", type=discord.ChannelType.public_thread)
        rid = len(recruit_data)
        recruit = Recruit(rid, self.date.value, self.place.value, max_people, self.note.value, thread.id)
        recruit_data.append(recruit)

        await update_category_view(channel, interaction.user)
        await interaction.response.send_message("募集を作成しました。", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is ready as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("📢 新しいGD練習の募集を開始したい方はこちら", view=RecruitCreateButton())

class RecruitCreateButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="募集を作成", style=discord.ButtonStyle.primary, custom_id="create_modal"))

@bot.event
async def on_socket_response(payload):
    if payload.get("t") != "INTERACTION_CREATE":
        return
    d = payload["d"]
    custom_id = d["data"].get("custom_id")
    if not custom_id:
        return

    user_id = int(d["member"]["user"]["id"])
    rid = int(custom_id.split(":")[1]) if ":" in custom_id else None
    user = await bot.fetch_user(user_id)

    if custom_id == "create_modal":
        interaction = await discord.Interaction._from_socket(bot, d, None)
        await interaction.response.send_modal(RecruitModal())
        return

    recruit = recruit_data[rid]
    if custom_id.startswith("join"):
        if not recruit.is_joined(user):
            recruit.participants.append(user)
    elif custom_id.startswith("leave"):
        recruit.participants = [u for u in recruit.participants if u.id != user.id]

    channel = bot.get_channel(CHANNEL_ID)
    await update_category_view(channel, user)

async def update_category_view(channel, user=None):
    await channel.purge(limit=50)
    await channel.send("📢 新しいGD練習の募集を開始したい方はこちら", view=RecruitCreateButton())

    空, 満, 参加 = [], [], []
    for r in recruit_data:
        box, buttons = r.status_block(user)
        if r.is_joined(user):
            参加.append((box, buttons))
        elif r.is_full():
            満.append((box, buttons))
        else:
            空.append((box, buttons))

    async def send_category(title, color, items):
        await channel.send(f"{color} **[{title}]**")
        for box, view in items:
            await channel.send(box, view=view if view else None)

    await send_category("空", "\U0001F7E9", 空)
    await send_category("満", "\U0001F7E8", 満)
    await send_category("参加予定", "\U0001F7E5", 参加)

bot.run("YOUR_BOT_TOKEN")