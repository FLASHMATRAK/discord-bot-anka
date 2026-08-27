import os
import sys
import time
import logging
import importlib.util
import traceback

import discord
from discord.ext import commands

from utils.config import load_config
from utils import state


# ============ LOGLAMA ============
# Artık hatalar sadece konsola değil, bot.log dosyasına da yazılıyor.
# Bot çöktüğünde/kapandığında "neden kapandığını" bu dosyadan görebilirsin.
LOG_FILE = "bot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("bot")


class MyBot(commands.Bot):
    def __init__(self, config: dict):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True  # /hoşgeldin mesajı (on_member_join) için gerekli
        super().__init__(command_prefix="!", intents=intents)

        self.config = config
        # Farklı komut dosyalarının on_message / on_member_join olaylarına
        # bağlanabilmesi için ortak bir "dinleyici listesi" sistemi.
        self.message_handlers = []       # [async def handler(message): ...]
        self.member_join_handlers = []   # [async def handler(member): ...]

        # Slash komutlarında (app_commands) yakalanmamış hataları yakala.
        # Bu olmadan bir slash komuttaki hata sadece o etkileşimi "başarısız" gösterir,
        # ama loglanmadığı için nedenini asla bilemezsin.
        self.tree.on_error = self.on_app_command_error

    async def on_ready(self):
        logger.info(f"🤖 {self.user.name} giriş yaptı!")
        try:
            synced = await self.tree.sync()
            logger.info(f"🔄 {len(synced)} slash komut senkronize edildi!")
        except Exception:
            logger.exception("❌ Komutlar senkronize edilemedi")

    async def on_message(self, message: discord.Message):
        # Kayıtlı tüm mesaj dinleyicilerini (küfür/spam filtresi, wanted sistemi vb.) sırayla çalıştırıyoruz.
        # Her handler kendi try/except'i içinde çalışır: biri patlarsa diğerleri ve bot etkilenmez.
        for handler in self.message_handlers:
            try:
                await handler(message)
            except Exception:
                logger.exception(f"⚠️ message handler hatası ({getattr(handler, '__module__', '?')})")

        if message.author.bot:
            return

        try:
            await self.process_commands(message)
        except Exception:
            logger.exception("⚠️ process_commands hatası")

    async def on_member_join(self, member: discord.Member):
        for handler in self.member_join_handlers:
            try:
                await handler(member)
            except Exception:
                logger.exception(f"⚠️ member_join handler hatası ({getattr(handler, '__module__', '?')})")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """! ile başlayan prefix komutlarında oluşan hataları yakalar (botu çökertmez)."""
        if isinstance(error, commands.CommandNotFound):
            return  # olmayan komut yazılırsa sessizce geç
        logger.exception(f"⚠️ Komut hatası ({ctx.command}): {error}", exc_info=error)
        try:
            await ctx.send("⚠️ Komut çalıştırılırken bir hata oluştu, bu kayıt altına alındı.")
        except Exception:
            pass

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """/ ile başlayan slash komutlarında oluşan hataları yakalar (botu çökertmez)."""
        logger.exception(f"⚠️ Slash komut hatası ({interaction.command}): {error}", exc_info=error)
        message = "⚠️ Komut çalıştırılırken bir hata oluştu, bu kayıt altına alındı."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except Exception:
            pass

    async def on_error(self, event_method: str, *args, **kwargs):
        """discord.py olaylarının (on_ready, on_message vb. üzerindeki asıl kod) herhangi birinde
        beklenmedik bir hata olursa, discord.py'nin varsayılan davranışı sadece traceback basmaktır.
        Burada onu ayrıca dosyaya da logluyoruz ki bot 'sessizce' garip davranmasın."""
        logger.error(f"⚠️ Beklenmeyen olay hatası ({event_method})\n{traceback.format_exc()}")


def load_commands(bot: MyBot, base_dir: str = "commands"):
    """commands/ klasörü altındaki tüm .py dosyalarını bulup setup(bot) fonksiyonlarını çalıştırır.

    Önemli: Tek bir komut dosyasında hata (import hatası, syntax hatası vb.) olursa
    artık TÜM BOT açılışta çökmüyor — sadece o dosya atlanıp diğerleri yükleniyor."""
    loaded = 0
    failed = 0
    for root, _, files in os.walk(base_dir):
        for filename in sorted(files):
            if not filename.endswith(".py") or filename.startswith("__"):
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, ".")
            module_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")

            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "setup"):
                    module.setup(bot)
                    loaded += 1
                    logger.info(f"✅ Yüklendi: {filepath}")
                else:
                    logger.warning(f"⚠️ 'setup' fonksiyonu bulunamadı, atlandı: {filepath}")
            except Exception:
                failed += 1
                logger.exception(f"❌ Komut dosyası yüklenirken hata, atlanıyor: {filepath}")

    logger.info(f"📦 Toplam {loaded} komut dosyası yüklendi, {failed} dosya atlandı.")


def run_bot():
    """Botu çalıştırır; beklenmeyen bir çökme olursa (internet kopması, discord tarafı sorun vb.)
    bekleyip otomatik olarak yeniden başlatır. Geçersiz token gibi düzelmeyecek hatalarda
    sonsuz döngüye girmemek için yeniden denemeden çıkar."""
    try:
        config = load_config("config.json")
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)

    # role_icons'u config.json'dan bellek durumuna kopyalıyoruz
    # (bot çalışırken /set-role-icon ile değiştirilebilecek)
    state.role_icons.update(config.get("role_icons", {}))

    max_retries = 10
    retry_delay = 5  # saniye, her denemede artacak (backoff)
    attempt = 0

    while attempt < max_retries:
        bot = MyBot(config)
        load_commands(bot, "commands")

        try:
            bot.run(config["token"], log_handler=None)
            # bot.run() normal şekilde (örn. kapatma komutu) döndüyse tekrar başlatma
            logger.info("Bot normal şekilde durduruldu, yeniden başlatılmıyor.")
            break
        except discord.LoginFailure:
            logger.critical("❌ Geçersiz token! config.json içindeki 'token' değerini kontrol et. Bot durduruluyor.")
            sys.exit(1)
        except discord.PrivilegedIntentsRequired:
            logger.critical(
                "❌ Gerekli 'Privileged Intents' (Members / Message Content) Discord Developer "
                "Portal'da açık değil. Bot ayarlarından açıp tekrar dene. Bot durduruluyor."
            )
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Bot manuel olarak durduruldu (Ctrl+C).")
            break
        except Exception:
            attempt += 1
            logger.exception(
                f"💥 Bot beklenmedik şekilde kapandı (deneme {attempt}/{max_retries}). "
                f"{retry_delay} saniye sonra yeniden başlatılacak."
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 300)  # en fazla 5 dakikaya kadar artan bekleme
    else:
        logger.critical("❌ Maksimum yeniden başlatma denemesine ulaşıldı. Bot durduruluyor, sunucu loglarını kontrol et.")
        sys.exit(1)


if __name__ == "__main__":
    run_bot()
