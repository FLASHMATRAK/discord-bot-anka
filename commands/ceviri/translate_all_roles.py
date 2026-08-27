import discord
from discord import app_commands
from deep_translator import GoogleTranslator


def setup(bot):
    @bot.tree.command(name="translate-all-roles", description="Translates the names of all roles in the server.")
    @app_commands.describe(target_lang="Hedef dil kodu (örn: en, tr, de, fr)")
    @app_commands.checks.has_permissions(manage_roles=True, manage_guild=True)
    async def translate_all_roles(interaction: discord.Interaction, target_lang: str = "en"):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        results = []

        for role in guild.roles:
            if role.name == "@everyone" or role.managed:
                continue
            try:
                translated = GoogleTranslator(source='auto', target=target_lang).translate(role.name)
                await role.edit(name=translated)
                results.append(f"`{role.name}` → `{translated}`")
            except discord.Forbidden:
                results.append(f"`{role.name}` → ⚠️ no permission (bot role must be higher)")
            except Exception as e:
                results.append(f"`{role.name}` → ⚠️ error: {e}")

        summary = "\n".join(results) if results else "No roles to translate."
        await interaction.followup.send(f"🔄 **Role translation result:**\n{summary}", ephemeral=True)
