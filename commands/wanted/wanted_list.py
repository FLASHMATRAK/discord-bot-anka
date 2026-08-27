import discord
from utils import state


def setup(bot):
    @bot.tree.command(name="wanted-list", description="Shows all currently wanted users and their bounties.")
    async def wanted_list(interaction: discord.Interaction):
        if not state.wanted_data:
            await interaction.response.send_message("✅ No one is currently wanted.")
            return

        embed = discord.Embed(title="🚨 Wanted List", color=discord.Color.dark_red())
        for user_id, data in state.wanted_data.items():
            embed.add_field(
                name=f"<@{user_id}>",
                value=f"Bounty: **{data['bounty']} diamonds**",
                inline=False
            )
        await interaction.response.send_message(embed=embed)
