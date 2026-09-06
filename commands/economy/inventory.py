import discord
from discord.ext import commands
from utils.economy_manager import EconomyManager

economy = EconomyManager()

def setup(bot):
    @bot.command(name="inventory", aliases=["inv"])
    async def inventory_cmd(ctx, page: int = 1):
        inv = economy.get_inventory(ctx.author.id)
        entries = [(iid, qty) for iid, qty in inv.items() if int(qty) > 0]
        size = int(economy.get_config().get("inventory_page_size", 8))
        page = max(1, int(page))
        chunk = entries[(page-1)*size:page*size]
        if not chunk:
            return await ctx.send("🎒 Envanterin boş veya bu sayfada item yok.")
        embed = discord.Embed(title=f"🎒 {ctx.author.display_name} Envanteri", description=f"Sayfa **{page}**")
        for iid, qty in chunk:
            item = economy.get_item(iid)
            if item:
                embed.add_field(name=f"{item['emoji']} {item['name']}", value=f"x**{int(qty)}**\n`{iid}`", inline=True)
        await ctx.send(embed=embed)

    @bot.command(name="use")
    async def use(ctx, item_id: str = None, quantity: int = 1):
        if not item_id:
            return await ctx.send("❌ Kullanım: `!use item_id [miktar]`")
        try:
            r = economy.use_item(ctx.author.id, item_id, quantity)
            await ctx.send(f"✨ **{r['item']['name']}** x{r['quantity']} kullanıldı.")
        except ValueError as e:
            await ctx.send(f"❌ {e}")

    @bot.command(name="giveitem")
    async def giveitem(ctx, member: discord.Member = None, item_id: str = None, quantity: int = 1):
        if not member or not item_id:
            return await ctx.send("❌ Kullanım: `!giveitem @Kullanıcı item_id [miktar]`")
        if member.bot:
            return await ctx.send("❌ Bot hesaplarına item gönderemezsin.")
        try:
            r = economy.give_item(ctx.author.id, member.id, item_id, quantity)
            await ctx.send(f"🎁 {member.mention} kullanıcısına **{r['item']['name']} x{r['quantity']}** gönderildi.")
        except ValueError as e:
            await ctx.send(f"❌ {e}")
