from collections import defaultdict

# ============ PAYLAŞILAN VERİ (Bellekte Tutulan Durum) ============
# Bu dosyadaki değişkenler tüm komut dosyaları tarafından ortak kullanılır.
# NOT: Bot her yeniden başladığında bu veriler sıfırlanır (kalıcı değil).

# --- Moderasyon ---
rap_sheet = defaultdict(list)      # {user_id: [ {"type":..,"reason":..,"moderator":..,"date":..} ]}
warnings = defaultdict(list)       # {user_id: [ {"word":..., "date":...} ]}
spam_tracker = defaultdict(list)   # {user_id: [timestamp, ...]}

# --- Hunter / Outlaw Puan Sistemi ---
hunter_points = defaultdict(int)
outlaw_points = defaultdict(int)
match_history = defaultdict(list)  # {user_id: [ {"vs":.., "result":.., "date":..} ]}
role_icons = {}                    # main.py içinde config'ten doldurulacak

# --- Wanted / Ödül Avı Sistemi ---
wanted_data = {}         # {user_id: {"bounty": puan, "since": tarih}}
last_wanted_time = {}    # {user_id: tarih}

# --- Yapay Zeka Sohbet (NVIDIA NIM) ---
ai_chat_history = defaultdict(list)  # {user_id: [{"role": "user"/"assistant", "content": ...}, ...]}
