import discord
from discord import app_commands
from utils import state


def setup(bot):
    @bot.tree.command(name="reset-points", description="Resets ALL points on both Hunter and Outlaw leaderboards.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_points(interaction: discord.Interaction):
        state.hunter_points.clear()
        state.outlaw_points.clear()
        state.match_history.clear()
        await interaction.response.send_message("🧹 All Hunter and Outlaw points have been reset.")
