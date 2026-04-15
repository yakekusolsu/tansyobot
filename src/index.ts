import { serve } from "@hono/node-server";
import healthCheckServer from "./server";
import { startHealthCheckCron } from "./cron";

// ... Discord BOTのコード ...

!pip install discord.py[voice] nest_asyncio
import discord
from discord import app_commands
import asyncio
import nest_asyncio

# --- 設定エリア ---
# ここにDiscord Developer Portalで取得したTOKENを貼り付けてください
TOKEN = 'MTQ3MTgwNjA5NjQ1NTg5NzE3MA.G4ykRu.CfuESj6-Dz7S2LcXFVpPiPUel0fgn4Kht_SPOs'
# ----------------

# Setup nest_asyncio to allow discord.py to run in a Colab environment
nest_asyncio.apply()

# List of 47 prefectures in Japan (Japanese / English)
PREFECTURES = [
    ("北海道", "Hokkaido"), ("青森県", "Aomori"), ("岩手県", "Iwate"), ("宮城県", "Miyagi"),
    ("秋田県", "Akita"), ("山形県", "Yamagata"), ("福島県", "Fukushima"), ("茨城県", "Ibaraki"),
    ("栃木県", "Tochigi"), ("群馬県", "Gunma"), ("埼玉県", "Saitama"), ("千葉県", "Chiba"),
    ("東京都", "Tokyo"), ("神奈川県", "Kanagawa"), ("新潟県", "Niigata"), ("富山県", "Toyama"),
    ("石川県", "Ishikawa"), ("福井県", "Fukui"), ("山梨県", "Yamanashi"), ("長野県", "Nagano"),
    ("岐阜県", "Gifu"), ("静岡県", "Shizuoka"), ("愛知県", "Aichi"), ("三重県", "Mie"),
    ("滋賀県", "Shiga"), ("京都府", "Kyoto"), ("大阪府", "Osaka"), ("兵庫県", "Hyogo"),
    ("奈良県", "Nara"), ("和歌山県", "Wakayama"), ("鳥取県", "Tottori"), ("島根県", "Shimane"),
    ("岡山県", "Okayama"), ("広島県", "Hiroshima"), ("山口県", "Yamaguchi"), ("徳島県", "Tokushima"),
    ("香川県", "Kagawa"), ("愛媛県", "Ehime"), ("高知県", "Kochi"), ("福岡県", "Fukuoka"),
    ("佐賀県", "Saga"), ("長崎県", "Nagasaki"), ("熊本県", "Kumamoto"), ("大分県", "Oita"),
    ("宮崎県", "Miyazaki"), ("鹿児島県", "Kagoshima"), ("沖縄県", "Okinawa")
]

ROLE_COLOR = discord.Color.from_str("#62c5e0")

# Pre-generate target role names for comparison with the format: "【都道府県】日本語／English"
TARGET_ROLE_NAMES = [f"【都道府県】{jp}／{en}" for jp, en in PREFECTURES]

class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

bot = MyBot()

@bot.tree.command(name="createrole-todofuken", description="47都道府県のロールを一括作成します (【都道府県】日本語／英語形式)")
@app_commands.checks.has_permissions(administrator=True)
async def createrole_todofuken(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    existing_roles = [role.name for role in guild.roles]
    created_count = 0
    skipped_count = 0

    try:
        for jp, en in PREFECTURES:
            role_name = f"【都道府県】{jp}／{en}"
            if role_name not in existing_roles:
                await guild.create_role(
                    name=role_name,
                    color=ROLE_COLOR,
                    reason="Prefecture role creation command"
                )
                created_count += 1
                await asyncio.sleep(0.2)
            else:
                skipped_count += 1

        await interaction.followup.send(
            f"ロールの作成が完了しました！\n新規作成: {created_count}件\n既存のためスキップ: {skipped_count}件",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {str(e)}", ephemeral=True)

@bot.tree.command(name="deleterole-todofuken", description="作成した47都道府県のロールをすべて削除します")
@app_commands.checks.has_permissions(administrator=True)
async def deleterole_todofuken(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    deleted_count = 0

    try:
        for role in list(guild.roles):
            if role.name in TARGET_ROLE_NAMES:
                await role.delete(reason="Prefecture role deletion command")
                deleted_count += 1
                await asyncio.sleep(0.2)

        await interaction.followup.send(
            f"ロールの削除が完了しました！\n削除済み: {deleted_count}件",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {str(e)}", ephemeral=True)

@bot.tree.command(name="list-todofuken", description="作成済みの都道府県ロール一覧を表示します")
async def list_todofuken(interaction: discord.Interaction):
    """
    Shows a list of all prefecture roles and indicates which ones exist in the server.
    """
    guild = interaction.guild
    existing_roles = [role.name for role in guild.roles]
    
    # Building the list
    lines = []
    found_count = 0
    
    for name in TARGET_ROLE_NAMES:
        if name in existing_roles:
            lines.append(f"✅ {name}")
            found_count += 1
        else:
            lines.append(f"❌ {name}")
    
    # Splitting into chunks because Discord has a 2000 character limit per message
    full_text = f"**都道府県ロール状況 ({found_count}/47)**\n\n" + "\n".join(lines)
    
    # If the text is too long, we might need to send it in parts (usually 47 roles fit in 2000 chars)
    if len(full_text) > 2000:
        parts = [full_text[i:i+1900] for i in range(0, len(full_text), 1900)]
        for i, part in enumerate(parts):
            if i == 0:
                await interaction.response.send_message(part, ephemeral=True)
            else:
                await interaction.followup.send(part, ephemeral=True)
    else:
        await interaction.response.send_message(full_text, ephemeral=True)

@bot.tree.command(name="setrole", description="自分の都道府県ロールを設定します (【都道府県】形式のみ付与可能)")
@app_commands.describe(role="設定したい都道府県のロールを選択してください")
async def setrole(interaction: discord.Interaction, role: discord.Role):
    """
    Assigns a prefecture role to the user and removes other prefecture roles.
    ONLY allows roles present in TARGET_ROLE_NAMES.
    """
    await interaction.response.defer(ephemeral=True)

    # STRICT CHECK: Ensure the selected role name is exactly in our predefined list
    if role.name not in TARGET_ROLE_NAMES:
        await interaction.followup.send(
            "エラー：このコマンドでは「【都道府県】」から始まる専用ロール以外は設定できません。",
            ephemeral=True
        )
        return

    member = interaction.user
    
    try:
        # Remove any other existing prefecture roles first
        roles_to_remove = [r for r in member.roles if r.name in TARGET_ROLE_NAMES]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        # Add the newly selected prefecture role
        await member.add_roles(role)
        await interaction.followup.send(
            f"ロールを「{role.name}」に設定しました！",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "権限不足です。Botのロールをサーバー設定の「ロール」一覧で、都道府県ロールよりも上に移動させてください。",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {str(e)}", ephemeral=True)

# Run the bot with the token specified above
if __name__ == "__main__":
    bot.run(TOKEN)

// Koyeb用のヘルスチェックサーバーを起動
serve({
  fetch: healthCheckServer.fetch,
  port: 8000,
});
startHealthCheckCron();
