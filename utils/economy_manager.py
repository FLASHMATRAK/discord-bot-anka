import json
import os
import random
import time
import uuid


DEFAULT_CONFIG = {
    "starting_balance": 100,
    "daily_reward": 100,
    "daily_cooldown": 86400,
    "work_min": 20,
    "work_max": 100,
    "work_cooldown": 300,
    "crime_cooldown": 600,
    "sell_rate": 0.50,
    "transfer_limit": 10000,
    "shop_page_size": 6,
    "inventory_page_size": 8,
}


class EconomyManager:
    def __init__(self, data_dir="data/economy"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.users_file = os.path.join(data_dir, "users.json")
        self.inventory_file = os.path.join(data_dir, "inventory.json")
        self.cooldowns_file = os.path.join(data_dir, "cooldowns.json")
        self.transactions_file = os.path.join(data_dir, "transactions.json")
        self.items_file = os.path.join(data_dir, "items.json")
        self.config_file = os.path.join(data_dir, "config.json")
        self.crime_events_file = os.path.join(data_dir, "crime_events.json")

        self._ensure_file(self.users_file, {})
        self._ensure_file(self.inventory_file, {})
        self._ensure_file(self.cooldowns_file, {})
        self._ensure_file(self.transactions_file, [])
        self._ensure_file(self.items_file, {})
        self._ensure_file(self.config_file, DEFAULT_CONFIG)
        self._ensure_file(self.crime_events_file, [])

        self._repair_config()
        self._sync_cooldowns_after_config_change()

    def _ensure_file(self, path, default):
        if not os.path.exists(path):
            self._save_json(path, default)

    def _load_json(self, path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default

    def _save_json(self, path, data):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp, path)

    def _repair_config(self):
        cfg = self._load_json(self.config_file, {})
        changed = False
        for key, value in DEFAULT_CONFIG.items():
            if key not in cfg:
                cfg[key] = value
                changed = True
        if changed:
            self._save_json(self.config_file, cfg)

    def get_config(self):
        cfg = self._load_json(self.config_file, {})
        changed = False
        for key, value in DEFAULT_CONFIG.items():
            if key not in cfg:
                cfg[key] = value
                changed = True
        if changed:
            self._save_json(self.config_file, cfg)
        return cfg


    def _sync_cooldowns_after_config_change(self):
        """Config'teki cooldown değişince eski aktif cooldown'ları temizler."""
        cfg = self.get_config()
        watched = {
            "daily_cooldown": int(cfg.get("daily_cooldown", 86400)),
            "work_cooldown": int(cfg.get("work_cooldown", 300)),
            "crime_cooldown": int(cfg.get("crime_cooldown", 600)),
        }
        signature = json.dumps(watched, sort_keys=True)
        key = "_cooldown_signature"
        old = cfg.get(key)
        if old is not None and old != signature:
            self._save_json(self.cooldowns_file, {})
        if old != signature:
            cfg[key] = signature
            self._save_json(self.config_file, cfg)

    def currency_name(self):
        return self.get_config().get("currency_name", "Elmas")

    def currency_symbol(self):
        return self.get_config().get("currency_symbol", "💎")

    def create_user(self, user_id):
        uid = str(user_id)
        users = self._load_json(self.users_file, {})
        if uid not in users:
            starting = max(0, int(self.get_config().get("starting_balance", 100)))
            users[uid] = {
                "user_id": uid,
                "cash": starting,
                "bank": 0,
                "total": starting,
                "rank": None,
                "source": "economy",
            }
            self._save_json(self.users_file, users)
        return users[uid]

    def get_user(self, user_id):
        uid = str(user_id)
        users = self._load_json(self.users_file, {})
        if uid not in users:
            return self.create_user(uid)
        u = users[uid]
        cash = max(0, int(u.get("cash", 0)))
        bank = max(0, int(u.get("bank", 0)))
        u["user_id"] = uid
        u["cash"] = cash
        u["bank"] = bank
        u["total"] = cash + bank
        users[uid] = u
        self._save_json(self.users_file, users)
        return u

    def get_all_users(self):
        return self._load_json(self.users_file, {})

    def get_balance(self, user_id):
        return int(self.get_user(user_id)["total"])

    def get_cash(self, user_id):
        return int(self.get_user(user_id)["cash"])

    def get_bank(self, user_id):
        return int(self.get_user(user_id)["bank"])

    def _update_user(self, user_id, cash, bank):
        uid = str(user_id)
        users = self._load_json(self.users_file, {})
        if uid not in users:
            self.create_user(uid)
            users = self._load_json(self.users_file, {})
        cash, bank = int(cash), int(bank)
        if cash < 0 or bank < 0:
            raise ValueError("Bakiye negatif olamaz.")
        users[uid]["cash"] = cash
        users[uid]["bank"] = bank
        users[uid]["total"] = cash + bank
        self._save_json(self.users_file, users)
        return users[uid]

    def add_balance(self, user_id, amount, transaction_type="reward", source=None):
        amount = int(amount)
        if amount < 0:
            raise ValueError("Eklenen miktar negatif olamaz.")
        u = self.get_user(user_id)
        before = int(u["total"])
        cash = int(u["cash"]) + amount
        bank = int(u["bank"])
        self._update_user(user_id, cash, bank)
        after = cash + bank
        if amount:
            self._add_transaction(user_id, transaction_type, amount, before, after, source)
        return {"amount": amount, "before": before, "after": after, "balance": after}

    def remove_balance(self, user_id, amount, transaction_type="spend", source=None):
        amount = int(amount)
        if amount < 0:
            raise ValueError("Çıkarılan miktar negatif olamaz.")
        u = self.get_user(user_id)
        before = int(u["total"])
        if before < amount:
            raise ValueError("Yetersiz bakiye.")
        cash, bank = int(u["cash"]), int(u["bank"])
        take_cash = min(cash, amount)
        cash -= take_cash
        bank -= amount - take_cash
        self._update_user(user_id, cash, bank)
        after = cash + bank
        if amount:
            self._add_transaction(user_id, transaction_type, -amount, before, after, source)
        return {"amount": amount, "before": before, "after": after, "balance": after}

    def set_balance(self, user_id, amount, source=None):
        amount = int(amount)
        if amount < 0:
            raise ValueError("Bakiye negatif olamaz.")
        before = self.get_balance(user_id)
        self._update_user(user_id, amount, 0)
        self._add_transaction(user_id, "set_balance", amount - before, before, amount, source)
        return amount

    def transfer(self, sender_id, receiver_id, amount):
        sid, rid, amount = str(sender_id), str(receiver_id), int(amount)
        if sid == rid:
            raise ValueError("Kendine Elmas gönderemezsin.")
        if amount <= 0:
            raise ValueError("Miktar 0'dan büyük olmalı.")
        limit = int(self.get_config().get("transfer_limit", 10000))
        if amount > limit:
            raise ValueError(f"Transfer limiti {limit:,} Elmas.")
        sender = self.get_user(sid)
        receiver = self.get_user(rid)
        sb, rb = int(sender["total"]), int(receiver["total"])
        if sb < amount:
            raise ValueError("Yetersiz bakiye.")
        cash, bank = int(sender["cash"]), int(sender["bank"])
        take_cash = min(cash, amount)
        cash -= take_cash
        bank -= amount - take_cash
        rcash = int(receiver["cash"]) + amount
        self._update_user(sid, cash, bank)
        self._update_user(rid, rcash, int(receiver["bank"]))
        sa, ra = cash + bank, rcash + int(receiver["bank"])
        self._add_transaction(sid, "transfer_sent", -amount, sb, sa, f"to:{rid}")
        self._add_transaction(rid, "transfer_received", amount, rb, ra, f"from:{sid}")
        return {"sender_balance": sa, "receiver_balance": ra, "amount": amount}

    def get_cooldown(self, user_id, name):
        cds = self._load_json(self.cooldowns_file, {})
        return int(cds.get(str(user_id), {}).get(name, 0))

    def set_cooldown(self, user_id, name, seconds):
        cds = self._load_json(self.cooldowns_file, {})
        uid = str(user_id)
        cds.setdefault(uid, {})[name] = int(time.time()) + max(0, int(seconds))
        self._save_json(self.cooldowns_file, cds)

    def cooldown_remaining(self, user_id, name):
        return max(0, self.get_cooldown(user_id, name) - int(time.time()))

    def is_on_cooldown(self, user_id, name):
        return self.cooldown_remaining(user_id, name) > 0

    def claim_daily(self, user_id):
        rem = self.cooldown_remaining(user_id, "daily")
        if rem:
            raise ValueError(f"Daily beklemede. Kalan süre: {self.format_time(rem)}")
        cfg = self.get_config()
        reward = max(0, int(cfg.get("daily_reward", 100)))
        result = self.add_balance(user_id, reward, "daily", "daily")
        self.set_cooldown(user_id, "daily", int(cfg.get("daily_cooldown", 86400)))
        return {"reward": reward, "balance": result["balance"]}

    def do_work(self, user_id):
        rem = self.cooldown_remaining(user_id, "work")
        if rem:
            raise ValueError(f"Tekrar çalışmak için **{self.format_time(rem)}** beklemelisin.")
        cfg = self.get_config()
        lo, hi = int(cfg.get("work_min", 20)), int(cfg.get("work_max", 100))
        if lo > hi:
            lo, hi = hi, lo
        reward = random.randint(max(0, lo), max(0, hi))
        result = self.add_balance(user_id, reward, "work", "work")
        self.set_cooldown(user_id, "work", int(cfg.get("work_cooldown", 300)))
        return {"reward": reward, "balance": result["balance"]}

    def get_crime_events(self):
        events = self._load_json(self.crime_events_file, [])
        return events if isinstance(events, list) else []

    def get_random_crime_event(self):
        events = self.get_crime_events()
        if not events:
            raise ValueError("crime_events.json içinde olay bulunamadı.")
        return random.choice(events)

    def do_crime(self, user_id):
        rem = self.cooldown_remaining(user_id, "crime")
        if rem:
            raise ValueError(f"Tekrar denemek için **{self.format_time(rem)}** beklemelisin.")
        event = self.get_random_crime_event()
        risk = max(0, min(100, int(event.get("risk", 50))))
        lo = max(0, int(event.get("reward_min", 50)))
        hi = max(0, int(event.get("reward_max", 100)))
        if lo > hi:
            lo, hi = hi, lo
        loss_max = max(0, int(event.get("failure_loss", 0)))
        self.set_cooldown(user_id, "crime", int(self.get_config().get("crime_cooldown", 600)))

        success = random.randint(1, 100) > risk
        if not success:
            balance = self.get_balance(user_id)
            loss = min(loss_max, balance)
            if loss:
                self.remove_balance(user_id, loss, "crime_loss", str(event.get("id", "unknown")))
            return {
                "success": False, "event": event, "risk": risk,
                "reward": 0, "loss": loss, "wanted": False,
                "balance": self.get_balance(user_id)
            }

        reward = random.randint(lo, hi)
        self.add_balance(user_id, reward, "crime_reward", str(event.get("id", "unknown")))
        wanted = random.randint(1, 100) <= risk
        if wanted:
            self.set_wanted(
                user_id, True,
                max(1, int(event.get("wanted_level", 1))),
                max(0, int(event.get("wanted_duration", 3600)))
            )
        return {
            "success": True, "event": event, "risk": risk,
            "reward": reward, "loss": 0, "wanted": wanted,
            "balance": self.get_balance(user_id)
        }

    def set_wanted(self, user_id, wanted=True, level=1, duration=3600):
        uid = str(user_id)
        users = self._load_json(self.users_file, {})
        if uid not in users:
            self.create_user(uid)
            users = self._load_json(self.users_file, {})
        users[uid]["wanted"] = bool(wanted)
        users[uid]["wanted_level"] = int(level) if wanted else 0
        users[uid]["wanted_until"] = int(time.time()) + int(duration) if wanted else 0
        self._save_json(self.users_file, users)
        return users[uid]

    def get_wanted_info(self, user_id):
        u = self.get_user(user_id)
        wanted = bool(u.get("wanted", False))
        until = int(u.get("wanted_until", 0))
        if wanted and until and time.time() >= until:
            self.set_wanted(user_id, False)
            return {"wanted": False, "level": 0, "until": 0}
        return {"wanted": wanted, "level": int(u.get("wanted_level", 0)), "until": until}

    def is_wanted(self, user_id):
        return self.get_wanted_info(user_id)["wanted"]

    def _add_transaction(self, user_id, typ, amount, before, after, source=None):
        tx = self._load_json(self.transactions_file, [])
        if not isinstance(tx, list):
            tx = []
        tx.append({
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "type": str(typ),
            "amount": int(amount),
            "balance_before": int(before),
            "balance_after": int(after),
            "source": source,
            "timestamp": int(time.time()),
        })
        self._save_json(self.transactions_file, tx)

    def get_transactions(self, user_id=None, limit=50):
        tx = self._load_json(self.transactions_file, [])
        if user_id is not None:
            tx = [x for x in tx if str(x.get("user_id")) == str(user_id)]
        return tx[-max(1, int(limit)):]

    # ----- Items: supports both imported UnbelievaBoat records and native records -----
    def _normalize_item(self, item_id, raw):
        if not isinstance(raw, dict):
            return None
        iid = str(raw.get("item_id", raw.get("id", item_id)))
        name = raw.get("name", iid)
        emoji = raw.get("emoji", raw.get("emoji_unicode", "")) or "📦"
        price = int(raw.get("price", 0) or 0)
        sell_price = raw.get("sell_price")
        if sell_price is None:
            sell_price = int(price * float(self.get_config().get("sell_rate", 0.50)))
        return {
            "item_id": iid,
            "name": str(name),
            "description": str(raw.get("description", "")),
            "emoji": str(emoji),
            "price": max(0, price),
            "sell_price": max(0, int(sell_price)),
            "type": str(raw.get("type", "normal")),
            "stackable": bool(raw.get("stackable", True)),
            "tradable": bool(raw.get("tradable", raw.get("is_sellable", True))),
            "usable": bool(raw.get("usable", raw.get("is_usable", False))),
        }

    def get_items(self):
        raw = self._load_json(self.items_file, {})
        return {str(k): v for k, v in raw.items()} if isinstance(raw, dict) else {}

    def get_item(self, item_id):
        raw = self.get_items().get(str(item_id))
        return self._normalize_item(item_id, raw) if raw else None

    def create_item(self, item_id, name, description="", emoji="📦", price=0, sell_price=0,
                    item_type="normal", stackable=True, tradable=True, usable=False):
        iid = str(item_id)
        items = self.get_items()
        if iid in items:
            raise ValueError("Bu item zaten mevcut.")
        items[iid] = {
            "item_id": iid, "name": str(name), "description": str(description),
            "emoji": str(emoji), "price": max(0, int(price)),
            "sell_price": max(0, int(sell_price)),
            "type": str(item_type), "stackable": bool(stackable),
            "tradable": bool(tradable), "usable": bool(usable),
        }
        self._save_json(self.items_file, items)
        return items[iid]

    def edit_item(self, item_id, **changes):
        iid = str(item_id)
        items = self.get_items()
        if iid not in items:
            raise ValueError("Item bulunamadı.")
        allowed = {"name", "description", "emoji", "price", "sell_price", "type",
                   "stackable", "tradable", "usable"}
        for k, v in changes.items():
            if k in allowed:
                if k in {"price", "sell_price"}:
                    v = max(0, int(v))
                elif k in {"stackable", "tradable", "usable"}:
                    v = bool(v)
                else:
                    v = str(v)
                items[iid][k] = v
        self._save_json(self.items_file, items)
        return self._normalize_item(iid, items[iid])

    def delete_item(self, item_id):
        iid = str(item_id)
        items = self.get_items()
        if iid not in items:
            raise ValueError("Item bulunamadı.")
        deleted = items.pop(iid)
        self._save_json(self.items_file, items)
        return deleted

    def get_inventory(self, user_id):
        inv = self._load_json(self.inventory_file, {})
        data = inv.get(str(user_id), {}) if isinstance(inv, dict) else {}
        return data if isinstance(data, dict) else {}

    def get_item_quantity(self, user_id, item_id):
        return int(self.get_inventory(user_id).get(str(item_id), 0))

    def add_item(self, user_id, item_id, quantity=1):
        iid, quantity = str(item_id), int(quantity)
        if quantity <= 0:
            raise ValueError("Miktar 0'dan büyük olmalı.")
        item = self.get_item(iid)
        if item is None:
            raise ValueError("Item bulunamadı.")
        inv = self._load_json(self.inventory_file, {})
        inv.setdefault(str(user_id), {})
        current = int(inv[str(user_id)].get(iid, 0))
        if not item["stackable"] and current:
            raise ValueError("Bu item stacklenemez.")
        inv[str(user_id)][iid] = current + quantity
        self._save_json(self.inventory_file, inv)
        return inv[str(user_id)][iid]

    def remove_item(self, user_id, item_id, quantity=1):
        iid, quantity = str(item_id), int(quantity)
        if quantity <= 0:
            raise ValueError("Miktar 0'dan büyük olmalı.")
        inv = self._load_json(self.inventory_file, {})
        data = inv.get(str(user_id), {})
        current = int(data.get(iid, 0))
        if current < quantity:
            raise ValueError("Yeterli item yok.")
        new = current - quantity
        if new:
            data[iid] = new
        else:
            data.pop(iid, None)
        inv[str(user_id)] = data
        self._save_json(self.inventory_file, inv)
        return new

    def buy_item(self, user_id, item_id, quantity=1):
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("Miktar 0'dan büyük olmalı.")
        item = self.get_item(item_id)
        if item is None:
            raise ValueError("Item bulunamadı.")
        total = item["price"] * quantity
        self.remove_balance(user_id, total, "shop_purchase", str(item_id))
        try:
            self.add_item(user_id, item_id, quantity)
        except Exception:
            self.add_balance(user_id, total, "shop_refund", str(item_id))
            raise
        return {"item": item, "quantity": quantity, "price": total, "balance": self.get_balance(user_id)}

    def sell_item(self, user_id, item_id, quantity=1):
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("Miktar 0'dan büyük olmalı.")
        item = self.get_item(item_id)
        if item is None:
            raise ValueError("Item bulunamadı.")
        if self.get_item_quantity(user_id, item_id) < quantity:
            raise ValueError("Yeterli item yok.")
        if not item["tradable"]:
            raise ValueError("Bu item satılamaz.")
        total = item["sell_price"] * quantity
        self.remove_item(user_id, item_id, quantity)
        try:
            result = self.add_balance(user_id, total, "shop_sell", str(item_id))
        except Exception:
            self.add_item(user_id, item_id, quantity)
            raise
        return {"item": item, "quantity": quantity, "price": total, "balance": result["balance"]}

    def use_item(self, user_id, item_id, quantity=1):
        quantity = int(quantity)
        item = self.get_item(item_id)
        if item is None:
            raise ValueError("Item bulunamadı.")
        if not item["usable"]:
            raise ValueError("Bu item kullanılamaz.")
        self.remove_item(user_id, item_id, quantity)
        return {"item": item, "quantity": quantity, "balance": self.get_balance(user_id)}

    def give_item(self, sender_id, receiver_id, item_id, quantity=1):
        if str(sender_id) == str(receiver_id):
            raise ValueError("Kendine item gönderemezsin.")
        item = self.get_item(item_id)
        if item is None:
            raise ValueError("Item bulunamadı.")
        if not item["tradable"]:
            raise ValueError("Bu item takas edilemez.")
        self.remove_item(sender_id, item_id, quantity)
        try:
            self.add_item(receiver_id, item_id, quantity)
        except Exception:
            self.add_item(sender_id, item_id, quantity)
            raise
        return {"item": item, "quantity": int(quantity), "sender_balance": self.get_balance(sender_id)}

    def get_rich_leaderboard(self):
        result = []
        for uid, u in self.get_all_users().items():
            total = int(u.get("cash", 0)) + int(u.get("bank", 0))
            result.append({"user_id": str(uid), "total": total})
        return sorted(result, key=lambda x: x["total"], reverse=True)

    def get_user_rank(self, user_id):
        for i, row in enumerate(self.get_rich_leaderboard(), 1):
            if row["user_id"] == str(user_id):
                return i
        return None

    def get_collectors_leaderboard(self):
        inv = self._load_json(self.inventory_file, {})
        result = []
        for uid, data in inv.items():
            if isinstance(data, dict):
                quantities = [int(v) for v in data.values()]
                result.append({
                    "user_id": str(uid),
                    "items": sum(quantities),
                    "unique_items": len(data),
                })
        return sorted(result, key=lambda x: (x["unique_items"], x["items"]), reverse=True)

    @staticmethod
    def format_time(seconds):
        seconds = int(seconds)
        if seconds <= 0:
            return "hazır"
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        parts = []
        if days: parts.append(f"{days}g")
        if hours: parts.append(f"{hours}s")
        if minutes: parts.append(f"{minutes}dk")
        if seconds and not days: parts.append(f"{seconds}sn")
        return " ".join(parts) if parts else "hazır"
