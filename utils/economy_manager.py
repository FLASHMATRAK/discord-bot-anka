import json
import os
import random
import time
import uuid


class EconomyManager:

    def __init__(self, data_dir="data/economy"):
        self.data_dir = data_dir

        os.makedirs(
            self.data_dir,
            exist_ok=True
        )

        self.users_file = os.path.join(
            self.data_dir,
            "users.json"
        )

        self.inventory_file = os.path.join(
            self.data_dir,
            "inventory.json"
        )

        self.cooldowns_file = os.path.join(
            self.data_dir,
            "cooldowns.json"
        )

        self.transactions_file = os.path.join(
            self.data_dir,
            "transactions.json"
        )

        self.items_file = os.path.join(
            self.data_dir,
            "items.json"
        )

        self.config_file = os.path.join(
            self.data_dir,
            "config.json"
        )

        self.crime_events_file = os.path.join(
            self.data_dir,
            "crime_events.json"
        )

        # -----------------------------------------------------
        # DOSYALARI OLUŞTUR
        # -----------------------------------------------------

        self._ensure_file(
            self.users_file,
            {}
        )

        self._ensure_file(
            self.inventory_file,
            {}
        )

        self._ensure_file(
            self.cooldowns_file,
            {}
        )

        self._ensure_file(
            self.transactions_file,
            []
        )

        self._ensure_file(
            self.items_file,
            {}
        )

        self._ensure_file(
            self.config_file,
            {
                "starting_balance": 100,
                "daily_reward": 100,

                "work_min": 20,
                "work_max": 100,
                "work_cooldown": 60,

                "crime_cooldown": 1,

                "sell_rate": 0.50,

                "transfer_limit": 10000
            }
        )

        self._ensure_file(
            self.crime_events_file,
            []
        )

    # =========================================================
    # JSON
    # =========================================================

    def _ensure_file(
        self,
        path,
        default
    ):
        if not os.path.exists(path):
            self._save_json(
                path,
                default
            )

    def _load_json(
        self,
        path,
        default
    ):
        try:
            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

                return data

        except (
            FileNotFoundError,
            json.JSONDecodeError
        ):
            return default

    def _save_json(
        self,
        path,
        data
    ):
        temp_path = path + ".tmp"

        with open(
            temp_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        os.replace(
            temp_path,
            path
        )

    # =========================================================
    # CONFIG
    # =========================================================

    def get_config(self):
        return self._load_json(
            self.config_file,
            {}
        )

    # =========================================================
    # USERS
    # =========================================================

    def create_user(
        self,
        user_id
    ):
        user_id = str(user_id)

        users = self._load_json(
            self.users_file,
            {}
        )

        if user_id not in users:

            config = self.get_config()

            starting_balance = int(
                config.get(
                    "starting_balance",
                    100
                )
            )

            users[user_id] = {
                "user_id": user_id,
                "cash": starting_balance,
                "bank": 0,
                "total": starting_balance,
                "rank": None,
                "source": "economy"
            }

            self._save_json(
                self.users_file,
                users
            )

        return users[user_id]

    def get_user(
        self,
        user_id
    ):
        user_id = str(user_id)

        users = self._load_json(
            self.users_file,
            {}
        )

        # Yeni kullanıcı
        if user_id not in users:
            return self.create_user(
                user_id
            )

        user = users[user_id]

        # Eski UnbelievaBoat verilerinin
        # cash + bank = total olmasını garanti et.
        cash = int(
            user.get(
                "cash",
                0
            )
        )

        bank = int(
            user.get(
                "bank",
                0
            )
        )

        user["user_id"] = user_id
        user["cash"] = cash
        user["bank"] = bank
        user["total"] = cash + bank

        users[user_id] = user

        self._save_json(
            self.users_file,
            users
        )

        return user

    def get_all_users(self):
        return self._load_json(
            self.users_file,
            {}
        )

    # =========================================================
    # BALANCE
    # =========================================================

    def get_balance(
        self,
        user_id
    ):
        user = self.get_user(
            user_id
        )

        return int(
            user["total"]
        )

    def get_cash(
        self,
        user_id
    ):
        user = self.get_user(
            user_id
        )

        return int(
            user["cash"]
        )

    def get_bank(
        self,
        user_id
    ):
        user = self.get_user(
            user_id
        )

        return int(
            user["bank"]
        )

    def _update_user(
        self,
        user_id,
        cash,
        bank
    ):
        user_id = str(user_id)

        users = self._load_json(
            self.users_file,
            {}
        )

        if user_id not in users:
            self.create_user(
                user_id
            )

            users = self._load_json(
                self.users_file,
                {}
            )

        cash = int(cash)
        bank = int(bank)

        if cash < 0:
            raise ValueError(
                "Nakit bakiye negatif olamaz."
            )

        if bank < 0:
            raise ValueError(
                "Banka bakiyesi negatif olamaz."
            )

        users[user_id]["cash"] = cash
        users[user_id]["bank"] = bank
        users[user_id]["total"] = cash + bank

        self._save_json(
            self.users_file,
            users
        )

        return users[user_id]

    # =========================================================
    # PARA EKLE
    # =========================================================

    def add_balance(
        self,
        user_id,
        amount,
        transaction_type="reward",
        source=None
    ):
        user_id = str(user_id)
        amount = int(amount)

        if amount < 0:
            raise ValueError(
                "Eklenen miktar negatif olamaz."
            )

        user = self.get_user(
            user_id
        )

        before = int(
            user["total"]
        )

        if amount == 0:
            return {
                "amount": 0,
                "before": before,
                "after": before,
                "balance": before
            }

        cash = int(
            user["cash"]
        ) + amount

        bank = int(
            user["bank"]
        )

        self._update_user(
            user_id,
            cash,
            bank
        )

        after = cash + bank

        self._add_transaction(
            user_id,
            transaction_type,
            amount,
            before,
            after,
            source
        )

        return {
            "amount": amount,
            "before": before,
            "after": after,
            "balance": after
        }

    # =========================================================
    # PARA ÇIKAR
    # =========================================================

    def remove_balance(
        self,
        user_id,
        amount,
        transaction_type="spend",
        source=None
    ):
        user_id = str(user_id)
        amount = int(amount)

        if amount < 0:
            raise ValueError(
                "Çıkarılan miktar negatif olamaz."
            )

        user = self.get_user(
            user_id
        )

        before = int(
            user["total"]
        )

        if amount == 0:
            return {
                "amount": 0,
                "before": before,
                "after": before,
                "balance": before
            }

        if before < amount:
            raise ValueError(
                "Yetersiz bakiye."
            )

        cash = int(
            user["cash"]
        )

        bank = int(
            user["bank"]
        )

        # Önce nakitten düş.
        if cash >= amount:

            cash -= amount

        else:

            remaining = amount - cash

            cash = 0

            bank -= remaining

        self._update_user(
            user_id,
            cash,
            bank
        )

        after = cash + bank

        self._add_transaction(
            user_id,
            transaction_type,
            -amount,
            before,
            after,
            source
        )

        return {
            "amount": amount,
            "before": before,
            "after": after,
            "balance": after
        }

    # =========================================================
    # BAKİYE AYARLA
    # =========================================================

    def set_balance(
        self,
        user_id,
        amount,
        source=None
    ):
        user_id = str(user_id)
        amount = int(amount)

        if amount < 0:
            raise ValueError(
                "Bakiye negatif olamaz."
            )

        user = self.get_user(
            user_id
        )

        before = int(
            user["total"]
        )

        self._update_user(
            user_id,
            amount,
            0
        )

        self._add_transaction(
            user_id,
            "set_balance",
            amount - before,
            before,
            amount,
            source
        )

        return amount

    # =========================================================
    # TRANSFER
    # =========================================================

    def transfer(
        self,
        sender_id,
        receiver_id,
        amount
    ):
        sender_id = str(sender_id)
        receiver_id = str(receiver_id)
        amount = int(amount)

        if sender_id == receiver_id:
            raise ValueError(
                "Kendine Elmas gönderemezsin."
            )

        if amount <= 0:
            raise ValueError(
                "Miktar 0'dan büyük olmalı."
            )

        config = self.get_config()

        limit = int(
            config.get(
                "transfer_limit",
                10000
            )
        )

        if amount > limit:
            raise ValueError(
                f"Transfer limiti {limit:,} Elmas."
            )

        sender = self.get_user(
            sender_id
        )

        receiver = self.get_user(
            receiver_id
        )

        sender_before = int(
            sender["total"]
        )

        receiver_before = int(
            receiver["total"]
        )

        if sender_before < amount:
            raise ValueError(
                "Yetersiz bakiye."
            )

        sender_cash = int(
            sender["cash"]
        )

        sender_bank = int(
            sender["bank"]
        )

        # Önce cash.
        if sender_cash >= amount:

            sender_cash -= amount

        else:

            remaining = amount - sender_cash

            sender_cash = 0

            sender_bank -= remaining

        receiver_cash = int(
            receiver["cash"]
        ) + amount

        receiver_bank = int(
            receiver["bank"]
        )

        self._update_user(
            sender_id,
            sender_cash,
            sender_bank
        )

        self._update_user(
            receiver_id,
            receiver_cash,
            receiver_bank
        )

        sender_after = (
            sender_cash +
            sender_bank
        )

        receiver_after = (
            receiver_cash +
            receiver_bank
        )

        self._add_transaction(
            sender_id,
            "transfer_sent",
            -amount,
            sender_before,
            sender_after,
            f"to:{receiver_id}"
        )

        self._add_transaction(
            receiver_id,
            "transfer_received",
            amount,
            receiver_before,
            receiver_after,
            f"from:{sender_id}"
        )

        return {
            "sender_balance": sender_after,
            "receiver_balance": receiver_after,
            "amount": amount
        }

    # =========================================================
    # COOLDOWN
    # =========================================================

    def get_cooldown(
        self,
        user_id,
        cooldown_name
    ):
        user_id = str(user_id)

        cooldowns = self._load_json(
            self.cooldowns_file,
            {}
        )

        return int(
            cooldowns.get(
                user_id,
                {}
            ).get(
                cooldown_name,
                0
            )
        )

    def set_cooldown(
        self,
        user_id,
        cooldown_name,
        seconds
    ):
        user_id = str(user_id)
        seconds = int(seconds)

        if seconds < 0:
            seconds = 0

        cooldowns = self._load_json(
            self.cooldowns_file,
            {}
        )

        if user_id not in cooldowns:
            cooldowns[user_id] = {}

        cooldowns[user_id][cooldown_name] = (
            int(time.time()) +
            seconds
        )

        self._save_json(
            self.cooldowns_file,
            cooldowns
        )

    def cooldown_remaining(
        self,
        user_id,
        cooldown_name
    ):
        expires = self.get_cooldown(
            user_id,
            cooldown_name
        )

        return max(
            0,
            expires - int(time.time())
        )

    def is_on_cooldown(
        self,
        user_id,
        cooldown_name
    ):
        return (
            self.cooldown_remaining(
                user_id,
                cooldown_name
            ) > 0
        )

    # =========================================================
    # DAILY
    # =========================================================

    def claim_daily(
        self,
        user_id
    ):
        user_id = str(user_id)

        remaining = self.cooldown_remaining(
            user_id,
            "daily"
        )

        if remaining > 0:
            raise ValueError(
                "Daily beklemede. "
                f"Kalan süre: "
                f"{self.format_time(remaining)}"
            )

        config = self.get_config()

        reward = int(
            config.get(
                "daily_reward",
                100
            )
        )

        result = self.add_balance(
            user_id,
            reward,
            transaction_type="daily",
            source="daily"
        )

        self.set_cooldown(
            user_id,
            "daily",
            86400
        )

        return {
            "reward": reward,
            "balance": result["balance"]
        }

    # =========================================================
    # WORK
    # =========================================================

    def do_work(
        self,
        user_id
    ):
        user_id = str(user_id)

        remaining = self.cooldown_remaining(
            user_id,
            "work"
        )

        if remaining > 0:
            raise ValueError(
                "Tekrar çalışmak için "
                f"**{self.format_time(remaining)}** "
                "beklemelisin."
            )

        config = self.get_config()

        work_min = int(
            config.get(
                "work_min",
                20
            )
        )

        work_max = int(
            config.get(
                "work_max",
                100
            )
        )

        cooldown = int(
            config.get(
                "work_cooldown",
                1800
            )
        )

        if work_min > work_max:
            work_min, work_max = (
                work_max,
                work_min
            )

        reward = random.randint(
            work_min,
            work_max
        )

        result = self.add_balance(
            user_id,
            reward,
            transaction_type="work",
            source="work"
        )

        self.set_cooldown(
            user_id,
            "work",
            cooldown
        )

        return {
            "reward": reward,
            "balance": result["balance"]
        }

    # =========================================================
    # CRIME EVENTS
    # =========================================================

    def get_crime_events(self):
        events = self._load_json(
            self.crime_events_file,
            []
        )

        if not isinstance(
            events,
            list
        ):
            return []

        return events

    def get_random_crime_event(self):
        events = self.get_crime_events()

        if not events:
            raise ValueError(
                "crime_events.json içinde "
                "olay bulunamadı."
            )

        return random.choice(
            events
        )

    # =========================================================
    # CRIME
    # =========================================================

    def do_crime(
        self,
        user_id
    ):
        user_id = str(user_id)

        remaining = self.cooldown_remaining(
            user_id,
            "crime"
        )

        if remaining > 0:
            raise ValueError(
                "Tekrar suç denemek için "
                f"**{self.format_time(remaining)}** "
                "beklemelisin."
            )

        event = self.get_random_crime_event()

        if not event:
            raise ValueError(
                "Henüz tanımlanmış "
                "bir suç etkinliği bulunmuyor."
            )

        event_id = str(
            event.get(
                "id",
                "unknown"
            )
        )

        # -----------------------------------------------------
        # RİSK
        # -----------------------------------------------------

        risk = max(
            0,
            min(
                100,
                int(
                    event.get(
                        "risk",
                        50
                    )
                )
            )
        )

        # -----------------------------------------------------
        # ÖDÜL
        # -----------------------------------------------------

        reward_min = int(
            event.get(
                "reward_min",
                50
            )
        )

        reward_max = int(
            event.get(
                "reward_max",
                100
            )
        )

        if reward_min < 0:
            reward_min = 0

        if reward_max < reward_min:
            reward_min, reward_max = (
                reward_max,
                reward_min
            )

        # -----------------------------------------------------
        # BAŞARISIZLIKTA KAYIP
        # -----------------------------------------------------

        failure_loss = int(
            event.get(
                "failure_loss",
                0
            )
        )

        if failure_loss < 0:
            failure_loss = 0

        # -----------------------------------------------------
        # COOLDOWN
        # -----------------------------------------------------

        config = self.get_config()

        cooldown = int(
            config.get(
                "crime_cooldown",
                1800
            )
        )

        # -----------------------------------------------------
        # SUÇ DENEMESİ
        #
        # Risk 20 ise yaklaşık %80 başarı.
        # Risk 80 ise yaklaşık %20 başarı.
        # -----------------------------------------------------

        success = (
            random.randint(
                1,
                100
            ) > risk
        )

        # Her denemeden sonra cooldown.
        self.set_cooldown(
            user_id,
            "crime",
            cooldown
        )

        # =====================================================
        # BAŞARISIZ
        # =====================================================

        if not success:

            balance = self.get_balance(
                user_id
            )

            actual_loss = min(
                failure_loss,
                balance
            )

            if actual_loss > 0:

                self.remove_balance(
                    user_id,
                    actual_loss,
                    transaction_type="crime_loss",
                    source=event_id
                )

            # ÖNEMLİ:
            # Başarısız suçta wanted yok.
            return {
                "success": False,
                "event": event,
                "risk": risk,
                "reward": 0,
                "loss": actual_loss,
                "wanted": False,
                "balance": self.get_balance(
                    user_id
                )
            }

        # =====================================================
        # BAŞARILI
        # =====================================================

        reward = random.randint(
            reward_min,
            reward_max
        )

        self.add_balance(
            user_id,
            reward,
            transaction_type="crime_reward",
            source=event_id
        )

        # -----------------------------------------------------
        # WANTED KONTROLÜ
        #
        # Sadece başarılı suçtan sonra.
        # -----------------------------------------------------

        wanted = (
            random.randint(
                1,
                100
            ) <= risk
        )

        if wanted:

            wanted_level = int(
                event.get(
                    "wanted_level",
                    1
                )
            )

            wanted_duration = int(
                event.get(
                    "wanted_duration",
                    3600
                )
            )

            if wanted_level < 1:
                wanted_level = 1

            if wanted_duration < 0:
                wanted_duration = 0

            self.set_wanted(
                user_id,
                wanted=True,
                level=wanted_level,
                duration=wanted_duration
            )

        return {
            "success": True,
            "event": event,
            "risk": risk,
            "reward": reward,
            "loss": 0,
            "wanted": wanted,
            "balance": self.get_balance(
                user_id
            )
        }

    # =========================================================
    # WANTED
    # =========================================================

    def set_wanted(
        self,
        user_id,
        wanted=True,
        level=1,
        duration=3600
    ):
        user_id = str(user_id)

        users = self._load_json(
            self.users_file,
            {}
        )

        if user_id not in users:
            self.create_user(
                user_id
            )

            users = self._load_json(
                self.users_file,
                {}
            )

        if wanted:

            users[user_id]["wanted"] = True

            users[user_id]["wanted_level"] = int(
                level
            )

            users[user_id]["wanted_until"] = (
                int(time.time()) +
                int(duration)
            )

        else:

            users[user_id]["wanted"] = False

            users[user_id]["wanted_level"] = 0

            users[user_id]["wanted_until"] = 0

        self._save_json(
            self.users_file,
            users
        )

        return users[user_id]

    def is_wanted(
        self,
        user_id
    ):
        user = self.get_user(
            user_id
        )

        wanted = bool(
            user.get(
                "wanted",
                False
            )
        )

        until = int(
            user.get(
                "wanted_until",
                0
            )
        )

        if wanted and until > 0:

            if int(time.time()) >= until:

                self.set_wanted(
                    user_id,
                    False
                )

                return False

        return wanted

    def get_wanted_info(
        self,
        user_id
    ):
        user = self.get_user(
            user_id
        )

        wanted = bool(
            user.get(
                "wanted",
                False
            )
        )

        level = int(
            user.get(
                "wanted_level",
                0
            )
        )

        until = int(
            user.get(
                "wanted_until",
                0
            )
        )

        # Süresi dolmuşsa temizle.
        if wanted and until > 0:

            if int(time.time()) >= until:

                self.set_wanted(
                    user_id,
                    False
                )

                wanted = False
                level = 0
                until = 0

        return {
            "wanted": wanted,
            "level": level,
            "until": until
        }

    # =========================================================
    # TRANSACTIONS
    # =========================================================

    def _add_transaction(
        self,
        user_id,
        transaction_type,
        amount,
        balance_before,
        balance_after,
        source=None
    ):
        transactions = self._load_json(
            self.transactions_file,
            []
        )

        if not isinstance(
            transactions,
            list
        ):
            transactions = []

        transaction = {
            "id": str(
                uuid.uuid4()
            ),

            "user_id": str(
                user_id
            ),

            "type": str(
                transaction_type
            ),

            "amount": int(
                amount
            ),

            "balance_before": int(
                balance_before
            ),

            "balance_after": int(
                balance_after
            ),

            "source": source,

            "timestamp": int(
                time.time()
            )
        }

        transactions.append(
            transaction
        )

        self._save_json(
            self.transactions_file,
            transactions
        )

        return transaction

    def get_transactions(
        self,
        user_id=None,
        limit=50
    ):
        transactions = self._load_json(
            self.transactions_file,
            []
        )

        if not isinstance(
            transactions,
            list
        ):
            return []

        if user_id is not None:

            user_id = str(
                user_id
            )

            transactions = [
                transaction
                for transaction in transactions
                if str(
                    transaction.get(
                        "user_id"
                    )
                ) == user_id
            ]

        limit = max(
            1,
            int(limit)
        )

        return transactions[-limit:]

    # =========================================================
    # ITEMS
    # =========================================================

    def get_items(self):
        items = self._load_json(
            self.items_file,
            {}
        )

        if not isinstance(
            items,
            dict
        ):
            return {}

        return items

    def get_item(
        self,
        item_id
    ):
        item_id = str(
            item_id
        )

        return self.get_items().get(
            item_id
        )

    def create_item(
        self,
        item_id,
        name,
        description="",
        emoji="📦",
        price=0,
        sell_price=0,
        item_type="normal",
        stackable=True,
        tradable=True,
        usable=False
    ):
        item_id = str(
            item_id
        )

        items = self.get_items()

        if item_id in items:
            raise ValueError(
                "Bu item zaten mevcut."
            )

        price = int(
            price
        )

        sell_price = int(
            sell_price
        )

        if price < 0:
            raise ValueError(
                "Item fiyatı negatif olamaz."
            )

        if sell_price < 0:
            raise ValueError(
                "Satış fiyatı negatif olamaz."
            )

        items[item_id] = {
            "item_id": item_id,
            "name": str(name),
            "description": str(description),
            "emoji": str(emoji),
            "price": price,
            "sell_price": sell_price,
            "type": str(item_type),
            "stackable": bool(stackable),
            "tradable": bool(tradable),
            "usable": bool(usable)
        }

        self._save_json(
            self.items_file,
            items
        )

        return items[item_id]

    def edit_item(
        self,
        item_id,
        **changes
    ):
        item_id = str(
            item_id
        )

        items = self.get_items()

        if item_id not in items:
            raise ValueError(
                "Item bulunamadı."
            )

        allowed_fields = {
            "name",
            "description",
            "emoji",
            "price",
            "sell_price",
            "type",
            "stackable",
            "tradable",
            "usable"
        }

        for key, value in changes.items():

            if key not in allowed_fields:
                continue

            if key in {
                "price",
                "sell_price"
            }:

                value = int(
                    value
                )

                if value < 0:
                    raise ValueError(
                        "Fiyat negatif olamaz."
                    )

            elif key in {
                "stackable",
                "tradable",
                "usable"
            }:

                value = bool(
                    value
                )

            else:

                value = str(
                    value
                )

            items[item_id][key] = value

        self._save_json(
            self.items_file,
            items
        )

        return items[item_id]

    def delete_item(
        self,
        item_id
    ):
        item_id = str(
            item_id
        )

        items = self.get_items()

        if item_id not in items:
            raise ValueError(
                "Item bulunamadı."
            )

        deleted = items.pop(
            item_id
        )

        self._save_json(
            self.items_file,
            items
        )

        return deleted

    # =========================================================
    # INVENTORY
    # =========================================================

    def get_inventory(
        self,
        user_id
    ):
        user_id = str(
            user_id
        )

        inventory = self._load_json(
            self.inventory_file,
            {}
        )

        if not isinstance(
            inventory,
            dict
        ):
            return {}

        return inventory.get(
            user_id,
            {}
        )

    def get_item_quantity(
        self,
        user_id,
        item_id
    ):
        inventory = self.get_inventory(
            user_id
        )

        return int(
            inventory.get(
                str(item_id),
                0
            )
        )

    def add_item(
        self,
        user_id,
        item_id,
        quantity=1
    ):
        user_id = str(
            user_id
        )

        item_id = str(
            item_id
        )

        quantity = int(
            quantity
        )

        if quantity <= 0:
            raise ValueError(
                "Miktar 0'dan büyük olmalı."
            )

        item = self.get_item(
            item_id
        )

        if item is None:
            raise ValueError(
                "Item bulunamadı."
            )

        inventory = self._load_json(
            self.inventory_file,
            {}
        )

        if not isinstance(
            inventory,
            dict
        ):
            inventory = {}

        if user_id not in inventory:
            inventory[user_id] = {}

        current = int(
            inventory[user_id].get(
                item_id,
                0
            )
        )

        if not item.get(
            "stackable",
            True
        ) and current > 0:

            raise ValueError(
                "Bu item stacklenemez."
            )

        inventory[user_id][item_id] = (
            current +
            quantity
        )

        self._save_json(
            self.inventory_file,
            inventory
        )

        return inventory[user_id][item_id]

    def remove_item(
        self,
        user_id,
        item_id,
        quantity=1
    ):
        user_id = str(
            user_id
        )

        item_id = str(
            item_id
        )

        quantity = int(
            quantity
        )

        if quantity <= 0:
            raise ValueError(
                "Miktar 0'dan büyük olmalı."
            )

        inventory = self._load_json(
            self.inventory_file,
            {}
        )

        if not isinstance(
            inventory,
            dict
        ):
            inventory = {}

        if user_id not in inventory:
            raise ValueError(
                "Envanter boş."
            )

        current = int(
            inventory[user_id].get(
                item_id,
                0
            )
        )

        if current < quantity:
            raise ValueError(
                "Yeterli item yok."
            )

        new_amount = (
            current -
            quantity
        )

        if new_amount == 0:

            inventory[user_id].pop(
                item_id,
                None
            )

        else:

            inventory[user_id][item_id] = (
                new_amount
            )

        self._save_json(
            self.inventory_file,
            inventory
        )

        return new_amount

    # =========================================================
    # BUY
    # =========================================================

    def buy_item(
        self,
        user_id,
        item_id,
        quantity=1
    ):
        user_id = str(
            user_id
        )

        item_id = str(
            item_id
        )

        quantity = int(
            quantity
        )

        if quantity <= 0:
            raise ValueError(
                "Miktar 0'dan büyük olmalı."
            )

        item = self.get_item(
            item_id
        )

        if item is None:
            raise ValueError(
                "Item bulunamadı."
            )

        price = int(
            item.get(
                "price",
                0
            )
        )

        if price < 0:
            raise ValueError(
                "Item fiyatı geçersiz."
            )

        total_price = (
            price *
            quantity
        )

        balance_before = self.get_balance(
            user_id
        )

        if balance_before < total_price:
            raise ValueError(
                "Yetersiz bakiye."
            )

        self.remove_balance(
            user_id,
            total_price,
            transaction_type="shop_purchase",
            source=item_id
        )

        try:

            self.add_item(
                user_id,
                item_id,
                quantity
            )

        except Exception:

            # Item eklenemezse parayı geri ver.
            self.add_balance(
                user_id,
                total_price,
                transaction_type="shop_refund",
                source=item_id
            )

            raise

        return {
            "item": item,
            "quantity": quantity,
            "price": total_price,
            "balance": self.get_balance(
                user_id
            )
        }

    # =========================================================
    # SELL
    # =========================================================

    def sell_item(
        self,
        user_id,
        item_id,
        quantity=1
    ):
        user_id = str(
            user_id
        )

        item_id = str(
            item_id
        )

        quantity = int(
            quantity
        )

        if quantity <= 0:
            raise ValueError(
                "Miktar 0'dan büyük olmalı."
            )

        item = self.get_item(
            item_id
        )

        if item is None:
            raise ValueError(
                "Item bulunamadı."
            )

        owned = self.get_item_quantity(
            user_id,
            item_id
        )

        if owned < quantity:
            raise ValueError(
                "Yeterli item yok."
            )

        sell_price = int(
            item.get(
                "sell_price",
                0
            )
        )

        # Eğer sell_price verilmemişse
        # config içindeki sell_rate kullanılır.
        if sell_price <= 0:

            price = int(
                item.get(
                    "price",
                    0
                )
            )

            sell_rate = float(
                self.get_config().get(
                    "sell_rate",
                    0.50
                )
            )

            sell_price = int(
                price *
                sell_rate
            )

        total_price = (
            sell_price *
            quantity
        )

        self.remove_item(
            user_id,
            item_id,
            quantity
        )

        try:

            result = self.add_balance(
                user_id,
                total_price,
                transaction_type="shop_sell",
                source=item_id
            )

        except Exception:

            # Para eklenemezse itemi geri koy.
            self.add_item(
                user_id,
                item_id,
                quantity
            )

            raise

        return {
            "item": item,
            "quantity": quantity,
            "price": total_price,
            "balance": result["balance"]
        }

    # =========================================================
    # USE ITEM
    # =========================================================

    def use_item(
        self,
        user_id,
        item_id,
        quantity=1
    ):
        user_id = str(
            user_id
        )

        item_id = str(
            item_id
        )

        quantity = int(
            quantity
        )

        if quantity <= 0:
            raise ValueError(
                "Miktar 0'dan büyük olmalı."
            )

        item = self.get_item(
            item_id
        )

        if item is None:
            raise ValueError(
                "Item bulunamadı."
            )

        if not item.get(
            "usable",
            False
        ):
            raise ValueError(
                "Bu item kullanılamaz."
            )

        owned = self.get_item_quantity(
            user_id,
            item_id
        )

        if owned < quantity:
            raise ValueError(
                "Envanterinde yeterli item yok."
            )

        self.remove_item(
            user_id,
            item_id,
            quantity
        )

        return {
            "item": item,
            "quantity": quantity,
            "balance": self.get_balance(
                user_id
            )
        }

    # =========================================================
    # GIVE ITEM
    # =========================================================

    def give_item(
        self,
        sender_id,
        receiver_id,
        item_id,
        quantity=1
    ):
        sender_id = str(
            sender_id
        )

        receiver_id = str(
            receiver_id
        )

        item_id = str(
            item_id
        )

        quantity = int(
            quantity
        )

        if sender_id == receiver_id:
            raise ValueError(
                "Kendine item gönderemezsin."
            )

        if quantity <= 0:
            raise ValueError(
                "Miktar 0'dan büyük olmalı."
            )

        item = self.get_item(
            item_id
        )

        if item is None:
            raise ValueError(
                "Item bulunamadı."
            )

        if not item.get(
            "tradable",
            True
        ):
            raise ValueError(
                "Bu item takas edilemez."
            )

        owned = self.get_item_quantity(
            sender_id,
            item_id
        )

        if owned < quantity:
            raise ValueError(
                "Yeterli item yok."
            )

        self.remove_item(
            sender_id,
            item_id,
            quantity
        )

        try:

            self.add_item(
                receiver_id,
                item_id,
                quantity
            )

        except Exception:

            # Alıcıya eklenemezse
            # gönderenin itemini geri ver.
            self.add_item(
                sender_id,
                item_id,
                quantity
            )

            raise

        return {
            "item": item,
            "quantity": quantity,
            "sender_balance": self.get_balance(
                sender_id
            )
        }

    # =========================================================
    # LEADERBOARD
    # =========================================================

    def get_rich_leaderboard(self):

        users = self.get_all_users()

        leaderboard = []

        for user_id, user in users.items():

            cash = int(
                user.get(
                    "cash",
                    0
                )
            )

            bank = int(
                user.get(
                    "bank",
                    0
                )
            )

            total = cash + bank

            leaderboard.append({
                "user_id": str(
                    user_id
                ),
                "total": total
            })

        leaderboard.sort(
            key=lambda user: user["total"],
            reverse=True
        )

        return leaderboard

    def get_user_rank(
        self,
        user_id
    ):
        user_id = str(
            user_id
        )

        leaderboard = (
            self.get_rich_leaderboard()
        )

        for index, user in enumerate(
            leaderboard,
            start=1
        ):

            if user["user_id"] == user_id:
                return index

        return None

    def get_collectors_leaderboard(self):

        inventories = self._load_json(
            self.inventory_file,
            {}
        )

        if not isinstance(
            inventories,
            dict
        ):
            return []

        leaderboard = []

        for user_id, inventory in inventories.items():

            if not isinstance(
                inventory,
                dict
            ):
                continue

            total_items = sum(
                int(quantity)
                for quantity in inventory.values()
            )

            unique_items = len(
                inventory
            )

            leaderboard.append({
                "user_id": str(
                    user_id
                ),
                "items": total_items,
                "unique_items": unique_items
            })

        leaderboard.sort(
            key=lambda user: (
                user["unique_items"],
                user["items"]
            ),
            reverse=True
        )

        return leaderboard

    # =========================================================
    # YARDIMCI
    # =========================================================

    @staticmethod
    def format_time(
        seconds
    ):
        seconds = int(
            seconds
        )

        if seconds <= 0:
            return "hazır"

        days, seconds = divmod(
            seconds,
            86400
        )

        hours, seconds = divmod(
            seconds,
            3600
        )

        minutes, seconds = divmod(
            seconds,
            60
        )

        parts = []

        if days:
            parts.append(
                f"{days}g"
            )

        if hours:
            parts.append(
                f"{hours}s"
            )

        if minutes:
            parts.append(
                f"{minutes}dk"
            )

        if seconds and not days:
            parts.append(
                f"{seconds}sn"
            )

        if not parts:
            return "hazır"

        return " ".join(
            parts
        )