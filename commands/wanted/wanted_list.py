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

        wanted_members = []

        for member in outlaw_role.members:
            data = state.wanted_data.get(member.id)

            if not data:
                continue

            bounty = int(data.get("bounty", 0))

            if bounty <= 0:
                continue

            wanted_members.append((member, bounty))

        if not wanted_members:
            await interaction.response.send_message(
                "✅ No one is currently wanted."
            )
            return

        embed = discord.Embed(
            title="🚨 Wanted List",
            color=discord.Color.dark_red()
        )

        for member, bounty in wanted_members:
            embed.add_field(
                name=member.display_name,
                value=(
                    f"<@{member.id}>\n"
                    f"Bounty: **{bounty:,} SP**"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed)