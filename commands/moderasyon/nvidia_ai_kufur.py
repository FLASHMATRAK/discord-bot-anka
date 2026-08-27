import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI

# ========== NVIDIA API KONFİGÜRASYONU ==========
NVIDIA_API_KEY = "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"  # 🔴 Buraya kendi anahtarını yaz

# ========== LOG KANALI ID ==========
LOG_KANAL_ID = 1540028117572132934  # 🔴 Logların gideceği kanal ID'si (Sayı olarak!)

# ========== KÜFÜR ÖĞRENME KANALI ID ==========
KUFUR_OGRENME_KANAL_ID = 1540035231808225300  # 🔴 Botun dinleyeceği kanal ID'si (Sayı olarak!)

# NVIDIA OpenAI Client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# Dosya Yolu
KUFUR_LISTESI_DOSYASI = "nvidia_kufur_listesi.json"


def kufur_listesini_yukle():
    if not os.path.exists(KUFUR_LISTESI_DOSYASI):
        with open(KUFUR_LISTESI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)
        return []
    with open(KUFUR_LISTESI_DOSYASI, "r", encoding="utf-8") as f:
        return json.load(f)


def kufur_listesini_kaydet(liste):
    with open(KUFUR_LISTESI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)


async def nvidia_ile_kufur_mu_kontrol_et(mesaj_icerigi: str) -> tuple:
    prompt = f"""
    Sen bir Discord moderasyon botusun. Aşağıdaki mesajı analiz et.
    Eğer mesaj küfür, hakaret, argo veya saldırgan bir dil içeriyorsa:
    - İlk satıra "EVET" yaz
    - İkinci satıra tespit ettiğin kelimeyi yaz (tek kelime)
    Eğer temizse sadece "HAYIR" yaz.
    Mesaj: "{mesaj_icerigi}"
    """
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": "Sen bir moderasyon asistanısın."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        cevap = response.choices[0].message.content.strip()
        print(f"🤖 AI Cevabı: {cevap}")
        
        if cevap.upper().startswith("EVET"):
            satirlar = cevap.split("\n")
            if len(satirlar) > 1:
                return True, satirlar[1].strip().lower()
            return True, mesaj_icerigi
        return False, None
    except Exception as e:
        print(f"⚠️ NVIDIA API hatası: {e}")
        return False, None


class NVIDIAAIKufurFiltresi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kufur_listesi = kufur_listesini_yukle()
        print(f"📚 NVIDIA AI Küfür listesi yüklendi: {len(self.kufur_listesi)} kelime")

    async def log_kanalina_gonder(self, embed: discord.Embed):
        try:
            kanal = self.bot.get_channel(LOG_KANAL_ID)
            if kanal:
                await kanal.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Log kanalına gönderilemedi: {e}")

    # ========== MESAJ DINLEYİCİ (message_handlers SİSTEMİ İÇİN) ==========
    async def on_learn_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Sadece belirlenen kanaldan öğren
        if message.channel.id != KUFUR_OGRENME_KANAL_ID:
            return

        icerik = message.content.lower()

        # 1. Hızlı Liste Kontrolü
        for kelime in self.kufur_listesi:
            if kelime in icerik:
                await self._mesaj_engelle(message, kelime, "Listeden")
                return

        # 2. AI Analizi
        if len(icerik) > 2:
            kufur_mu, bulunan_kelime = await nvidia_ile_kufur_mu_kontrol_et(icerik)
            if kufur_mu and bulunan_kelime:
                yeni = False
                if bulunan_kelime not in self.kufur_listesi:
                    self.kufur_listesi.append(bulunan_kelime)
                    kufur_listesini_kaydet(self.kufur_listesi)
                    yeni = True
                    print(f"🧠 YENİ KELİME ÖĞRENDİ: {bulunan_kelime}")
                
                await self._mesaj_engelle(message, bulunan_kelime, "AI" if not yeni else "Yeni Öğrenme")

    async def _mesaj_engelle(self, message: discord.Message, kelime: str, tip: str):
        """Mesajı siler, loglar ve uyarı gönderir."""
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        renk = discord.Color.orange() if tip == "Yeni Öğrenme" else discord.Color.red()
        baslik = "🧠 AI Yeni Küfür Öğrendi!" if tip == "Yeni Öğrenme" else f"🚫 Küfür Engellendi ({tip})"

        embed = discord.Embed(
            title=baslik,
            description=f"**Kullanıcı:** {message.author.mention}\n"
                        f"**Kanal:** {message.channel.mention}\n"
                        f"**Kelime:** `{kelime}`\n"
                        f"**Mesaj:** {message.content}",
            color=renk
        )
        embed.set_footer(text=f"Mesaj ID: {message.id} | Model: Llama-3.1-8B")
        await self.log_kanalina_gonder(embed)

        try:
            await message.channel.send(
                f"🚫 {message.author.mention}, mesajın küfür/hakaret içeriyor! "
                f"`{kelime}` kelimesi yasaklı listesine eklendi.",
                delete_after=5
            )
        except:
            pass
        print(f"⛔ Engellendi ({tip}): {message.author.name} -> {kelime}")

    # ========== SLASH KOMUTLAR ==========
    
    @app_commands.command(name="kufur-listesi", description="Yasaklı küfür kelimelerinin listesini gösterir")
    @app_commands.default_permissions(manage_messages=True)
    async def kufur_listesi_slash(self, interaction: discord.Interaction):
        if not self.kufur_listesi:
            await interaction.response.send_message("📭 Kara liste şu an boş.", ephemeral=True)
            return

        # Listeyi parçalara böl (Discord embed limiti 4096 karakter)
        liste_metni = ", ".join(f"`{k}`" for k in self.kufur_listesi)
        
        if len(liste_metni) <= 4000:
            embed = discord.Embed(
                title=f"📋 Kara Liste ({len(self.kufur_listesi)} kelime)",
                description=liste_metni,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            # Çok uzunsa dosya olarak gönder
            with open("kufur_listesi.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.kufur_listesi))
            await interaction.response.send_message(
                f"📋 Liste çok uzun ({len(self.kufur_listesi)} kelime), dosya olarak gönderiyorum:",
                file=discord.File("kufur_listesi.txt"),
                ephemeral=True
            )

    @app_commands.command(name="kufur-kaldir", description="Kara listeden bir kelimeyi çıkarır")
    @app_commands.describe(kelime="Çıkarılacak kelime")
    @app_commands.default_permissions(manage_messages=True)
    async def kufur_kaldir_slash(self, interaction: discord.Interaction, kelime: str):
        kelime = kelime.lower().strip()
        
        if kelime in self.kufur_listesi:
            self.kufur_listesi.remove(kelime)
            kufur_listesini_kaydet(self.kufur_listesi)
            
            embed = discord.Embed(
                title="✅ Kelime Kara Listeden Çıkarıldı",
                description=f"`{kelime}` kelimesi artık yasaklı değil.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log kanalına da bildir
            log_embed = discord.Embed(
                title="✅ Kelime Kara Listeden Çıkarıldı",
                description=f"**Yetkili:** {interaction.user.mention}\n**Kelime:** `{kelime}`",
                color=discord.Color.green()
            )
            await self.log_kanalina_gonder(log_embed)
        else:
            await interaction.response.send_message(f"❌ `{kelime}` kelimesi kara listede bulunamadı.", ephemeral=True)

    # Slash komut hata yakalama (Yetki yoksa)
    @kufur_kaldir_slash.error
    @kufur_listesi_slash.error
    async def slash_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Bu komutu kullanmak için `Mesajları Yönet` yetkisine sahip olmalısın.", ephemeral=True)
        else:
            print(f"Slash komut hatası: {error}")


async def setup(bot):
    cog = NVIDIAAIKufurFiltresi(bot)
    await bot.add_cog(cog)
    
    # Sizin botunuzdaki message_handlers sistemine ekle
    if hasattr(bot, 'message_handlers'):
        bot.message_handlers.append(cog.on_learn_message)
        print("✅ NVIDIA AI Küfür Filtresi message_handlers'a eklendi.")
    
    print("✅ NVIDIA AI Küfür Filtresi (Slash Komutlu) yüklendi.")
