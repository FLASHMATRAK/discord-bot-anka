import discord
from discord import app_commands


class HuntRequestView(discord.ui.View):
    def __init__(self, requester: discord.Member, target: discord.Member):
        super().__init__(timeout=300)
        self.requester = requester
        self.target = target

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ This invitation isn't for you.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"✅ {self.target.mention} has **accepted** the hunt request from {self.requester.mention}!",
            view=self
        )

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ This invitation isn't for you.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"❌ {self.target.mention} has **declined** the hunt request from {self.requester.mention}.",
            view=self
        )


def setup(bot):
    @bot.tree.command(name="hunt-request", description="Sends a hunt invitation to a user.")
    @app_commands.describe(user="Davet edilecek kullanıcı")
    async def hunt_request(interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot invite yourself.", ephemeral=True)
            return

        view = HuntRequestView(requester=interaction.user, target=user)
        await interaction.response.send_message(
            f"🎯 {user.mention}, you have received a **hunt request** from {interaction.user.mention}! Do you accept?",
            view=view
        )
