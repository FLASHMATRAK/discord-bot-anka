import discord
from discord import app_commands
from utils import state
from utils.helpers import get_role_type, get_role_emoji


def setup(bot):
    @bot.tree.command(name="status", description="Shows a user's role and current points.")
    @app_commands.describe(user="Görüntülenecek kullanıcı")
    async def status(interaction: discord.Interaction, user: discord.Member):
        role_type = get_role_type(bot, user)

        if role_type is None:
            await interaction.response.send_message(f"❌ **{user.display_name}** has neither the Hunter nor the Outlaw role.", ephemeral=True)
            return

        points = state.hunter_points[user.id] if role_type == "Hunter" else state.outlaw_points[user.id]
        emoji = get_role_emoji(bot, interaction.guild, role_type)

        embed = discord.Embed(title=f"{emoji} {user.display_name} — Status", color=discord.Color.teal())
        embed.add_field(name="Role", value=role_type, inline=True)
        embed.add_field(name="Points", value=str(points), inline=True)

        await interaction.response.send_message(embed=embed)
