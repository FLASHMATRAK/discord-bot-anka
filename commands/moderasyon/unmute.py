import discord
from discord import app_commands


def setup(bot):
    @bot.tree.command(name="unmute", description="Unmutes a user.")
    @app_commands.describe(member="Susturması kaldırılacak kullanıcı")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(interaction: discord.Interaction, member: discord.Member):
        await member.timeout(None)
        await interaction.response.send_message(f"🔊 **{member.display_name}** has been unmuted.")
