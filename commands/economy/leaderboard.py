import discord
from discord.ext import commands
from utils.economy_manager import EconomyManager

economy = EconomyManager()

def setup(bot):
    @bot.command(name="rich")
    async def rich(ctx):
        rows = economy.get_rich_leaderboard()[:10]
        if not rows:
            return await ctx.send("📊 Henüz veri yok.")
        lines = []
        for i, row in enumerate(rows, 1):
            member = ctx.guild.get_member(int(row["user_id"]))
            name = member.display_name if member else row["user_id"]
            lines.append(f"**{i}.** {name} — 💎 {row['total']:,}")
        await ctx.send("🏆 **En Zenginler**\n" + "\n".join(lines))

    @bot.command(name="collectors")
    async def collectors(ctx):
        rows = economy.get_collectors_leaderboard()[:10]
        if not rows:
            return await ctx.send("📊 Henüz koleksiyon verisi yok.")
        lines = []
        for i, row in enumerate(rows, 1):
            member = ctx.guild.get_member(int(row["user_id"]))
            name = member.display_name if member else row["user_id"]
            lines.append(f"**{i}.** {name} — {row['unique_items']} farklı / {row['items']} toplam")
        await ctx.send("🎒 **Koleksiyoncular**\n" + "\n".join(lines))

    @bot.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(ctx):
        await rich(ctx)
