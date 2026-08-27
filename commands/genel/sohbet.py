import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands
from openai import AsyncOpenAI, OpenAIError

from utils import state

logger = logging.getLogger("bot")

# Kullanıcı başına hafızada tutulacak son mesaj sayısı (user+assistant toplam).
MAX_HISTORY_MESSAGES = 20

# Discord tek mesajda 2000 karakterden fazlasına izin vermiyor, biraz pay bırakıyoruz.
DISCORD_MESSAGE_LIMIT = 1900

# Stream sırasında mesajı en fazla bu sıklıkta (saniye) düzenle;
# Discord'un mesaj düzenleme rate limitine takılmamak için.
EDIT_MIN_INTERVAL = 0.9


def _get_client(bot: commands.Bot) -> AsyncOpenAI:
    # NVIDIA NIM (integrate.api.nvidia.com), OpenAI ile uyumlu bir endpoint sunuyor;
    # sadece base_url ve kendi api key'ini veriyorsun, kod tarafı openai kütüphanesiyle aynı kalıyor.
    return AsyncOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=bot.config["nvidia_api_key"],
    )


def setup(bot: commands.Bot):
    @bot.tree.command(name="sohbet", description="Yapay zeka ile sohbet et (NVIDIA NIM)")
    @app_commands.describe(mesaj="Yapay zekaya söylemek istediğin şey")
    async def sohbet(interaction: discord.Interaction, mesaj: str):
        api_key = bot.config.get("nvidia_api_key", "")
        if not api_key or api_key.startswith("BURAYA_"):
            await interaction.response.send_message(
                "⚠️ NVIDIA API anahtarı henüz ayarlanmamış. `config.json` içindeki "
                "`nvidia_api_key` alanına kendi anahtarını yazman gerekiyor.",
                ephemeral=True,
            )
            return

        # Cevap birkaç saniye sürebilir, Discord'un 3 saniyelik timeout'una takılmamak için erteliyoruz.
        await interaction.response.defer(thinking=True)

        user_id = interaction.user.id
        history = state.ai_chat_history[user_id]
        history.append({"role": "user", "content": mesaj})

        system_prompt = bot.config.get(
            "nvidia_system_prompt",
            "Sen bu Discord sunucusunda kullanıcılara yardımcı olan, Türkçe konuşan samimi bir yapay zeka asistanısın.",
        )
        model = bot.config.get("nvidia_model", "meta/llama-3.1-8b-instruct")
        messages = [{"role": "system", "content": system_prompt}] + history[-MAX_HISTORY_MESSAGES:]

        # Nemotron gibi "reasoning" (düşünme) destekli modellerde, config'te bir bütçe
        # belirtilmişse thinking modunu açıyoruz. Belirtilmemişse hiç gönderilmiyor,
        # böylece bunu desteklemeyen modellerde soruna yol açmıyor.
        extra_body = None
        reasoning_budget = bot.config.get("nvidia_reasoning_budget", 0)
        if reasoning_budget:
            extra_body = {
                "chat_template_kwargs": {"enable_thinking": True},
                "reasoning_budget": reasoning_budget,
            }

        try:
            client = _get_client(bot)
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=bot.config.get("nvidia_temperature", 0.7),
                top_p=bot.config.get("nvidia_top_p", 0.95),
                max_tokens=bot.config.get("nvidia_max_tokens", 1024),
                extra_body=extra_body,
                stream=True,
            )
        except OpenAIError:
            logger.exception(f"NVIDIA API hatası (/sohbet, kullanıcı {user_id})")
            history.pop()
            await interaction.followup.send(
                "⚠️ Yapay zeka isteğinde bir hata oluştu (API anahtarı, model adı veya kota sorunu olabilir). "
                "Bu hata `bot.log` dosyasına kaydedildi."
            )
            return
        except Exception:
            logger.exception(f"/sohbet isteği başlatılırken beklenmeyen hata (kullanıcı {user_id})")
            history.pop()
            await interaction.followup.send("⚠️ Beklenmeyen bir hata oluştu, bu kayıt altına alındı.")
            return

        sent_message = await interaction.followup.send("⏳ Düşünüyor...")
        buffer = ""       # şu an ekranda gösterilen (henüz gönderilmemiş) parça
        full_answer = ""  # geçmişe kaydedilecek, baştan sona tüm cevap
        loop = asyncio.get_event_loop()
        last_edit = 0.0

        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # reasoning_content = modelin "düşünme" adımları. Discord'da göstermiyoruz
                # (çok uzun/gürültülü olabiliyor), sadece nihai content'i basıyoruz.
                piece = getattr(delta, "content", None)
                if not piece:
                    continue

                full_answer += piece
                buffer += piece

                # Mesaj Discord limitini aşarsa: mevcut mesajı sabitleyip yeni bir mesajla devam et.
                if len(buffer) > DISCORD_MESSAGE_LIMIT:
                    await sent_message.edit(content=buffer[:DISCORD_MESSAGE_LIMIT])
                    buffer = buffer[DISCORD_MESSAGE_LIMIT:]
                    sent_message = await interaction.followup.send("⏳ ...")

                now = loop.time()
                if now - last_edit >= EDIT_MIN_INTERVAL:
                    try:
                        await sent_message.edit(content=buffer + " ▌")
                    except discord.HTTPException:
                        pass  # ara ara rate limit yenirse görmezden gel, akış devam etsin
                    last_edit = now

            if not full_answer.strip():
                await sent_message.edit(content="⚠️ Yapay zekadan boş bir cevap geldi, tekrar dener misin?")
                history.pop()
                return

            await sent_message.edit(content=buffer)

        except OpenAIError:
            logger.exception(f"NVIDIA API stream hatası (/sohbet, kullanıcı {user_id})")
            history.pop()
            try:
                await sent_message.edit(content="⚠️ Yapay zeka isteği yarıda kesildi (API hatası). Bu kayıt altına alındı.")
            except discord.HTTPException:
                pass
            return
        except Exception:
            logger.exception(f"/sohbet stream işlenirken beklenmeyen hata (kullanıcı {user_id})")
            history.pop()
            try:
                await sent_message.edit(content="⚠️ Beklenmeyen bir hata oluştu, bu kayıt altına alındı.")
            except discord.HTTPException:
                pass
            return

        history.append({"role": "assistant", "content": full_answer})
        if len(history) > MAX_HISTORY_MESSAGES * 2:
            del history[: len(history) - MAX_HISTORY_MESSAGES]

    @bot.tree.command(name="sohbet-sifirla", description="Yapay zeka ile olan sohbet geçmişini sıfırlar")
    async def sohbet_sifirla(interaction: discord.Interaction):
        state.ai_chat_history.pop(interaction.user.id, None)
        await interaction.response.send_message("🔄 Sohbet geçmişin sıfırlandı.", ephemeral=True)
