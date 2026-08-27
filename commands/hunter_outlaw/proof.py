import datetime
import discord
from discord import app_commands


def setup(bot):
    @bot.tree.command(name="proof", description="Submits match evidence for moderator review.")
    @app_commands.describe(photo="Kanıt fotoğrafı")
    async def proof(interaction: discord.Interaction, photo: discord.Attachment):
        if not photo.content_type or not photo.content_type.startswith("image/"):
            await interaction.response.send_message("❌ Please upload a valid image.", ephemeral=True)
            return

        proof_channel = interaction.guild.get_channel(bot.config["proof_channel_id"])
        if not proof_channel:
            await interaction.response.send_message("❌ Proof channel not found, please contact an admin.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📸 New Match Evidence",
            description=f"Submitted by: {interaction.user.mention}",
            color=discord.Color.blue()
        )
        embed.set_image(url=photo.url)
        embed.set_footer(text=datetime.datetime.now().strftime("%d.%m.%Y %H:%M"))

        await proof_channel.send(embed=embed)
        await interaction.response.send_message("✅ Your evidence has been submitted for moderator review.", ephemeral=True)
