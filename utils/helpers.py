import datetime
import discord


async def log_action(bot, interaction: discord.Interaction, member: discord.Member, action_type: str, reason: str):
    """Moderasyon eylemini sabıka kaydına ve log kanalına yazar."""
    from utils import state

    entry = {
        "type": action_type,
        "reason": reason,
        "moderator": interaction.user.display_name,
        "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    state.rap_sheet[member.id].append(entry)

    log_channel = interaction.guild.get_channel(bot.config["log_channel_id"])
    if log_channel:
        embed = discord.Embed(title=f"📋 Yeni Kayıt: {action_type}", color=discord.Color.red())
        embed.add_field(name="Kullanıcı", value=f"{member.mention} ({member.id})", inline=False)
        embed.add_field(name="Yetkili", value=interaction.user.mention, inline=True)
        embed.add_field(name="Sebep", value=reason, inline=True)
        embed.set_footer(text=entry["date"])
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass


def get_role_type(bot, member: discord.Member):
    """Kullanıcının Hunter mı Outlaw mı olduğunu döner, ikisi de yoksa None."""
    role_names = [r.name for r in member.roles]
    if bot.config["hunter_role_name"] in role_names:
        return "Hunter"
    if bot.config["outlaw_role_name"] in role_names:
        return "Outlaw"
    return None


def get_role_emoji(bot, guild: discord.Guild, role_type: str) -> str:
    """Verilen rol tipi için sunucu emojisini döner, bulamazsa varsayılan unicode emoji kullanır."""
    from utils import state

    emoji_name = state.role_icons.get(role_type)
    if emoji_name:
        found = discord.utils.get(guild.emojis, name=emoji_name)
        if found:
            return str(found)
    return "🏹" if role_type == "Hunter" else "🔫"


async def check_and_assign_rank(bot, member: discord.Member, role_type: str, points: int):
    """Kullanıcının puanına göre hak ettiği en yüksek rütbe rolünü verir."""
    rank_table_raw = bot.config["hunter_rank_roles"] if role_type == "Hunter" else bot.config["outlaw_rank_roles"]
    # config.json'daki eşik değerleri string olarak geliyor, int'e çeviriyoruz
    rank_table = {int(k): v for k, v in rank_table_raw.items()}

    earned_role_name = None
    for threshold in sorted(rank_table.keys()):
        if points >= threshold:
            earned_role_name = rank_table[threshold]

    if earned_role_name is None:
        return

    guild = member.guild
    target_role = discord.utils.get(guild.roles, name=earned_role_name)
    if not target_role:
        return

    if target_role not in member.roles:
        old_rank_roles = [discord.utils.get(guild.roles, name=n) for n in rank_table.values()]
        old_rank_roles = [r for r in old_rank_roles if r and r in member.roles]
        try:
            if old_rank_roles:
                await member.remove_roles(*old_rank_roles)
            await member.add_roles(target_role)
        except discord.Forbidden:
            pass
