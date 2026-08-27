import discord
from discord import app_commands
from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from utils import state

# Sohbet geçmişinde kullanıcı başına en fazla kaç mesaj (soru+cevap) tutulacağı.
# Çok büyürse hem NVIDIA'ya giden istek maliyeti artar hem cevap yavaşlar.
MAX_HISTORY_MESSAGES = 20

# Discord tek mesajda 2000 karakterden fazlasına izin vermiyor, cevabı bölmek için.
DISCORD_MESSAGE_LIMIT = 2000


def _get_client(bot) -> AsyncOpenAI:
    """NVIDIA NIM (integrate.api.nvidia.com), OpenAI ile uyumlu bir API sunuyor,
    bu yüzden openai kütüphanesini sadece base_url'i değiştirerek kullanabiliyoruz."""
    return AsyncOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=bot.config["nvidia_api_key"],
    )


def _chunk_text(text: str, limit: int = DISCORD_MESSAGE_LIMIT):
    """Uzun cevapları Discord'un 2000 karakter sınırına göre parçalara ayırır."""
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:]
    if text:
        chunks.append(text)
    return chunks


async def _ask_ai(bot, user_id: int, mesaj: str):
    """/sohbet komutu ve '!' ile başlayan mesajlar tarafından ortak kullanılan asıl AI çağrısı.
    Başarılı olursa (True, cevap_metni) döner, hata olursa (False, kullanıcıya gösterilecek_hata_mesajı) döner."""
    history = state.ai_chat_history[user_id]
    history.append({"role": "user", "content": mesaj})

    system_prompt = bot.config.get(
        "nvidia_system_prompt",
        "Sen bu Discord sunucusunda kullanıcılara yardımcı olan, Türkçe konuşan samimi bir yapay zeka asistanısın.",
    )
    model = bot.config.get("nvidia_model", "meta/llama-3.1-8b-instruct")
    messages = [{"role": "system", "content": system_prompt}] + history[-MAX_HISTORY_MESSAGES:]

    try:
        client = _get_client(bot)
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content
    except RateLimitError:
        history.pop()
        return False, "⚠️ Şu anda çok fazla istek var, biraz sonra tekrar dener misin?"
    except APIConnectionError:
        history.pop()
        return False, "⚠️ NVIDIA API'ye bağlanılamadı, internet bağlantısı ya da API adresini kontrol et."
    except APIError as e:
        history.pop()
        print(f"⚠️ NVIDIA API hatası: {e}")
        return False, "⚠️ Yapay zekadan cevap alınamadı (API hatası). Bu kayıt altına alındı."
    except Exception as e:
        history.pop()
        print(f"⚠️ /sohbet beklenmeyen hata: {e}")
        return False, "⚠️ Beklenmeyen bir hata oluştu, bu kayıt altına alındı."

    history.append({"role": "assistant", "content": reply})
    # Geçmişi limitin biraz üstünde tutup budayalım (bellek şişmesin).
    if len(history) > MAX_HISTORY_MESSAGES * 2:
        del history[: len(history) - MAX_HISTORY_MESSAGES]

    return True, reply


def setup(bot):
    @bot.tree.command(name="sohbet", description="Yapay zeka ile sohbet et (NVIDIA NIM).")
    @app_commands.describe(mesaj="Yapay zekaya söylemek istediğin şey")
    async def sohbet(interaction: discord.Interaction, mesaj: str):
        if not bot.config.get("nvidia_api_key"):
            await interaction.response.send_message(
                "⚠️ Bu özellik henüz ayarlanmamış. `config.json` içine `nvidia_api_key` eklenmesi gerekiyor.",
                ephemeral=True,
            )
            return

        # API isteği birkaç saniye sürebilir, Discord'un "3 saniyede cevap ver" limitine takılmamak için erken defer ediyoruz.
        await interaction.response.defer(thinking=True)

        ok, result = await _ask_ai(bot, interaction.user.id, mesaj)
        if not ok:
            await interaction.followup.send(result)
            return

        chunks = _chunk_text(result)
        await interaction.followup.send(chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

    @bot.tree.command(name="sohbet-sifirla", description="Yapay zeka ile olan sohbet geçmişini sıfırlar.")
    async def sohbet_sifirla(interaction: discord.Interaction):
        state.ai_chat_history.pop(interaction.user.id, None)
        await interaction.response.send_message("🧹 Sohbet geçmişin sıfırlandı.", ephemeral=True)

    # --- "!" ile başlayan normal mesajlarla da sohbet edebilme ---
    # Örn: "!merhaba nasılsın" yazınca /sohbet komutuna gerek kalmadan AI cevap verir.
    async def ai_prefix_handler(message: discord.Message):
        if message.author.bot:
            return
        if not message.content.startswith("!"):
            return

        mesaj = message.content[1:].strip()
        if not mesaj:
            return

        # "!" ile başlayan gerçek bir bot komutuysa (örn. ileride eklenirse), ona karışma.
        first_word = mesaj.split(maxsplit=1)[0].lower()
        if bot.get_command(first_word) is not None:
            return

        if not bot.config.get("nvidia_api_key"):
            return  # API key yoksa sessizce geç, her "!" mesajında uyarı basıp spam yapmayalım

        async with message.channel.typing():
            ok, result = await _ask_ai(bot, message.author.id, mesaj)

        if not ok:
            await message.reply(result, mention_author=False)
            return

        chunks = _chunk_text(result)
        await message.reply(chunks[0], mention_author=False)
        for chunk in chunks[1:]:
            await message.channel.send(chunk)

    bot.message_handlers.append(ai_prefix_handler)
