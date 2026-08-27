import discord
from discord import app_commands


def setup(bot):
    @bot.tree.command(name="lock", description="Locks the channel (no one can send messages).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(interaction: discord.Interaction):
        channel = interaction.channel
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 Channel locked.")
