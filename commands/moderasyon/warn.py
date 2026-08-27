import datetime
import discord
from discord import app_commands
from utils.helpers import log_action
from utils import state


def setup(bot):
    @bot.tree.command(name="warn", description="Warns a user.")
    @app_commands.describe(member="Uyarılacak kullanıcı", reason="Sebep")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Belirtilmedi"):
        state.warnings[member.id].append({
            "word": reason,
            "date": datetime.datetime.now().strftime("%d/%m/%y")
        })
        count = len(state.warnings[member.id])
        await log_action(bot, interaction, member, "Warn", reason)
        await interaction.response.send_message(f"⚠️ **{member.display_name}** was warned ({count} total). Reason: {reason}")
