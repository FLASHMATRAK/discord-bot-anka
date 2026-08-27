import aiohttp

# UnbelievaBoat'un resmi ekonomi API'si. Bot token'ından farklı, ayrı bir API anahtarı gerektirir:
# https://unbelievaboat.com/api/docs adresinden sunucu sahibi kendi API anahtarını oluşturup
# config.json'daki "unbelievaboat_api_token" alanına yazmalı.
API_BASE = "https://unbelievaboat.com/api/v1"


async def add_cash(bot, guild_id: int, user_id: int, amount: int):
    """UnbelievaBoat ekonomisinde bir kullanıcının nakit bakiyesine 'amount' kadar ekler
    (negatif değer verilirse bakiyeden düşer).

    Başarılıysa (True, yeni_bakiye) döner.
    Başarısızsa (False, kullanıcıya/loga gösterilecek hata_mesajı) döner.
    """
    api_key = bot.config.get("unbelievaboat_api_token")
    if not api_key or api_key.startswith("BURAYA_"):
        return False, "⚠️ UnbelievaBoat API anahtarı `config.json` içinde ayarlanmamış (`unbelievaboat_api_token`)."

    url = f"{API_BASE}/guilds/{guild_id}/users/{user_id}"
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    payload = {"cash": amount}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return True, data.get("cash")
                if resp.status == 429:
                    return False, "⚠️ UnbelievaBoat API rate limit'e takıldı, birkaç saniye sonra tekrar dene."
                if resp.status == 403:
                    return False, "⚠️ UnbelievaBoat API anahtarı geçersiz ya da bu sunucuya erişim izni yok."
                text = await resp.text()
                return False, f"⚠️ UnbelievaBoat API hatası ({resp.status}): {text}"
    except aiohttp.ClientError as e:
        return False, f"⚠️ UnbelievaBoat API'ye bağlanılamadı: {e}"
