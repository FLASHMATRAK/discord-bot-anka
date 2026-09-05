import logging

import discord

logger = logging.getLogger("partners")


# =========================================================
# AYARLAR
# =========================================================

PARTNERS_KANAL_ID = 123456789012345678  # our partners kanal ID


# =========================================================
# UYARI
# =========================================================

UYARI_BASLIK = "⚠️ Partner Sunucuları Hakkında"

UYARI_METNI = (
    "Bu kanalda yer alan sunucular ile ANKAtuber arasında herhangi bir "
    "güven veya garanti ilişkisi yoktur. Amaç yalnızca toplulukların "
    "karşılıklı tanıtımı ve yeni üyeler kazanmaktır. Yaşanabilecek "
    "dolandırıcılık, ödül veya benzeri anlaşmazlıklardan ANKAtuber "
    "sorumlu değildir."
)


def uyari_embed():
    return discord.Embed(
        title=UYARI_BASLIK,
        description=UYARI_METNI,
        color=discord.Color.orange()
    )


# =========================================================
# UYARI MESAJINI BUL
# =========================================================

async def uyariyi_bul(kanal):
    async for mesaj in kanal.history(limit=100):
        if (
            mesaj.author == bot.user
            and mesaj.embeds
            and mesaj.embeds[0].title == UYARI_BASLIK
        ):
            return mesaj

    return None


# =========================================================
# UYARIYI EN ALTA TAŞI
# =========================================================

async def uyariyi_en_alta_tasi(kanal):
    try:
        mesaj = await uyariyi_bul(kanal)

        if mesaj is not None:
            await mesaj.delete()

        await kanal.send(embed=uyari_embed())

        logger.info("✅ Partner uyarısı en alta taşındı.")

    except discord.Forbidden:
        logger.error(
            "❌ Partners kanalında mesaj silme/gönderme yetkim yok."
        )

    except Exception:
        logger.exception(
            "❌ Partner uyarısı taşınırken hata oluştu."
        )


# =========================================================
# MESAJ DİNLEYİCİSİ
# =========================================================

async def message_handler(message):
    if message.channel.id != PARTNERS_KANAL_ID:
        return

    # Kendi uyarımızı tekrar alta taşımaya çalışma
    if message.author == bot.user:
        return

    await uyariyi_en_alta_tasi(message.channel)


# =========================================================
# BAŞLANGIÇ
# =========================================================

bot = None


def setup(bot_instance):
    global bot
    bot = bot_instance

    bot.message_handlers.append(message_handler)

    async def baslat():
        await bot.wait_until_ready()

        kanal = bot.get_channel(PARTNERS_KANAL_ID)

        if kanal is None:
            logger.error(
                "❌ Partners kanalı bulunamadı: %s",
                PARTNERS_KANAL_ID
            )
            return

        mesaj = await uyariyi_bul(kanal)

        if mesaj is None:
            await kanal.send(embed=uyari_embed())
            logger.info("✅ Partner uyarısı oluşturuldu.")
        else:
            logger.info("✅ Partner uyarısı zaten mevcut.")

    bot.loop.create_task(baslat())

    logger.info("✅ Partners sistemi yüklendi.")