import datetime
import discord
from discord import app_commands
from utils.helpers import log_action


def setup(bot):
    @bot.tree.command(name="mute", description="Mutes a user for a given number of minutes.")
    @app_commands.describe(member="Susturulacak kullanıcı", minutes="Süre (dakika)", reason="Sebep")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Belirtilmedi"):
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await log_action(bot, interaction, member, f"Mute ({minutes} dk)", reason)
        await interaction.response.send_message(f"🔇 **{member.display_name}** has been muted for {minutes} minutes. Reason: {reason}")
