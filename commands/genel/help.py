import discord


def setup(bot):
    @bot.tree.command(name="help", description="Shows all available commands.")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(title="📖 Command List", color=discord.Color.blurple())

        embed.add_field(
            name="🌐 Translation",
            value=(
                "`/translate-role` — Translate a single role's name\n"
                "`/translate-all-roles` — Translate all role names\n"
                "`/nuke-translate` — Reset channel and translate its messages"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Moderation",
            value=(
                "`/kick` `/ban` `/mute` `/unmute`\n"
                "`/warn` `/warnings` `/clearwarnings`\n"
                "`/purge` `/lock` `/unlock`\n"
                "`/criminal-record`"
            ),
            inline=False
        )

        embed.add_field(
            name="🏹 Hunter / Outlaw System",
            value=(
                "`/hunt-request` `/proof` `/give-award`\n"
                "`/leaderboard` `/status` `/history`\n"
                "`/set-role-icon` `/wanted-list` `/catch-wanted`"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Admin",
            value=(
                "`/reset-points` `/reset-user-points` `/rules`"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
