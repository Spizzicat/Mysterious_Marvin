import discord
from discord.ext import commands
from config import *
import os
import PIL as pil
import numpy as np
import requests
    
class Image(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nIMAGE COG READY")

    @commands.command(aliases=['autocrop','croptransparent'])
    async def crop(self, ctx):

        try:
            url = ctx.message.attachments[0].url
        except IndexError:
            return   

        with open(f'{DIR}/temp/cropped.png', 'wb') as f:
            f.write(requests.get(url).content)

        im = pil.Image.open(f'{DIR}/temp/cropped.png')

        if im.mode in ['RGBA', 'LA'] or im.mode == 'P' and 'transparency' in im.info:
            if bbox := im.convert('RGBA').split()[-1].getbbox():
                im = im.crop(bbox)

        im.save(f'{DIR}/temp/cropped.png', format='PNG')
        await ctx.send(file=discord.File(f'{DIR}/temp/cropped.png'))

async def setup(bot):
    await bot.add_cog(Image(bot))
