import discord
from discord.ext import commands
from config import *
import os
import PIL as pil
    
class Image(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nIMAGE COG READY")

    @commands.command()
    async def image(self, ctx):
        await ctx.reply('This command does not work yet.')

async def setup(bot):
    await bot.add_cog(Image(bot))