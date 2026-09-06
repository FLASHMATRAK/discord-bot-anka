import discord
from utils import state


OUTLAW_ROLE_ID = 1533075067355926730


def setup(bot):
    @bot.tree.command(
        name="wanted-list",
        description="Shows all currently wanted users and their bounties."
    )
    async def wanted_list(interaction: discord.Interaction):
        outlaw_role = interaction.guild.get_role(OUTLAW_ROLE_ID)

        if outlaw_role is None:
            await interaction.response.send_message(
                "❌ Outlaw role could not be found.",
                ephemeral=True
            )
            return

        outlaw_members = outlaw_role.members

        if not outlaw_members:
            await interaction.response.send_message(
                "✅ No one is currently wanted."
            )
            return

        embed = discord.Embed(
            title="🚨 Wanted List",
            color=discord.Color.dark_red()
        )

        for member in outlaw_members:
            user_id = str(member.id)

            data = state.wanted_data.get(user_id, {})
            bounty = data.get("bounty", 0)

            embed.add_field(
                name=member.display_name,
                value=f"<@{member.id}>\nBounty: **{bounty} diamonds**",
                inline=False
            )

        await interaction.response.send_message(embed=embed)