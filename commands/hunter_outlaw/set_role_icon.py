import re
import discord
from discord import app_commands
from utils import state


def setup(bot):
    @bot.tree.command(name="set-role-icon", description="Sets the server emoji used for the Hunter or Outlaw role.")
    @app_commands.describe(role_type="Hunter mı Outlaw mı", emoji="Sunucudaki custom emoji")
    @app_commands.choices(role_type=[
        app_commands.Choice(name="Hunter", value="Hunter"),
        app_commands.Choice(name="Outlaw", value="Outlaw"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_role_icon(interaction: discord.Interaction, role_type: app_commands.Choice[str], emoji: str):
        match = re.match(r"<a?:(\w+):(\d+)>", emoji)
        if not match:
            await interaction.response.send_message("❌ Please pick a valid custom emoji from this server (use the emoji picker).", ephemeral=True)
            return

        emoji_name = match.group(1)
        found = discord.utils.get(interaction.guild.emojis, name=emoji_name)
        if not found:
            await interaction.response.send_message("❌ This emoji was not found in this server.", ephemeral=True)
            return

        state.role_icons[role_type.value] = emoji_name
        await interaction.response.send_message(f"✅ **{role_type.value}** icon has been set to {found}.")
