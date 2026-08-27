import discord
from discord import app_commands
from utils import state
from utils.helpers import get_role_emoji


def setup(bot):
    @bot.tree.command(name="leaderboard", description="Shows the Hunter and Outlaw leaderboards.")
    async def leaderboard(interaction: discord.Interaction):
        hunter_sorted = sorted(state.hunter_points.items(), key=lambda x: x[1], reverse=True)[:10]
        outlaw_sorted = sorted(state.outlaw_points.items(), key=lambda x: x[1], reverse=True)[:10]

        embed = discord.Embed(title="🏅 Leaderboard", color=discord.Color.purple())

        hunter_emoji = get_role_emoji(bot, interaction.guild, "Hunter")
        outlaw_emoji = get_role_emoji(bot, interaction.guild, "Outlaw")

        if hunter_sorted:
            hunter_text = "\n".join(f"{i+1}. <@{uid}> — {pts} pts" for i, (uid, pts) in enumerate(hunter_sorted))
        else:
            hunter_text = "No data yet."
        embed.add_field(name=f"{hunter_emoji} Hunter Leaderboard", value=hunter_text, inline=False)

        if outlaw_sorted:
            outlaw_text = "\n".join(f"{i+1}. <@{uid}> — {pts} pts" for i, (uid, pts) in enumerate(outlaw_sorted))
        else:
            outlaw_text = "No data yet."
        embed.add_field(name=f"{outlaw_emoji} Outlaw Leaderboard", value=outlaw_text, inline=False)

        await interaction.response.send_message(embed=embed)
