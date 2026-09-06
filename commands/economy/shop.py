import discord
from discord.ext import commands
from utils.economy_manager import EconomyManager

economy = EconomyManager()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Yardımcı fonksiyonlar
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_emoji(item: dict) -> str:
    name = item.get("emoji_name", "")
    eid  = item.get("emoji_id", "")
    if not name or not eid or str(eid).upper().startswith("BURAYA"):
        return ""
    try:
        return str(discord.PartialEmoji(name=str(name), id=int(eid)))
    except (ValueError, TypeError):
        return ""


def resolve_item(query: str) -> tuple:
    all_items   = economy.get_items()
    query_lower = query.lower().strip()
    partial_name  = None
    partial_alias = None

    for iid, data in all_items.items():
        if iid == query:
            return iid, data

        name_lower = data.get("name", "").lower()
        aliases    = [str(a).lower() for a in data.get("aliases", [])]

        if name_lower == query_lower:
            return iid, data

        if query_lower in aliases:
            return iid, data

        if partial_name is None and query_lower in name_lower:
            partial_name = (iid, data)

        if partial_alias is None:
            for alias in aliases:
                if query_lower in alias:
                    partial_alias = (iid, data)
                    break

    return partial_name or partial_alias or (None, None)


def parse_args(raw: str) -> tuple:
    parts = raw.rsplit(maxsplit=1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0].strip(), int(parts[1])
    return raw.strip(), 1


def get_item_name_from_id(guild: discord.Guild, role_id: str, fallback: str) -> str:
    all_items = economy.get_items()
    for data in all_items.values():
        actions = data.get("actions", [])
        if actions and actions[0].get("ids") and str(role_id) in actions[0]["ids"]:
            return data.get("name", fallback)
    return fallback


async def apply_item_roles(
    member: discord.Member,
    raw_item: dict,
    action: str = "buy",
) -> list:
    guild   = member.guild
    actions = raw_item.get("actions", [])
    reqs    = raw_item.get("requirements", [])
    logs    = []

    # ── Gereksinim kontrolü (sadece alımda) ──────────────────────────────
    if action == "buy":
        for req in reqs:
            for rid in req.get("ids", []):
                try:
                    role = guild.get_role(int(rid))
                except (ValueError, TypeError):
                    continue
                if role and role not in member.roles:
                    item_name = get_item_name_from_id(guild, rid, role.name)
                    raise ValueError(
                        f"Bu item'ı satın alabilmek için "
                        f"**{item_name}** rolüne sahip olman gerekiyor."
                    )

    def get_role(index) -> discord.Role | None:
        if index >= len(actions):
            return None
        ids = actions[index].get("ids", [])
        # Boş liste → None döner, hiçbir şey yapılmaz
        if not ids:
            return None
        try:
            return guild.get_role(int(ids[0]))
        except (ValueError, TypeError):
            return None

    if action == "buy":
        role_add = get_role(0)  # ver
        role_rem = get_role(1)  # al

        if role_add and role_add not in member.roles:
            await member.add_roles(
                role_add,
                reason=f"Shop › {raw_item.get('name')} [buy]",
            )
            logs.append(f"✅ **{role_add.name}** rolü verildi.")

        if role_rem and role_rem in member.roles:
            await member.remove_roles(
                role_rem,
                reason=f"Shop › {raw_item.get('name')} [buy]",
            )
            logs.append(f"🗑️ **{role_rem.name}** rolü alındı.")

    elif action == "sell":
        role_rem = get_role(0)  # satışta actions[0]'ı al
        role_add = get_role(1)  # satışta actions[1]'i ver (boşsa None gelir, işlem yapılmaz)

        if role_rem and role_rem in member.roles:
            await member.remove_roles(
                role_rem,
                reason=f"Shop › {raw_item.get('name')} [sell]",
            )
            logs.append(f"🗑️ **{role_rem.name}** rolü alındı.")

        if role_add and role_add not in member.roles:
            await member.add_roles(
                role_add,
                reason=f"Shop › {raw_item.get('name')} [sell]",
            )
            logs.append(f"✅ **{role_add.name}** rolü verildi.")

    return logs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Setup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup(bot):

    # ── !shop ──────────────────────────────────
    @bot.command(name="shop")
    async def shop_cmd(ctx, *, args: str = None):

        page = 1
        if args is not None:
            args = args.strip()
            if args.isdigit():
                page = int(args)
            else:
                return await ctx.send(
                    f"❌ `!shop` sadece sayfa numarası alır.\n"
                    f"Kullanım: `!shop [sayfa]`\n"
                    f"Item satın almak için: `!buy {args}`"
                )

        all_items = economy.get_items()
        if not all_items:
            return await ctx.send("🛒 Mağazada henüz hiç item yok.")

        items       = list(all_items.items())
        page_size   = int(economy.get_config().get("shop_page_size", 6))
        total_pages = max(1, (len(items) + page_size - 1) // page_size)
        page        = max(1, min(page, total_pages))
        start       = (page - 1) * page_size
        chunk       = items[start:start + page_size]

        embed = discord.Embed(
            title="🛒 Mağaza",
            description=f"Sayfa **{page} / {total_pages}**",
            color=discord.Color.gold(),
        )

        for _, raw_item in chunk:
            emoji       = build_emoji(raw_item)
            name        = raw_item.get("name") or "Bilinmeyen Item"
            description = raw_item.get("description") or "Açıklama yok."
            price       = max(0, int(raw_item.get("price", 0) or 0))
            stock_label = (
                "∞ Sınırsız"
                if raw_item.get("unlimited_stock")
                else f"{raw_item.get('stock_remaining', 0)} adet"
            )

            req_lines = []
            for req in raw_item.get("requirements", []):
                for rid in req.get("ids", []):
                    try:
                        role = ctx.guild.get_role(int(rid))
                        if role:
                            item_name = get_item_name_from_id(ctx.guild, rid, role.name)
                            req_lines.append(f"🔒 Gerekli: **{item_name}**")
                    except (ValueError, TypeError):
                        pass

            display_name = f"{emoji} {name}" if emoji else name
            value_parts  = [f"💎 **{price:,}** coin  •  📦 {stock_label}", description]
            if req_lines:
                value_parts.extend(req_lines)
            value_parts.append(f"`!buy {name}`")

            embed.add_field(
                name=display_name,
                value="\n".join(value_parts),
                inline=False,
            )

        footer = f"Toplam {len(items)} item  •  Sayfa {page}/{total_pages}"
        if page < total_pages:
            footer += f"  •  Sonraki: !shop {page + 1}"
        embed.set_footer(text=footer)

        await ctx.send(embed=embed)

    # ── !buy ───────────────────────────────────
    @bot.command(name="buy")
    async def buy_cmd(ctx, *, args: str = None):

        if not args:
            return await ctx.send(
                "❌ Kullanım: `!buy <item adı> [miktar]`\n"
                "Mağazayı görmek için: `!shop`"
            )

        query, quantity = parse_args(args)

        if quantity < 1:
            return await ctx.send("❌ Miktar en az **1** olmalıdır.")

        item_id, raw_item = resolve_item(query)
        if item_id is None:
            return await ctx.send(
                f"❌ **{query}** adında bir item bulunamadı.\n"
                f"Mağazayı görmek için `!shop` yazabilirsin."
            )

        # Stok kontrolü
        if (
            not raw_item.get("unlimited_stock")
            and int(raw_item.get("stock_remaining", 0)) < quantity
        ):
            return await ctx.send(
                f"❌ Yeterli stok yok. "
                f"Mevcut: **{raw_item.get('stock_remaining', 0)}** adet."
            )

        # Kullanıcı zaten bu role sahip mi?
        already_has_target = False
        try:
            if raw_item.get("actions") and len(raw_item["actions"]) > 0:
                for aid in raw_item["actions"][0].get("ids", []):
                    try:
                        role = ctx.guild.get_role(int(aid))
                        if role and role in ctx.author.roles:
                            already_has_target = True
                            break
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"[SHOP][buy] rol kontrol hatası: {e}")

        if already_has_target:
            return await ctx.send("❌ Bu role zaten sahipsin.")

        # Gereksinim kontrolü (para çekilmeden önce)
        for req in raw_item.get("requirements", []):
            for rid in req.get("ids", []):
                try:
                    role = ctx.guild.get_role(int(rid))
                except (ValueError, TypeError):
                    continue
                if role and role not in ctx.author.roles:
                    item_name = get_item_name_from_id(ctx.guild, rid, role.name)
                    return await ctx.send(
                        f"❌ Bu item'ı satın alabilmek için "
                        f"**{item_name}** rolüne sahip olman gerekiyor."
                    )

        try:
            result    = economy.buy_item(ctx.author.id, item_id, quantity)
            role_logs = await apply_item_roles(ctx.author, raw_item, action="buy")

        except ValueError as e:
            return await ctx.send(f"❌ {e}")
        except discord.Forbidden:
            return await ctx.send(
                "❌ Satın alma tamamlandı fakat rol atamak için yetkim yok.\n"
                "Lütfen bir yetkiliyle iletişime geç."
            )
        except Exception as e:
            print(f"[SHOP][buy] {type(e).__name__}: {e}")
            return await ctx.send("❌ Satın alma sırasında beklenmedik bir hata oluştu.")

        embed = discord.Embed(title="🛒 Satın Alma Başarılı", color=discord.Color.green())
        embed.add_field(
            name="Item",
            value=f"**{result['item']['name']}** x{result['quantity']}",
            inline=False,
        )
        embed.add_field(name="💸 Harcanan",     value=f"**{result['price']:,}** coin", inline=True)
        embed.add_field(name="💰 Kalan Bakiye", value=f"**{result['balance']:,}** coin", inline=True)
        if role_logs:
            embed.add_field(
                name="🎭 Rol Değişiklikleri",
                value="\n".join(role_logs),
                inline=False,
            )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    # ── !sell ──────────────────────────────────
    @bot.command(name="sell")
    async def sell_cmd(ctx, *, args: str = None):

        if not args:
            return await ctx.send(
                "❌ Kullanım: `!sell <item adı> [miktar]`\n"
                "Mağazayı görmek için: `!shop`"
            )

        query, quantity = parse_args(args)

        if quantity < 1:
            return await ctx.send("❌ Miktar en az **1** olmalıdır.")

        item_id, raw_item = resolve_item(query)
        if item_id is None:
            return await ctx.send(f"❌ **{query}** adında bir item bulunamadı.")

        if not raw_item.get("is_sellable", True):
            return await ctx.send("❌ Bu item satılamaz.")

        qty_owned = economy.get_item_quantity(ctx.author.id, item_id)
        if qty_owned < quantity:
            return await ctx.send(
                f"❌ Yeterli item yok. Envanterinde: **{qty_owned}** adet."
            )

        try:
            result    = economy.sell_item(ctx.author.id, item_id, quantity)
            role_logs = await apply_item_roles(ctx.author, raw_item, action="sell")

        except ValueError as e:
            return await ctx.send(f"❌ {e}")
        except discord.Forbidden:
            return await ctx.send(
                "❌ Satış tamamlandı fakat rolü güncellemek için yetkim yok."
            )
        except Exception as e:
            print(f"[SHOP][sell] {type(e).__name__}: {e}")
            return await ctx.send("❌ Satış sırasında beklenmedik bir hata oluştu.")

        embed = discord.Embed(title="💰 Satış Başarılı", color=discord.Color.blurple())
        embed.add_field(
            name="Item",
            value=f"**{result['item']['name']}** x{result['quantity']}",
            inline=False,
        )
        embed.add_field(name="💎 Kazanç",       value=f"**+{result['price']:,}** coin", inline=True)
        embed.add_field(name="💰 Kalan Bakiye", value=f"**{result['balance']:,}** coin", inline=True)
        if role_logs:
            embed.add_field(
                name="🎭 Rol Değişiklikleri",
                value="\n".join(role_logs),
                inline=False,
            )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)