ANKA ECONOMY - DROP-IN PATCH
================================

Bu paket ekonomi branch'indeki ekonomi sistemini düzeltir.

DEĞİŞENLER
- EconomyManager içindeki work/crime akışı düzeltilmiştir.
- daily/work/crime cooldown'ları config.json'dan yönetilir.
- Config'e yeni ayar eklenince mevcut config korunur ve eksikler otomatik eklenir.
- Cooldown ayarları değiştirildiğinde eski cooldown kayıtları bir kez temizlenir.
- cash + bank = total korunur.
- UnbelievaBoat'tan import edilmiş kullanıcılar silinmez.
- UnbelievaBoat item kayıtları için geriye dönük uyumluluk vardır.
- Shop, inventory, buy, sell, use, giveitem, leaderboard ve item admin komutları eklendi.
- Para işlemleri transaction log'una yazılır.

ÖNEMLİ
-------
Bu ZIP mevcut users.json/items.json/inventory.json/transactions.json verilerini
bilerek içine koymaz. Böylece import edilmiş ekonomi verilerinin üzerine boş dosya
yazıp kaybetme riski olmaz.

KOPYALANACAK DOSYALAR
---------------------
commands/economy/
utils/economy_manager.py
data/economy/config.json
data/economy/crime_events.json

Mevcut data/economy/users.json
Mevcut data/economy/items.json
Mevcut data/economy/inventory.json
Mevcut data/economy/transactions.json
korunmalıdır.

COOLDOWN
--------
work_cooldown = 300  -> 5 dakika
crime_cooldown = 600 -> 10 dakika
daily_cooldown = 86400 -> 24 saat

Bot açıldığında config ayarları değişmişse eski cooldown'lar otomatik temizlenir.
