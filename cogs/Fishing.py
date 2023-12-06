import discord
from discord.ext import commands
from config import *
import os
    
class Fishing(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("\nFISHING COG READY")

async def setup(bot):
    await bot.add_cog(Fishing(bot))