import discord
from discord.ext import commands
from bot import DIR
    
class FishingCog(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("\nFISHING COG READY")

async def setup(bot):
    await bot.add_cog(FishingCog(bot))