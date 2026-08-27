import discord
from discord import app_commands
from utils import state


def setup(bot):
    @bot.tree.command(name="criminal-record", description="Lists a user's full moderation history.")
    @app_commands.describe(member="Geçmişi görüntülenecek kullanıcı")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def criminal_record_command(interaction: discord.Interaction, member: discord.Member):
        history = state.rap_sheet.get(member.id, [])

        if not history:
            await interaction.response.send_message(f"✅ No records found for **{member.display_name}**, clean record.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📋 Criminal Record — {member.display_name}",
            description=f"Total {len(history)} record(s) found.",
            color=discord.Color.orange()
        )

        for i, entry in enumerate(history, 1):
            embed.add_field(
                name=f"{i}. {entry['type']} — {entry['date']}",
                value=f"Moderator: {entry['moderator']}\nReason: {entry['reason']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
