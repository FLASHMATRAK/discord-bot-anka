import discord


def setup(bot):
    @bot.tree.command(name="rules", description="Shows the server rules.")
    async def rules(interaction: discord.Interaction):
        embed = discord.Embed(title="📜 Server Rules", color=discord.Color.red())
        rules_text = "\n".join(f"{i+1}. {r}" for i, r in enumerate(bot.config["server_rules"]))
        embed.description = rules_text
        await interaction.response.send_message(embed=embed)
