import discord
from discord import app_commands

from utils import state
from utils.unbelievaboat import add_cash


def setup(bot):
    @bot.tree.command(name="catch-wanted", description="Marks a wanted user as caught, rewards the catcher.")
    @app_commands.describe(target="Yakalanan Wanted kullanıcı", catcher="Yakalayan avcı (ödül parasını alacak kişi)")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def catch_wanted(interaction: discord.Interaction, target: discord.Member, catcher: discord.Member):
        if target.id not in state.wanted_data:
            await interaction.response.send_message(f"❌ **{target.display_name}** is not currently wanted.", ephemeral=True)
            return

        # API isteği (UnbelievaBoat) birkaç saniye sürebilir, Discord'un 3sn limitine takılmamak için erteliyoruz.
        await interaction.response.defer(thinking=True)

        bounty = state.wanted_data[target.id]["bounty"]

        # --- Ödül: bounty miktarını avcının UnbelievaBoat bakiyesine ekle ---
        ok, result = await add_cash(bot, interaction.guild.id, catcher.id, bounty)
        if not ok:
            await interaction.followup.send(
                f"{result}\n"
                f"⚠️ Ödül otomatik verilemedi, admin **{bounty} diamonds**'ı {catcher.mention}'a elle vermeli."
            )
            # Ödül verilemese bile yakalama işlemine devam ediyoruz, avın kaydı kaybolmasın.

        # --- Wanted rolü KALDIRILMIYOR (bounty avı sisteminin kendi kalıcı rozeti olarak kalsın) ---

        # --- Kafasındaki para (aktif bounty) sıfırlanıyor / av kaydı kapatılıyor ---
        del state.wanted_data[target.id]

        # --- sp (Outlaw Point) sabit miktar düşüyor ---
        penalty = bot.config.get("catch_wanted_sp_penalty", 5)
        state.outlaw_points[target.id] = max(0, state.outlaw_points[target.id] - penalty)

        result_text = (
            f"✅ **{target.display_name}** has been caught!\n"
            f"💰 Bounty was **{bounty} diamonds** — awarded to {catcher.mention}.\n"
            f"📉 {target.mention}'s Outlaw Points decreased by **{penalty}**.\n"
            f"🏷️ Wanted badge stays on their record."
        )
        await interaction.followup.send(result_text)

    @bot.tree.command(name="wanted-poster", description="Shows the wanted poster for a currently wanted user.")
    @app_commands.describe(target="Görüntülenecek Wanted kullanıcı")
    async def wanted_poster(interaction: discord.Interaction, target: discord.Member):
        data = state.wanted_data.get(target.id)
        if not data:
            await interaction.response.send_message(f"❌ **{target.display_name}** is not currently wanted.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🚨 WANTED",
            description=(
                f"**{target.display_name}**\n"
                f"Bounty: **{data['bounty']} diamonds**\n"
                f"Suç: *{data.get('crime', 'Bilinmeyen suç')}*"
            ),
            color=discord.Color.red(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)
