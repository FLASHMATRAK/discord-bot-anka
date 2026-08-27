import discord
from discord import app_commands
from utils.helpers import log_action


def setup(bot):
    @bot.tree.command(name="kick", description="Kicks a user from the server.")
    @app_commands.describe(member="Atılacak kullanıcı", reason="Sebep")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Belirtilmedi"):
        await member.kick(reason=reason)
        await log_action(bot, interaction, member, "Kick", reason)
        await interaction.response.send_message(f"👢 **{member.display_name}** was kicked from the server. Reason: {reason}")
