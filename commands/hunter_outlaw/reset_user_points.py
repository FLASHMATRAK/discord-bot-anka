import discord
from discord import app_commands
from utils import state
from utils.helpers import get_role_type


def setup(bot):
    @bot.tree.command(name="reset-user-points", description="Resets a single user's points.")
    @app_commands.describe(user="The user whose points will be reset")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def reset_user_points(interaction: discord.Interaction, user: discord.Member):
        role_type = get_role_type(bot, user)

        if role_type is None:
            await interaction.response.send_message(f"❌ **{user.display_name}** has no Hunter or Outlaw role.", ephemeral=True)
            return

        if role_type == "Hunter":
            state.hunter_points[user.id] = 0
        else:
            state.outlaw_points[user.id] = 0

        state.match_history[user.id] = []

        await interaction.response.send_message(f"🧹 **{user.display_name}**'s points have been reset to 0.")
