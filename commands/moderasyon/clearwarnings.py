import discord
from discord import app_commands
from utils import state


def setup(bot):
    @bot.tree.command(name="clearwarnings", description="Clears all warnings of a user.")
    @app_commands.describe(member="Kullanıcı")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
        state.warnings[member.id] = []
        await interaction.response.send_message(f"🧹 **{member.display_name}**'s warnings have been cleared.")
