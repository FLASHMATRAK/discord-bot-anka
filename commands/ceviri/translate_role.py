import discord
from discord import app_commands
from deep_translator import GoogleTranslator


def setup(bot):
    @bot.tree.command(name="translate-role", description="Translates a role's name (optionally applies the change).")
    @app_commands.describe(
        role="Çevrilecek rol",
        target_lang="Hedef dil kodu (örn: en, tr, de, fr)",
        apply="Çeviriyi role gerçekten uygulasın mı?"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def translate_role(
        interaction: discord.Interaction,
        role: discord.Role,
        target_lang: str = "en",
        apply: bool = False
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            translated_name = GoogleTranslator(source='auto', target=target_lang).translate(role.name)
        except Exception as e:
            await interaction.followup.send(f"❌ Translation failed: {e}", ephemeral=True)
            return

        if apply:
            try:
                await role.edit(name=translated_name)
                await interaction.followup.send(
                    f"✅ Role name updated: `{role.name}` → `{translated_name}`",
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ I don't have permission to edit this role (my role must be above it).",
                    ephemeral=True
                )
        else:
            await interaction.followup.send(
                f"🔤 Translation preview (not applied): `{role.name}` → `{translated_name}`\n"
                f"Run again with `apply: True` to apply it.",
                ephemeral=True
            )
