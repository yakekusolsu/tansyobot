import os
import discord
from discord import app_commands
import asyncio

# --- 設定エリア ---
# 直接トークンを書かず、環境変数 "tansyobot" から読み込みます
# Render.comの管理画面で Key: tansyobot / Value: (あなたのトークン) を設定してください
TOKEN = os.getenv("tansyobot")
# ----------------

# 47都道府県のリスト
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

@bot.tree.command(name="createrole-todofuken", description="47都道府県のロールを一括作成します")
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

@bot.tree.command(name="deleterole-todofuken", description="作成した都道府県ロールをすべて削除します")
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

        await interaction.followup.send(f"削除完了: {deleted_count}件", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"エラー: {str(e)}", ephemeral=True)

@bot.tree.command(name="setrole", description="自分の都道府県ロールを設定します")
@app_commands.describe(role="設定したい都道府県のロールを選択")
async def setrole(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    if role.name not in TARGET_ROLE_NAMES:
        await interaction.followup.send("エラー：専用ロール以外は設定できません。", ephemeral=True)
        return

    member = interaction.user
    try:
        roles_to_remove = [r for r in member.roles if r.name in TARGET_ROLE_NAMES]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)
        await member.add_roles(role)
        await interaction.followup.send(f"ロールを「{role.name}」に設定しました！", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("権限不足です。Botのロールを一番上に移動してください。", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"エラー: {str(e)}", ephemeral=True)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("エラー: 環境変数 'tansyobot' が設定されていません。")
