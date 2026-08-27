import time
import datetime
import discord
from utils import state


def setup(bot):
    """Otomatik küfür ve spam filtresi. Komut değil, mesaj dinleyicisi olarak kaydedilir."""

    async def handle_message(message: discord.Message):
        if message.author.bot:
            return

        bad_words = bot.config["bad_words"]
        content_lower = message.content.lower()
        matched_word = next((w for w in bad_words if w.lower() in content_lower), None)

        if matched_word:
            state.warnings[message.author.id].append({
                "word": matched_word,
                "date": datetime.datetime.now().strftime("%d/%m/%y")
            })
            await message.delete()
            try:
                await message.channel.send(
                    f"🚫 {message.author.mention}, your message was removed for inappropriate content.",
                    delete_after=5
                )
            except discord.Forbidden:
                pass
            return

        spam_limit = bot.config["spam_limit"]
        spam_window = bot.config["spam_window"]

        now = time.time()
        user_id = message.author.id
        state.spam_tracker[user_id] = [t for t in state.spam_tracker[user_id] if now - t < spam_window]
        state.spam_tracker[user_id].append(now)

        if len(state.spam_tracker[user_id]) > spam_limit:
            try:
                await message.channel.purge(limit=spam_limit + 1, check=lambda m: m.author.id == user_id)
            except discord.Forbidden:
                pass
            await message.channel.send(
                f"🚫 {message.author.mention}, spam detected! Your messages have been deleted.",
                delete_after=5
            )
            state.spam_tracker[user_id] = []

    bot.message_handlers.append(handle_message)
