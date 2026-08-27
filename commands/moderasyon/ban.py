import discord
from discord import app_commands
from utils.helpers import log_action


def setup(bot):
    @bot.tree.command(name="ban", description="Bans a user from the server.")
    @app_commands.describe(member="Yasaklanacak kullanıcı", reason="Sebep")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Belirtilmedi"):
        await member.ban(reason=reason)
        await log_action(bot, interaction, member, "Ban", reason)
        await interaction.response.send_message(f"🔨 **{member.display_name}** was banned from the server. Reason: {reason}")
