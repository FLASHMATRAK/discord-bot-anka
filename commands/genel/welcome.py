import discord


def setup(bot):
    """Yeni katılan üyeye hoşgeldin mesajı gönderir. Komut değil, member_join dinleyicisidir."""

    async def handle_member_join(member: discord.Member):
        channel = member.guild.get_channel(bot.config["welcome_channel_id"])
        if channel:
            embed = discord.Embed(
                title=f"👋 Welcome, {member.display_name}!",
                description=f"Glad to have you here, {member.mention}. Check out the rules with `/rules` and see all commands with `/help`.",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

        try:
            await member.send(f"👋 Welcome to **{member.guild.name}**! Type `/help` in the server to see what I can do.")
        except discord.Forbidden:
            pass

    bot.member_join_handlers.append(handle_member_join)
