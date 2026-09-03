import json
import random
from pathlib import Path

import discord
from discord.ext import tasks


BASE_DIR = Path(__file__).resolve().parent.parent
SORULAR_DOSYASI = BASE_DIR / "sorular" / "sorular.json"

KANAL_ID = 123456789012345678
ROL_ID = 123456789012345678


def sorulari_yukle():
    with open(SORULAR_DOSYASI, "r", encoding="utf-8") as f:
        return json.load(f)


class SohbetEtkinligi(discord.Client):
    pass


async def setup(bot):
    async def etkinlik():
        try:
            sorular = sorulari_yukle()

            if not sorular:
                print("⚠️ Sohbet etkinliği: Soru listesi boş.")
                return

            soru = random.choice(sorular)
            kanal = bot.get_channel(KANAL_ID)

            if kanal is None:
                print(f"⚠️ Sohbet etkinliği kanalı bulunamadı: {KANAL_ID}")
                return

            embed = discord.Embed(
                title="💬 Sohbet Etkinliği",
                description=f"**Soru:** {soru['soru']}",
            )

            foto = soru.get("foto")

            if foto:
                foto_yolu = BASE_DIR / foto

                if foto_yolu.exists():
                    file = discord.File(foto_yolu, filename=foto_yolu.name)
                    embed.set_image(url=f"attachment://{foto_yolu.name}")

                    await kanal.send(
                        content=f"<@&{ROL_ID}>",
                        embed=embed,
                        file=file,
                    )
                    return

            await kanal.send(
                content=f"<@&{ROL_ID}>",
                embed=embed,
            )

        except Exception as e:
            print(f"❌ Sohbet etkinliği hatası: {e}")

    @tasks.loop(hours=2)
    async def zamanlayici():
        await etkinlik()

    @zamanlayici.before_loop
    async def baslamadan_once():
        await bot.wait_until_ready()

    zamanlayici.start()