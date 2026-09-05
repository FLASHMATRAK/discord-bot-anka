import random

import discord
from discord.ext import commands

from utils.economy_manager import EconomyManager


economy = EconomyManager()


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def money(amount: int) -> str:
    return f"{amount:,}"


def remaining_text(seconds: int) -> str:
    return economy.format_time(seconds)


# ============================================================
# GÜVENLİ İŞLER
# ============================================================

WORK_JOBS = [
    "Brawl Stars koçluğu",
    "Discord moderasyonu",
    "Video düzenleme",
    "Kodlama",
    "Grafik tasarımı",
    "Sunucu düzenleme",
    "Harita tasarımı",
    "Topluluk yönetimi"
]


# ============================================================
# BALANCE
# ============================================================

def setup(bot):

    @bot.command(
        name="balance",
        aliases=["bal", "bakiye"]
    )
    async def balance(ctx, member: discord.Member = None):
        member = member or ctx.author

        amount = economy.get_balance(member.id)

        await ctx.send(
            f"💎 **{member.display_name} Bakiye:** "
            f"{money(amount)} Elmas"
        )


    # ========================================================
    # DAILY
    # ========================================================

    @bot.command(name="daily")
    async def daily(ctx):
        try:
            result = economy.claim_daily(ctx.author.id)

            await ctx.send(
                f"🎁 **Günlük ödülünü aldın!**\n"
                f"💎 +{money(result['reward'])} Elmas\n"
                f"💰 Yeni bakiye: **{money(result['balance'])} Elmas**"
            )

        except ValueError as e:
            await ctx.send(f"⏳ {e}")


    # ========================================================
    # WORK
    # ========================================================

    @bot.command(name="work")
    async def work(ctx):
        try:
            result = economy.do_work(ctx.author.id)

            job = random.choice(WORK_JOBS)

            await ctx.send(
                f"🛠️ **{job} yaptın!**\n"
                f"💎 +{money(result['reward'])} Elmas\n"
                f"💰 Yeni bakiye: **{money(result['balance'])} Elmas**"
            )

        except ValueError as e:
            await ctx.send(f"⏳ {e}")


    # ========================================================
    # CRIME
    # ========================================================

    @bot.command(name="crime")
    async def crime(ctx):
        try:
            result = economy.do_crime(ctx.author.id)

            event = result["event"]

            embed = discord.Embed(
                title=f"🌑 {event['name']}",
                description=event["description"]
            )

            embed.add_field(
                name="⚠️ Risk",
                value=f"**{result['risk']}%**",
                inline=True
            )

            if result["success"]:

                embed.add_field(
                    name="✅ Sonuç",
                    value=(
                        f"Başarılı!\n"
                        f"💎 **+{money(result['reward'])} Elmas**"
                    ),
                    inline=True
                )

                if result["wanted"]:
                    embed.add_field(
                        name="🚨 Aranıyorsun!",
                        value=(
                            "Başarılı olsan da dikkat çektin.\n"
                            "Wanted durumuna girdin."
                        ),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🕶️ Dikkat çekmedin",
                        value="Wanted durumuna girmedin.",
                        inline=False
                    )

            else:

                loss = result["loss"]

                if loss > 0:
                    loss_text = f"💸 **-{money(loss)} Elmas**"
                else:
                    loss_text = "💸 Para kaybetmedin."

                embed.add_field(
                    name="❌ Sonuç",
                    value=(
                        f"Görev başarısız oldu.\n"
                        f"{loss_text}"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="🛑 Wanted",
                    value="Başarısız olduğun için wanted kontrolü yapılmadı.",
                    inline=False
                )

            embed.add_field(
                name="💰 Bakiye",
                value=f"{money(result['balance'])} Elmas",
                inline=False
            )

            await ctx.send(embed=embed)

        except ValueError as e:
            await ctx.send(f"⏳ {e}")


    # ========================================================
    # GIVE
    # ========================================================

    @bot.command(name="give")
    async def give(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if member is None or amount is None:
            await ctx.send(
                "❌ Kullanım: `!give @Kullanıcı miktar`"
            )
            return

        if member.id == ctx.author.id:
            await ctx.send(
                "❌ Kendine Elmas gönderemezsin."
            )
            return

        if member.bot:
            await ctx.send(
                "❌ Bot hesaplarına Elmas gönderemezsin."
            )
            return

        if amount <= 0:
            await ctx.send(
                "❌ Miktar 0'dan büyük olmalı."
            )
            return

        try:
            result = economy.transfer(
                ctx.author.id,
                member.id,
                amount
            )

            await ctx.send(
                f"💸 **Transfer başarılı!**\n"
                f"👤 {member.mention} → "
                f"**+{money(amount)} Elmas**\n"
                f"💰 Yeni bakiyen: "
                f"**{money(result['sender_balance'])} Elmas**"
            )

        except ValueError as e:
            await ctx.send(f"❌ {e}")


    # ========================================================
    # ECONOMY ADMIN KOMUTLARI
    # ========================================================

    @bot.group(
        name="economy",
        invoke_without_command=True
    )
    async def economy_command(ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "❌ Bu komut sadece yöneticiler içindir."
            )
            return

        await ctx.send(
            "💎 **Ekonomi Yönetimi**\n\n"
            "`!economy give @User miktar`\n"
            "`!economy take @User miktar`\n"
            "`!economy set @User miktar`\n"
            "`!economy reset @User`"
        )


    # ========================================================
    # ECONOMY GIVE
    # ========================================================

    @economy_command.command(name="give")
    async def economy_give(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "❌ Bu komut sadece yöneticiler içindir."
            )
            return

        if member is None or amount is None:
            await ctx.send(
                "❌ Kullanım: `!economy give @User miktar`"
            )
            return

        if amount <= 0:
            await ctx.send(
                "❌ Miktar 0'dan büyük olmalı."
            )
            return

        result = economy.add_balance(
            member.id,
            amount,
            transaction_type="admin_give",
            source=f"admin:{ctx.author.id}"
        )

        await ctx.send(
            f"💎 {member.mention} hesabına "
            f"**+{money(amount)} Elmas** eklendi.\n"
            f"💰 Yeni bakiye: "
            f"**{money(result['balance'])} Elmas**"
        )


    # ========================================================
    # ECONOMY TAKE
    # ========================================================

    @economy_command.command(name="take")
    async def economy_take(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "❌ Bu komut sadece yöneticiler içindir."
            )
            return

        if member is None or amount is None:
            await ctx.send(
                "❌ Kullanım: `!economy take @User miktar`"
            )
            return

        if amount <= 0:
            await ctx.send(
                "❌ Miktar 0'dan büyük olmalı."
            )
            return

        try:
            result = economy.remove_balance(
                member.id,
                amount,
                transaction_type="admin_take",
                source=f"admin:{ctx.author.id}"
            )

            await ctx.send(
                f"💸 {member.mention} hesabından "
                f"**-{money(amount)} Elmas** alındı.\n"
                f"💰 Yeni bakiye: "
                f"**{money(result['balance'])} Elmas**"
            )

        except ValueError as e:
            await ctx.send(f"❌ {e}")


    # ========================================================
    # ECONOMY SET
    # ========================================================

    @economy_command.command(name="set")
    async def economy_set(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "❌ Bu komut sadece yöneticiler içindir."
            )
            return

        if member is None or amount is None:
            await ctx.send(
                "❌ Kullanım: `!economy set @User miktar`"
            )
            return

        if amount < 0:
            await ctx.send(
                "❌ Bakiye negatif olamaz."
            )
            return

        result = economy.set_balance(
            member.id,
            amount,
            source=f"admin:{ctx.author.id}"
        )

        await ctx.send(
            f"⚙️ {member.mention} bakiyesi "
            f"**{money(amount)} Elmas** olarak ayarlandı."
        )


    # ========================================================
    # ECONOMY RESET
    # ========================================================

    @economy_command.command(name="reset")
    async def economy_reset(
        ctx,
        member: discord.Member = None
    ):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "❌ Bu komut sadece yöneticiler içindir."
            )
            return

        if member is None:
            await ctx.send(
                "❌ Kullanım: `!economy reset @User`"
            )
            return

        config = economy.get_config()

        starting_balance = int(
            config.get("starting_balance", 100)
        )

        economy.set_balance(
            member.id,
            starting_balance,
            source=f"admin_reset:{ctx.author.id}"
        )

        await ctx.send(
            f"🔄 {member.mention} ekonomi hesabı sıfırlandı.\n"
            f"💎 Başlangıç bakiyesi: "
            f"**{money(starting_balance)} Elmas**"
        )