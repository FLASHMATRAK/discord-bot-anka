import discord
from discord import app_commands
from utils import state


def setup(bot):
    @bot.tree.command(name="catch-wanted", description="Marks a wanted user as caught and clears their bounty.")
    @app_commands.describe(target="The wanted user who was caught", catcher="The user who caught them (optional)")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def catch_wanted(interaction: discord.Interaction, target: discord.Member, catcher: discord.Member = None):
        if target.id not in state.wanted_data:
            await interaction.response.send_message(f"❌ **{target.display_name}** is not currently wanted.", ephemeral=True)
            return

        bounty = state.wanted_data[target.id]["bounty"]
        del state.wanted_data[target.id]

        wanted_role = discord.utils.get(interaction.guild.roles, name=bot.config["wanted_role_name"])
        if wanted_role and wanted_role in target.roles:
            try:
                await target.remove_roles(wanted_role)
            except discord.Forbidden:
                pass

        result_text = f"✅ **{target.display_name}** has been caught! Bounty was **{bounty} diamonds**."
        if catcher:
            result_text += f"\nCaught by: {catcher.mention}"

        await interaction.response.send_message(result_text)
