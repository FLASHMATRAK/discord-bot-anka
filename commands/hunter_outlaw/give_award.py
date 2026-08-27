import datetime
import discord
from discord import app_commands
from utils import state
from utils.helpers import get_role_type, check_and_assign_rank


def setup(bot):
    @bot.tree.command(name="give-award", description="Transfers the loser's point (converted by role) to the winner.")
    @app_commands.describe(lose="Kaybeden kullanıcı", winner="Kazanan kullanıcı", amount="Aktarılacak puan miktarı (varsayılan 1)")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def give_award(interaction: discord.Interaction, lose: discord.Member, winner: discord.Member, amount: int = 1):
        loser_role = get_role_type(bot, lose)
        winner_role = get_role_type(bot, winner)

        if loser_role is None or winner_role is None:
            await interaction.response.send_message("❌ Both users must have either the Hunter or the Outlaw role.", ephemeral=True)
            return

        if loser_role == winner_role:
            await interaction.response.send_message("❌ The loser and winner cannot share the same role (one must be Hunter, the other Outlaw).", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ The amount must be a positive number.", ephemeral=True)
            return

        if loser_role == "Hunter":
            state.hunter_points[lose.id] = max(0, state.hunter_points[lose.id] - amount)
            state.outlaw_points[winner.id] += amount
            conversion_text = f"{amount} Hunter Point → {amount} Outlaw Point"
        else:
            state.outlaw_points[lose.id] = max(0, state.outlaw_points[lose.id] - amount)
            state.hunter_points[winner.id] += amount
            conversion_text = f"{amount} Outlaw Point → {amount} Hunter Point"

        match_date = datetime.datetime.now().strftime("%d/%m/%y")
        state.match_history[winner.id].append({"vs": lose.id, "result": "win", "date": match_date})
        state.match_history[lose.id].append({"vs": winner.id, "result": "loss", "date": match_date})

        winner_new_points = state.hunter_points[winner.id] if winner_role == "Hunter" else state.outlaw_points[winner.id]
        await check_and_assign_rank(bot, winner, winner_role, winner_new_points)

        embed = discord.Embed(title="🏆 Point Transfer", color=discord.Color.gold())
        embed.add_field(name="Loser", value=f"{lose.mention} ({loser_role})", inline=True)
        embed.add_field(name="Winner", value=f"{winner.mention} ({winner_role})", inline=True)
        embed.add_field(name="Conversion", value=conversion_text, inline=False)
        embed.set_footer(text=f"Approved by: {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)
