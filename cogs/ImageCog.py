import discord
from discord.ext import commands
from config import *
import os
import PIL as pil
from PIL import Image
import numpy as np
import requests
    
class ImageCog(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nIMAGE COG READY")

    @commands.hybrid_command(
        name="crop",
        description="crop transparent border off of an image",
        aliases=['autocrop','croptransparent']
    )
    async def crop(self, ctx : commands.Context):

        try:
            url = ctx.message.attachments[0].url
        except IndexError:
            return   

        with open(f'{DIR}/temp/cropped.png', 'wb') as f:
            f.write(requests.get(url).content)

        im = Image.open(f'{DIR}/temp/cropped.png')

        if im.mode in ['RGBA', 'LA'] or im.mode == 'P' and 'transparency' in im.info:
            if bbox := im.convert('RGBA').split()[-1].getbbox():
                im = im.crop(bbox)

        im.save(f'{DIR}/temp/cropped.png', format='PNG')
        await ctx.send(file=discord.File(f'{DIR}/temp/cropped.png'))

    @commands.hybrid_command(
        name="vstack",
        description="vertically stack images",
    )
    async def vstack(self, ctx : commands.Context, backwards : bool = False):

        # does not handle non-image attachments
        try:
            urls = [a.url for a in ctx.message.attachments]
        except IndexError:
            return   
        
        num_ims = len(urls)
        if num_ims == 1:
            return
        
        for i in range(num_ims):
            with open(f'{DIR}/temp/vstack{i}.png', 'wb') as f:
                f.write(requests.get(urls[i]).content)

        if backwards:
            images = [Image.open(f'{DIR}/temp/vstack{i}.png') for i in range(num_ims - 1, -1, -1)]
        else:
            images = [Image.open(f'{DIR}/temp/vstack{i}.png') for i in range(num_ims)]

        new_width = max([im.width for im in images])
        new_height = 0
        resized_images = []

        for i, im in enumerate(images):
            old_width, old_height = im.size
            new_size = (new_width, old_height * new_width // old_width)
            new_height += new_size[1]
            resized = im.resize(new_size, Image.BICUBIC)
            resized_images.append(resized)

        result = Image.new('RGBA', (new_width, new_height))
        cur_y = 0

        for im in resized_images:
            result.paste(im, (0, cur_y))
            cur_y += im.size[1]

        result.save(f'{DIR}/temp/vstack.png', format='PNG')
        await ctx.send(file=discord.File(f'{DIR}/temp/vstack.png'))

    @commands.hybrid_command(
        name="hstack",
        description="horizontally stack images",
    )
    async def hstack(self, ctx : commands.Context, backwards : bool = False):

        # does not handle non-image attachments
        try:
            urls = [a.url for a in ctx.message.attachments]
        except IndexError:
            return   
        
        num_ims = len(urls)
        if num_ims == 1:
            return
        
        for i in range(num_ims):
            with open(f'{DIR}/temp/hstack{i}.png', 'wb') as f:
                f.write(requests.get(urls[i]).content)

        if backwards:
            images = [Image.open(f'{DIR}/temp/hstack{i}.png') for i in range(num_ims - 1, -1, -1)]
        else:
            images = [Image.open(f'{DIR}/temp/hstack{i}.png') for i in range(num_ims)]

        new_height = max([im.height for im in images])
        new_width = 0
        resized_images = []

        for i, im in enumerate(images):
            old_width, old_height = im.size
            new_size = (old_width * new_height // old_height, new_height)
            new_width += new_size[0]
            resized = im.resize(new_size, Image.BICUBIC)
            resized_images.append(resized)

        result = Image.new('RGBA', (new_width, new_height))
        cur_x = 0

        for im in resized_images:
            result.paste(im, (cur_x, 0))
            cur_x += im.size[0]

        result.save(f'{DIR}/temp/hstack.png', format='PNG')
        await ctx.send(file=discord.File(f'{DIR}/temp/hstack.png'))

async def setup(bot):
    await bot.add_cog(ImageCog(bot))
