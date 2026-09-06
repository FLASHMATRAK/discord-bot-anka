import discord
from discord import app_commands

from utils import state
from utils.economy_manager import EconomyManager


economy = EconomyManager()


def setup(bot):

    # ── /catch-wanted ──────────────────────────────────────────────────────
    @bot.tree.command(
        name="catch-wanted",
        description="Wanted kullanıcıyı yakala, avcıya ödülü ver.",
    )
    @app_commands.describe(
        target="Yakalanan wanted kullanıcı",
        catcher="Yakalayan avcı (ödülü alacak kişi)",
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def catch_wanted(
        interaction: discord.Interaction,
        target: discord.Member,
        catcher: discord.Member,
    ):
        # Kullanıcı wanted listesinde mi?
        if target.id not in state.wanted_data:
            await interaction.response.send_message(
                f"❌ **{target.display_name}** şu an wanted listesinde değil.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)

        # Wanted bilgilerini al
        wanted_info = state.wanted_data[target.id]

        bounty = int(wanted_info.get("bounty", 0))
        crime = wanted_info.get(
            "crime",
            "Bilinmeyen suç"
        )

        # ── Ödülü avcıya ver ──────────────────────────────────────────────
        try:
            result = economy.add_balance(
                catcher.id,
                bounty,
                "catch_wanted_reward",
                f"catch_wanted:{target.id}"
            )

            reward_text = (
                f"{economy.currency_symbol()} **{bounty:,}** "
                f"{economy.currency_name()} "
                f"ödül {catcher.mention}'a verildi.\n"
                f"Yeni bakiye: **{result['balance']:,}** "
                f"{economy.currency_name()}"
            )

        except ValueError as error:
            await interaction.followup.send(
                f"⚠️ Ödül verilemedi: {error}\n"
                f"Wanted kaydı silinmedi.",
                ephemeral=True,
            )
            return

        except Exception as error:
            print(
                f"[CATCH-WANTED] Ödül verme hatası: {error}"
            )

            await interaction.followup.send(
                "❌ Ödül verilirken beklenmeyen bir hata oluştu.\n"
                "Wanted kaydı silinmedi.",
                ephemeral=True,
            )
            return

        # ── Av kaydını kapat ──────────────────────────────────────────────
        del state.wanted_data[target.id]

        # ── Outlaw Point düş ──────────────────────────────────────────────
        penalty = bot.config.get(
            "catch_wanted_sp_penalty",
            5
        )

        current = state.outlaw_points.get(
            target.id,
            0
        )

        state.outlaw_points[target.id] = max(
            0,
            current - penalty
        )

        # ── Sonuç mesajı ─────────────────────────────────────────────────
        embed = discord.Embed(
            title="✅ Yakalandı!",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="Kullanıcı",
            value=target.mention,
            inline=True,
        )

        embed.add_field(
            name="Avcı",
            value=catcher.mention,
            inline=True,
        )

        embed.add_field(
            name="Suç",
            value=f"_{crime}_",
            inline=False,
        )

        embed.add_field(
            name="Ödül",
            value=reward_text,
            inline=False,
        )

        embed.add_field(
            name="📉 Outlaw Point",
            value=(
                f"{target.display_name} "
                f"**{penalty}** OP kaybetti."
            ),
            inline=False,
        )

        embed.add_field(
            name="🏷️ Wanted Rozeti",
            value=(
                "Rozet kayıt olarak üzerinde "
                "kalmaya devam ediyor."
            ),
            inline=False,
        )

        embed.set_thumbnail(
            url=target.display_avatar.url
        )

        await interaction.followup.send(
            embed=embed
        )

    # ── /wanted-poster ────────────────────────────────────────────────────
    @bot.tree.command(
        name="wanted-poster",
        description="Wanted kullanıcının afişini gösterir.",
    )
    @app_commands.describe(
        target="Görüntülenecek wanted kullanıcı"
    )
    async def wanted_poster(
        interaction: discord.Interaction,
        target: discord.Member,
    ):
        data = state.wanted_data.get(target.id)

        if not data:
            await interaction.response.send_message(
                f"❌ **{target.display_name}** "
                f"şu an wanted listesinde değil.",
                ephemeral=True,
            )
            return

        bounty = int(data.get("bounty", 0))
        crime = data.get(
            "crime",
            "Bilinmeyen suç"
        )

        embed = discord.Embed(
            title="🚨 WANTED",
            description=(
                f"**{target.display_name}**\n\n"
                f"{economy.currency_symbol()} "
                f"Ödül: **{bounty:,} "
                f"{economy.currency_name()}**\n"
                f"⚖️ Suç: _{crime}_"
            ),
            color=discord.Color.red(),
        )

        embed.set_thumbnail(
            url=target.display_avatar.url
        )

        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url,
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ── Hata yakalayıcı ──────────────────────────────────────────────────
    @catch_wanted.error
    async def catch_wanted_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        if isinstance(
            error,
            app_commands.MissingPermissions
        ):
            message = (
                "❌ Bu komutu kullanmak için "
                "**Üyeleri Yönet** yetkisine sahip olman gerekiyor."
            )

            if interaction.response.is_done():
                await interaction.followup.send(
                    message,
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    message,
                    ephemeral=True,
                )

        else:
            print(
                f"[CATCH-WANTED] Hata: {error}"
            )

            message = (
                f"❌ Beklenmedik bir hata oluştu: `{error}`"
            )

            if interaction.response.is_done():
                await interaction.followup.send(
                    message,
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    message,
                    ephemeral=True,
                )