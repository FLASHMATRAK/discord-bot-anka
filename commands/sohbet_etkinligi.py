import json
import random
import logging
from pathlib import Path

import discord
from discord.ext import tasks


logger = logging.getLogger("sohbet_etkinligi")

# Proje ana klasörü
BASE_DIR = Path(__file__).resolve().parent.parent

# Soruların bulunduğu JSON
SORULAR_DOSYASI = BASE_DIR / "sorular" / "sorular.json"

# BURAYI DEĞİŞTİR
KANAL_ID = 123456789012345678
ROL_ID = 123456789012345678


def sorulari_yukle():
    """Soruları JSON dosyasından yükler."""
    try:
        with open(SORULAR_DOSYASI, "r", encoding="utf-8") as dosya:
            sorular = json.load(dosya)

        if not isinstance(sorular, list):
            raise ValueError("sorular.json bir liste içermeli.")

        return sorular

    except FileNotFoundError:
        logger.error(f"❌ Soru dosyası bulunamadı: {SORULAR_DOSYASI}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ sorular.json bozuk: {e}")
    except Exception:
        logger.exception("❌ Sorular yüklenirken hata oluştu.")

    return []


async def soru_gonder(bot):
    """Rastgele bir sohbet sorusunu kanala gönderir."""

    kanal = bot.get_channel(KANAL_ID)

    if kanal is None:
        logger.error(f"❌ Kanal bulunamadı: {KANAL_ID}")
        return

    sorular = sorulari_yukle()

    if not sorular:
        logger.warning("⚠️ Gönderilecek soru bulunamadı.")
        return

    soru = random.choice(sorular)

    metin = soru.get("soru")
    foto = soru.get("foto")

    if not metin:
        logger.warning("⚠️ Seçilen soruda 'soru' alanı yok.")
        return

    embed = discord.Embed(
        title="💬 Sohbet Etkinliği",
        description=f"**Soru:** {metin}",
    )

    dosya = None

    # Fotoğraf varsa
    if foto:
        foto_yolu = BASE_DIR / foto

        if foto_yolu.exists():
            dosya = discord.File(
                foto_yolu,
                filename=foto_yolu.name
            )

            embed.set_image(
                url=f"attachment://{foto_yolu.name}"
            )
        else:
            logger.warning(
                f"⚠️ Fotoğraf bulunamadı: {foto_yolu}"
            )

    # Rolü etiketle
    icerik = f"<@&{ROL_ID}>"

    if dosya:
        await kanal.send(
            content=icerik,
            embed=embed,
            file=dosya,
        )
    else:
        await kanal.send(
            content=icerik,
            embed=embed,
        )

    logger.info(f"💬 Sohbet etkinliği gönderildi: {metin}")


@tasks.loop(hours=2)
async def sohbet_etkinligi_zamanlayici():
    """Her 2 saatte bir sohbet etkinliği gönderir."""

    bot = sohbet_etkinligi_zamanlayici.bot

    try:
        await soru_gonder(bot)
    except Exception:
        logger.exception(
            "❌ Sohbet etkinliği gönderilirken hata oluştu."
        )


@sohbet_etkinligi_zamanlayici.before_loop
async def zamanlayiciyi_beklet():
    bot = sohbet_etkinligi_zamanlayici.bot
    await bot.wait_until_ready()


async def setup(bot):
    """Bot tarafından otomatik olarak çağrılır."""

    sohbet_etkinligi_zamanlayici.bot = bot
    sohbet_etkinligi_zamanlayici.start()

    logger.info(
        "✅ Sohbet etkinliği zamanlayıcısı başlatıldı. "
        "Her 2 saatte bir çalışacak."
    )