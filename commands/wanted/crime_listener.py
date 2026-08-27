import re
import random
import datetime
import discord
from utils import state

# UnbelievaBoat +crime embed renk kodları
SUCCESS_COLOR = 0x66bb6a  # başarılı suç
FAIL_COLOR = 0xef5350     # başarısız suç


def is_on_cooldown(bot, user_id):
    last = state.last_wanted_time.get(user_id)
    if not last:
        return False
    elapsed_minutes = (datetime.datetime.now() - last).total_seconds() / 60
    return elapsed_minutes < bot.config["wanted_cooldown_minutes"]


async def get_crime_command_user(message: discord.Message):
    # Yöntem 1: Slash komutsa interaction üzerinden kullanıcıyı buluyoruz
    if message.interaction_metadata is not None:
        return message.interaction_metadata.user

    # Yöntem 2: Mesaj bir reply ise orijinal mesajın yazarını alıyoruz
    if message.reference and message.reference.resolved:
        ref = message.reference.resolved
        if isinstance(ref, discord.Message):
            return ref.author

    # Yöntem 3: Embed/metin içinde mention arıyoruz (<@1234567890> formatı)
    text = message.content
    for embed in message.embeds:
        if embed.description:
            text += " " + embed.description
    match = re.search(r"<@!?(\d+)>", text)
    if match:
        user_id = int(match.group(1))
        return message.guild.get_member(user_id)

    return None


def setup(bot):
    """UnbelievaBoat +crime mesajlarını dinleyip Wanted sistemini tetikler. Komut değil, mesaj dinleyicisidir."""

    async def handle_crime_message(message: discord.Message):
        if message.author.id != bot.config["unbelievaboat_bot_id"]:
            return

        if not message.embeds:
            return

        embed_color = message.embeds[0].color
        if embed_color is None:
            return

        # Sadece başarılı suç rengiyle (#66bb6a) birebir eşleşiyorsa devam ediyoruz
        if embed_color.value != SUCCESS_COLOR:
            return  # başarısızsa (#ef5350) ya da başka bir renkse hiçbir şey yapmıyoruz

        user = await get_crime_command_user(message)
        if user is None:
            return

        diamond_channel = message.guild.get_channel(bot.config["diamond_grind_channel_id"])
        if not diamond_channel:
            return

        # Zaten Wanted ise: yeni Wanted olayı tetiklenmez, sadece mevcut ödül artar
        if user.id in state.wanted_data:
            increase = random.randint(bot.config["min_bounty"] // 2, bot.config["max_bounty"] // 2)
            state.wanted_data[user.id]["bounty"] += increase
            await diamond_channel.send(
                f"💰 {user.mention}, your bounty has increased to **{state.wanted_data[user.id]['bounty']} diamonds**!"
            )
            return

        # Cooldown süresindeyse yeni Wanted olayı tetiklenmez, şanslı sayılır
        if is_on_cooldown(bot, user.id):
            await diamond_channel.send(f"🍀 {user.mention}, you got lucky this time.")
            return

        # Şans faktörü - Wanted olma ya da olmama ihtimali
        if random.random() > bot.config["wanted_chance"]:
            await diamond_channel.send(f"🍀 {user.mention}, you got lucky this time.")
            return

        # Wanted ilan ediliyor
        bounty = random.randint(bot.config["min_bounty"], bot.config["max_bounty"])
        state.wanted_data[user.id] = {"bounty": bounty, "since": datetime.datetime.now()}
        state.last_wanted_time[user.id] = datetime.datetime.now()

        guild = message.guild
        wanted_role = discord.utils.get(guild.roles, name=bot.config["wanted_role_name"])
        if wanted_role:
            try:
                await user.add_roles(wanted_role)
            except discord.Forbidden:
                pass

        await diamond_channel.send(f"🚨 {user.mention}, a bounty of **{bounty} diamonds** has been placed on your head!")

        # Bounty duyuru kanalına bildirim
        announce_channel = guild.get_channel(bot.config["bounty_announce_channel_id"])
        if announce_channel:
            embed = discord.Embed(
                title="🚨 WANTED",
                description=f"{user.mention} — Bounty: **{bounty} diamonds**",
                color=discord.Color.red()
            )
            # Gerçek görsel URL'sini verdiğinde bu satırı aktif edeceğiz:
            # embed.set_image(url="GERÇEK_GORSEL_URL")
            embed.set_thumbnail(url=user.display_avatar.url)
            try:
                await announce_channel.send(embed=embed)
            except discord.Forbidden:
                pass

    bot.message_handlers.append(handle_crime_message)
