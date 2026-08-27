import discord
from discord import app_commands
from utils import state


def setup(bot):
    @bot.tree.command(name="history", description="Shows a user's match history.")
    @app_commands.describe(user="The user whose history will be shown")
    async def history_command(interaction: discord.Interaction, user: discord.Member):
        user_history = state.match_history.get(user.id, [])

        if not user_history:
            await interaction.response.send_message(f"📭 **{user.display_name}** has no match history yet.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📜 Match History — {user.display_name}",
            color=discord.Color.dark_teal()
        )

        for i, entry in enumerate(user_history[-15:], 1):
            result_emoji = "✅" if entry["result"] == "win" else "❌"
            embed.add_field(
                name=f"{i}. {result_emoji} {entry['result'].upper()} vs <@{entry['vs']}>",
                value=entry["date"],
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
