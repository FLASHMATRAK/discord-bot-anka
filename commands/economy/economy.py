import random
import discord
from discord.ext import commands
from utils.economy_manager import EconomyManager

economy = EconomyManager()

WORK_JOBS = [
    "Brawl Stars koçluğu", "Discord moderasyonu", "Video düzenleme",
    "Kodlama", "Grafik tasarımı", "Sunucu düzenleme",
    "Harita tasarımı", "Topluluk yönetimi",
]


def money(amount):
    return f"{int(amount):,}"


def setup(bot):

    @bot.command(name="balance", aliases=["bal", "bakiye"])
    async def balance(ctx, member: discord.Member = None):
        member = member or ctx.author
        symbol = economy.currency_symbol()
        name = economy.currency_name()

        await ctx.send(
            f"{symbol} **{member.display_name} Bakiye:** "
            f"{money(economy.get_balance(member.id))} {name}"
        )


    @bot.command(name="daily")
    async def daily(ctx):
        try:
            r = economy.claim_daily(ctx.author.id)

            await ctx.send(
                f"🎁 **Günlük ödülünü aldın!**\n"
                f"{economy.currency_symbol()} "
                f"+{money(r['reward'])} {economy.currency_name()}\n"
                f"💰 Yeni bakiye: "
                f"**{money(r['balance'])} {economy.currency_name()}**"
            )

        except ValueError as e:
            await ctx.send(f"⏳ {e}")


    @bot.command(name="work")
    async def work(ctx):
        try:
            r = economy.do_work(ctx.author.id)
            job = random.choice(WORK_JOBS)

            await ctx.send(
                f"🛠️ **{job} yaptın!**\n"
                f"{economy.currency_symbol()} "
                f"+{money(r['reward'])} {economy.currency_name()}\n"
                f"💰 Yeni bakiye: "
                f"**{money(r['balance'])} {economy.currency_name()}**"
            )

        except ValueError as e:
            await ctx.send(f"⏳ {e}")


    @bot.command(name="crime")
    async def crime(ctx):
        try:
            r = economy.do_crime(ctx.author.id)
            e = r["event"]

            embed = discord.Embed(
                title=f"🌑 {e['name']}",
                description=e.get("description", "")
            )

            embed.add_field(
                name="⚠️ Risk",
                value=f"**{r['risk']}%**",
                inline=True
            )

            if r["success"]:

                embed.add_field(
                    name="✅ Sonuç",
                    value=(
                        f"Başarılı!\n"
                        f"{economy.currency_symbol()} "
                        f"**+{money(r['reward'])} "
                        f"{economy.currency_name()}**"
                    ),
                    inline=True
                )

                if r["wanted"]:

                    # ==========================================
                    # OUTLAW ROLÜ VER
                    # ==========================================

                    OUTLAW_ROLE_ID = 1533075067355926730

                    outlaw_role = ctx.guild.get_role(OUTLAW_ROLE_ID)

                    if outlaw_role is None:
                        print(
                            f"[CRIME] {ctx.guild.name} sunucusunda "
                            f"'outlaw' rolü bulunamadı."
                        )

                        role_message = (
                            "🚨 **Wanted oldun!**\n"
                            "Ancak `outlaw` rolü bulunamadığı için "
                            "rol verilemedi."
                        )

                    else:

                        if outlaw_role not in ctx.author.roles:

                            try:
                                await ctx.author.add_roles(
                                    outlaw_role,
                                    reason="Crime sonucu wanted oldu."
                                )

                                role_message = (
                                    "🚨 **Aranıyorsun!**\n"
                                    "Başarılı oldun fakat dikkat çektin.\n"
                                    f"🔴 {outlaw_role.mention} rolü verildi."
                                )

                            except discord.Forbidden:
                                print(
                                    "[CRIME] Outlaw rolü verilemedi. "
                                    "Botun 'Rolleri Yönet' yetkisini ve "
                                    "rol hiyerarşisini kontrol et."
                                )

                                role_message = (
                                    "🚨 **Aranıyorsun!**\n"
                                    "Başarılı oldun fakat dikkat çektin.\n"
                                    "❌ `outlaw` rolü verilemedi."
                                )

                            except discord.HTTPException as error:
                                print(
                                    f"[CRIME] Rol verme Discord hatası: "
                                    f"{error}"
                                )

                                role_message = (
                                    "🚨 **Aranıyorsun!**\n"
                                    "❌ `outlaw` rolü verilirken hata oluştu."
                                )

                        else:
                            role_message = (
                                "🚨 **Aranıyorsun!**\n"
                                "Başarılı oldun fakat dikkat çektin.\n"
                                f"🔴 Zaten {outlaw_role.mention} rolüne sahipsin."
                            )

                    embed.add_field(
                        name="🚨 Wanted!",
                        value=role_message,
                        inline=False
                    )

                else:

                    embed.add_field(
                        name="🕶️ Dikkat çekmedin",
                        value="Wanted durumuna girmedin.",
                        inline=False
                    )

            else:

                loss = r["loss"]

                if loss:
                    result_text = (
                        f"Başarısız oldu.\n"
                        f"💸 **-{money(loss)} "
                        f"{economy.currency_name()}**"
                    )
                else:
                    result_text = (
                        "Başarısız oldu.\n"
                        "💸 Para kaybetmedin."
                    )

                embed.add_field(
                    name="❌ Sonuç",
                    value=result_text,
                    inline=False
                )

                embed.add_field(
                    name="🛑 Wanted",
                    value=(
                        "Başarısız olduğun için "
                        "wanted kontrolü yapılmadı."
                    ),
                    inline=False
                )

            embed.add_field(
                name="💰 Bakiye",
                value=(
                    f"**{money(r['balance'])} "
                    f"{economy.currency_name()}**"
                ),
                inline=False
            )

            await ctx.send(embed=embed)

        except ValueError as e:
            await ctx.send(f"⏳ {e}")


    @bot.command(name="give")
    async def give(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if member is None or amount is None:
            return await ctx.send(
                "❌ Kullanım: `!give @Kullanıcı miktar`"
            )

        if member.id == ctx.author.id or member.bot:
            return await ctx.send(
                "❌ Geçersiz kullanıcı."
            )

        try:
            r = economy.transfer(
                ctx.author.id,
                member.id,
                amount
            )

            await ctx.send(
                f"💸 **Transfer başarılı!**\n"
                f"👤 {member.mention} → "
                f"**+{money(amount)} {economy.currency_name()}**\n"
                f"💰 Yeni bakiyen: "
                f"**{money(r['sender_balance'])} "
                f"{economy.currency_name()}**"
            )

        except ValueError as e:
            await ctx.send(f"❌ {e}")


    @bot.group(name="economy", invoke_without_command=True)
    async def economy_command(ctx):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                "❌ Bu komut sadece yöneticiler içindir."
            )

        await ctx.send(
            "⚙️ `!economy give @User miktar`\n"
            "`!economy take @User miktar`\n"
            "`!economy set @User miktar`\n"
            "`!economy reset @User`"
        )


    @economy_command.command(name="give")
    async def economy_give(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                "❌ Yönetici yetkisi gerekli."
            )

        if member is None or amount is None or amount <= 0:
            return await ctx.send(
                "❌ Kullanım: `!economy give @User miktar`"
            )

        r = economy.add_balance(
            member.id,
            amount,
            "admin_give",
            f"admin:{ctx.author.id}"
        )

        await ctx.send(
            f"💎 {member.mention} hesabına "
            f"**+{money(amount)}** eklendi. "
            f"Yeni bakiye: **{money(r['balance'])}**"
        )


    @economy_command.command(name="take")
    async def economy_take(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                "❌ Yönetici yetkisi gerekli."
            )

        if member is None or amount is None or amount <= 0:
            return await ctx.send(
                "❌ Kullanım: `!economy take @User miktar`"
            )

        try:
            r = economy.remove_balance(
                member.id,
                amount,
                "admin_take",
                f"admin:{ctx.author.id}"
            )

            await ctx.send(
                f"💸 {member.mention} hesabından "
                f"**-{money(amount)}** alındı. "
                f"Yeni bakiye: **{money(r['balance'])}**"
            )

        except ValueError as e:
            await ctx.send(f"❌ {e}")


    @economy_command.command(name="set")
    async def economy_set(
        ctx,
        member: discord.Member = None,
        amount: int = None
    ):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                "❌ Yönetici yetkisi gerekli."
            )

        if member is None or amount is None or amount < 0:
            return await ctx.send(
                "❌ Kullanım: `!economy set @User miktar`"
            )

        economy.set_balance(
            member.id,
            amount,
            f"admin:{ctx.author.id}"
        )

        await ctx.send(
            f"⚙️ {member.mention} bakiyesi "
            f"**{money(amount)}** olarak ayarlandı."
        )


    @economy_command.command(name="reset")
    async def economy_reset(
        ctx,
        member: discord.Member = None
    ):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                "❌ Yönetici yetkisi gerekli."
            )

        if member is None:
            return await ctx.send(
                "❌ Kullanım: `!economy reset @User`"
            )

        start = int(
            economy.get_config().get(
                "starting_balance",
                100
            )
        )

        economy.set_balance(
            member.id,
            start,
            f"admin_reset:{ctx.author.id}"
        )

        await ctx.send(
            f"🔄 {member.mention} sıfırlandı. "
            f"Başlangıç bakiyesi: **{money(start)}**"
        )