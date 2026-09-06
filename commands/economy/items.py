import discord
from discord.ext import commands
from utils.economy_manager import EconomyManager

economy = EconomyManager()

def admin(ctx):
    return ctx.author.guild_permissions.administrator

def setup(bot):
    @bot.group(name="item", invoke_without_command=True)
    async def item_group(ctx):
        if not admin(ctx):
            return await ctx.send("❌ Yönetici yetkisi gerekli.")
        await ctx.send("⚙️ `!item create id fiyat [satış] isim`\n`!item edit id alan değer`\n`!item delete id`\n`!item give @User id [miktar]`\n`!item take @User id [miktar]`")

    @item_group.command(name="create")
    async def item_create(ctx, item_id: str = None, price: int = None, sell_price: int = None, *, name: str = None):
        if not admin(ctx): return await ctx.send("❌ Yönetici yetkisi gerekli.")
        if not item_id or not name or price is None:
            return await ctx.send("❌ Kullanım: `!item create id fiyat [satış] isim`")
        try:
            r = economy.create_item(item_id, name, price=price, sell_price=sell_price if sell_price is not None else int(price * economy.get_config().get("sell_rate", .5)))
            await ctx.send(f"✅ Item oluşturuldu: **{r['name']}** (`{item_id}`)")
        except ValueError as e: await ctx.send(f"❌ {e}")

    @item_group.command(name="edit")
    async def item_edit(ctx, item_id: str = None, field: str = None, *, value: str = None):
        if not admin(ctx): return await ctx.send("❌ Yönetici yetkisi gerekli.")
        if not item_id or not field or value is None: return await ctx.send("❌ Kullanım: `!item edit id alan değer`")
        try:
            if field in {"price","sell_price"}: value = int(value)
            elif field in {"stackable","tradable","usable"}: value = value.lower() in {"true","1","yes","evet"}
            r = economy.edit_item(item_id, **{field: value})
            await ctx.send(f"✅ **{r['name']}** güncellendi.")
        except ValueError as e: await ctx.send(f"❌ {e}")

    @item_group.command(name="delete")
    async def item_delete(ctx, item_id: str = None):
        if not admin(ctx): return await ctx.send("❌ Yönetici yetkisi gerekli.")
        if not item_id: return await ctx.send("❌ Kullanım: `!item delete id`")
        try:
            r = economy.delete_item(item_id)
            await ctx.send(f"🗑️ **{r.get('name', item_id)}** silindi.")
        except ValueError as e: await ctx.send(f"❌ {e}")

    @item_group.command(name="give")
    async def item_give(ctx, member: discord.Member = None, item_id: str = None, quantity: int = 1):
        if not admin(ctx): return await ctx.send("❌ Yönetici yetkisi gerekli.")
        if not member or not item_id: return await ctx.send("❌ Kullanım: `!item give @User id [miktar]`")
        try:
            economy.add_item(member.id, item_id, quantity)
            await ctx.send(f"🎁 {member.mention} kullanıcısına item verildi.")
        except ValueError as e: await ctx.send(f"❌ {e}")

    @item_group.command(name="take")
    async def item_take(ctx, member: discord.Member = None, item_id: str = None, quantity: int = 1):
        if not admin(ctx): return await ctx.send("❌ Yönetici yetkisi gerekli.")
        if not member or not item_id: return await ctx.send("❌ Kullanım: `!item take @User id [miktar]`")
        try:
            economy.remove_item(member.id, item_id, quantity)
            await ctx.send(f"🗑️ {member.mention} kullanıcısından item alındı.")
        except ValueError as e: await ctx.send(f"❌ {e}")
