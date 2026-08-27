import discord
from discord import app_commands


def setup(bot):
    @bot.tree.command(name="unlock", description="Unlocks the channel.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(interaction: discord.Interaction):
        channel = interaction.channel
        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Channel unlocked.")
