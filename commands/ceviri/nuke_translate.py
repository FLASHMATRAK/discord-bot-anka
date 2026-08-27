import discord
from discord import app_commands
from deep_translator import GoogleTranslator


def setup(bot):
    @bot.tree.command(name="nuke-translate", description="It cleans up the channel, changes its name to English, and translates the messages.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nuke_translate(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        old_channel = interaction.channel
        guild = interaction.guild
        category = old_channel.category
        position = old_channel.position
        overwrites = old_channel.overwrites

        messages = []
        async for msg in old_channel.history(limit=10, oldest_first=True):
            if not msg.author.bot and msg.content:
                messages.append((msg.author.display_name, msg.content))

        try:
            translated_name = GoogleTranslator(source='auto', target='en').translate(old_channel.name)
            new_channel_name = translated_name.lower().replace(" ", "-")
        except Exception:
            new_channel_name = f"{old_channel.name}-en"

        await old_channel.delete()

        new_channel = await guild.create_text_channel(
            name=new_channel_name,
            category=category,
            position=position,
            overwrites=overwrites
        )

        await new_channel.send(f"🔄 **The channel was reset and its name was translated into English:** `#{new_channel_name}`\n--- Archive Messages ---")

        for author, content in messages:
            try:
                translated_content = GoogleTranslator(source='auto', target='en').translate(content)
                await new_channel.send(f"**{author}:** {translated_content}")
            except Exception:
                await new_channel.send(f"**{author}:** {content} *(Could not be translated)*")
