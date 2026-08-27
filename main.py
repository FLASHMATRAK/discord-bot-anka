import os
import sys
import time
import logging
import inspect
import importlib.util
import traceback

import discord
from discord.ext import commands

from utils.config import load_config
from utils import state


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
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

        self.config = config
        self.message_handlers = []
        self.member_join_handlers = []

        self.tree.on_error = self.on_app_command_error

    async def setup_hook(self):
        # discord.py, bağlanmadan hemen önce bunu kendi (doğru) event loop'unda otomatik çağırıyor.
        # Komut dosyalarını burada yüklemek, ayrı bir loop açmaktan çok daha güvenli.
        await load_commands(self, "commands")

    async def on_ready(self):
        logger.info(f"🤖 {self.user.name} giriş yaptı!")
        try:
            synced = await self.tree.sync()
            logger.info(f"🔄 {len(synced)} slash komut senkronize edildi!")
        except Exception:
            logger.exception("❌ Komutlar senkronize edilemedi")

    async def on_message(self, message: discord.Message):
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
        if isinstance(error, commands.CommandNotFound):
            return
        logger.exception(f"⚠️ Komut hatası ({ctx.command}): {error}", exc_info=error)
        try:
            await ctx.send("⚠️ Komut çalıştırılırken bir hata oluştu, bu kayıt altına alındı.")
        except Exception:
            pass

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
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
        logger.error(f"⚠️ Beklenmeyen olay hatası ({event_method})\n{traceback.format_exc()}")


async def load_commands(bot: MyBot, base_dir: str = "commands"):
    """commands/ klasörü altındaki tüm .py dosyalarını bulup setup(bot) fonksiyonlarını çalıştırır.
    setup(bot) ister normal (sync) bir fonksiyon olsun ister 'async def setup(bot):' olsun, ikisini de destekler."""
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
                    result = module.setup(bot)
                    if inspect.isawaitable(result):
                        await result
                    loaded += 1
                    logger.info(f"✅ Yüklendi: {filepath}")
                else:
                    logger.warning(f"⚠️ 'setup' fonksiyonu bulunamadı, atlandı: {filepath}")
            except Exception:
                failed += 1
                logger.exception(f"❌ Komut dosyası yüklenirken hata, atlanıyor: {filepath}")

    logger.info(f"📦 Toplam {loaded} komut dosyası yüklendi, {failed} dosya atlandı.")


def run_bot():
    """Botu çalıştırır; beklenmeyen bir çökme olursa bekleyip otomatik olarak yeniden başlatır."""
    try:
        config = load_config("config.json")
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)

    state.role_icons.update(config.get("role_icons", {}))

    max_retries = 10
    retry_delay = 5
    attempt = 0

    while attempt < max_retries:
        bot = MyBot(config)

        try:
            bot.run(config["token"], log_handler=None)
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
            retry_delay = min(retry_delay * 2, 300)
    else:
        logger.critical("❌ Maksimum yeniden başlatma denemesine ulaşıldı. Bot durduruluyor, sunucu loglarını kontrol et.")
        sys.exit(1)


if __name__ == "__main__":
    run_bot()