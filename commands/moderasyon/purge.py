import discord
from discord import app_commands


def setup(bot):
    @bot.tree.command(name="purge", description="Deletes a number of messages.")
    @app_commands.describe(amount="Silinecek mesaj sayısı (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 {len(deleted)} messages deleted.", ephemeral=True)
