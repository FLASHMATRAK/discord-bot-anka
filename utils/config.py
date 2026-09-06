import json
import os

# config.json dosyasını okuyup Python sözlüğüne çeviren yardımcı fonksiyon


def load_config(path: str = "config.json") -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    try:
        config = json.loads(raw)

        # Secret yöneticilerinden gelen değerler, config.json içindeki değerlerin
        # önüne geçer. JSON dosyası böylece güvenli varsayılan ayarlar için kalır.
        secret_keys = {
            "DISCORD_TOKEN": "token",
            "TOKEN": "token",
            "NVIDIA_API_KEY": "nvidia_api_key",
            "UNBELIEVABOAT_API_TOKEN": "unbelievaboat_api_token",
        }
        for environment_key, config_key in secret_keys.items():
            secret = os.getenv(environment_key)
            if secret:
                config[config_key] = secret

        return config
    except json.JSONDecodeError as e:
        # Varsayılan hata mesajı sadece satır/sütun veriyor, dosyanın neresi olduğunu
        # görmek zorlaşıyor. Burada o satırı ve hatalı karakterin tam yerini gösteriyoruz.
        lines = raw.splitlines()
        bad_line = lines[e.lineno - 1] if 0 < e.lineno <= len(lines) else ""
        pointer = " " * (e.colno - 1) + "^"

        raise ValueError(
            f"\n\n❌ '{path}' geçerli bir JSON dosyası değil!\n"
            f"Hata: {e.msg} (satır {e.lineno}, sütun {e.colno})\n\n"
            f"  {bad_line}\n"
            f"  {pointer}\n\n"
            "En sık sebep: bir metin alanı ('token', 'nvidia_system_prompt' vb.) içine "
            "gerçek bir Enter (yeni satır) veya görünmez bir karakter yapıştırılmış olması. "
            "O satırdaki tırnaklar arasını silip yeniden, tek satır halinde yazmayı dene.\n"
        ) from None
