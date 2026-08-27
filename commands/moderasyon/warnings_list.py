import discord
from discord import app_commands
from utils import state


def setup(bot):
    @bot.tree.command(name="warnings", description="Lists a user's warnings.")
    @app_commands.describe(member="Kullanıcı")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def list_warnings(interaction: discord.Interaction, member: discord.Member):
        user_warnings = state.warnings.get(member.id, [])
        if not user_warnings:
            await interaction.response.send_message(f"✅ **{member.display_name}** has no warnings.")
            return

        lines = [f"{member.name}={w['word']}={w['date']}" for w in user_warnings]
        text = "\n".join(lines)
        await interaction.response.send_message(f"⚠️ **{member.display_name}** warnings:\n```\n{text}\n```")
