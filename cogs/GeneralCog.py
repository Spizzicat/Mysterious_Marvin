import discord
from discord.ext import commands
import os
import requests
from send2trash import send2trash
import numpy as np
from helpers import get_relevant_attachment_url
from constants import DIR

# the manga commands take in mangadex IDs which you can find in the URLs of the mangas and chapters

async def send_chapter(ctx : commands.Context, chapter_id : str, chapter_number : int = None):

    # get chapter data
    chapter_response = requests.get(url=f"https://api.mangadex.org/at-home/server/{chapter_id}")
    if chapter_response.status_code != 200: 
        print('Status:', chapter_response.status_code, 'Problem with the request!')
    data = chapter_response.json()

    # create list of the filenames of the chapter images
    img_filenames = [s for s in data['chapter']['data']]
    
    # partition filenames into groups of 10
    img_filename_groups = [img_filenames[i : i + 10] for i in range(0, len(img_filenames), 10)]

    # send chapter number if appropriate 
    # idk how to the chapter number from just the chapter id
    if chapter_number:
        await ctx.send(content=f"Chapter {float(chapter_number):g}")
        
    # loop through list of image filename groups
    for g, group in enumerate(img_filename_groups):
        
        # loop through image filename group
        for f, filename in enumerate(group):
            
            with open(f'{DIR}/temp/manga/{f}.jpg', 'wb') as f:
                image_response = requests.get(url=f"https://uploads.mangadex.org/data/{data['chapter']['hash']}/{filename}")
                if image_response.status_code != 200: 
                    print('Status:', image_response.status_code, 'Problem with the request!')
                f.write(image_response.content)
            
        # send files
        await ctx.send(content='',files=[discord.File(fp=f"{DIR}/temp/manga/{i}.jpg",filename=f"{1+i+g*10}.jpg") for i in range(len(os.listdir(f'{DIR}/temp/manga')))])
        
        # clear manga folder
        for file in os.listdir(f'{DIR}/temp/manga'):
            # DANGEROUS!
            os.remove(f'{DIR}/temp/manga/{file}')  

async def send_manga(ctx : commands.Context, manga_id : str):

    # search_term = ' '.join(args).strip()
    
    # note: change this to remove duplicates or add scanlation groups

    response_list = []
    chapters_with_ids = []

    # create list of responses
    for i in range(8):
        manga_response = requests.get(url=f"https://api.mangadex.org/manga/{manga_id}/feed?limit=100&offset={100*i}")
        if manga_response.status_code != 200:
            print('Status:', manga_response.status_code, 'Problem with the request!')
        response_list.append(manga_response.json())

    # create list of chapter ids
    for response in response_list:
        for c in response['data']:
            if c['attributes']['translatedLanguage'] == 'en' and not c['attributes']['externalUrl']:
                chapters_with_ids.append( (c['id'], float(c['attributes']['chapter'])) )

    # sorts by chapter number
    chapters_with_ids.sort(key=lambda x: x[1])
    
    # loop through list of chapter ids
    for chapter_id, chapter_number in chapters_with_ids:
        
        # send chapter
        await send_chapter(ctx, chapter_id, chapter_number)
    
class GeneralCog(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("\nGENERAL COG READY")

    @commands.hybrid_command(
        name="ping",
        description="ping the bot",
        aliases=['latency']
    )
    async def ping(self, ctx):
        await ctx.reply(str(str(round(self.bot.latency*1000,1))+" ms"))

    @commands.hybrid_command(
        name="oingo",
        description="boingo",
    )
    async def oingo(self, ctx):
        await ctx.reply("boingo")

    @commands.hybrid_command(
        name="boingo",
        description="oingo",
    )
    async def boingo(self, ctx):
        await ctx.reply("oingo")

    @commands.hybrid_command(
        name="zamn",
        description="ZAMN!",
    ) 
    async def zamn(self, ctx):
        await ctx.send("ZAMN!")

    @commands.hybrid_command(
        name="marvin",
        description="send an image of marvin",
    ) 
    async def marvin(self, ctx):
        await ctx.send(file=discord.File(f'{DIR}/data/images/marvin.png'))

    @commands.hybrid_command(
        name="ball",
        description="send an image of a ball",
    ) 
    async def ball(self, ctx):
        await ctx.send(file=discord.File(f'{DIR}/data/images/ball.png'))

    @commands.hybrid_command(
        name="balls",
        description="send an image of balls",
    ) 
    async def balls(self, ctx):
        await ctx.send(files=[discord.File(f'{DIR}/data/images/ball.png') for i in range(2)])

    @commands.command(
        name="say",
        description="say a message",
        hidden=True
    ) 
    @commands.is_owner()
    async def say(self, ctx : commands.Context, message : str = None, channel_id : int = None):

        channel = ctx.channel if not channel_id else self.bot.get_channel(channel_id)
        
        files = []
        for index,attachment in enumerate(ctx.message.attachments):
            file = await attachment.to_file(filename=f'attachment{index+1}.png')
            files.append(file)

        await channel.send(content=message,files=files)

    @commands.hybrid_command(
        name="chapter",
        description="send a manga chapter",
    ) 
    async def chapter(self, ctx : commands.Context, mangadex_chapter_id=None):
        if mangadex_chapter_id:
            await send_chapter(ctx,mangadex_chapter_id)

    @commands.hybrid_command(
        name="manga",
        description="send a manga",
        hidden=True
    ) 
    @commands.is_owner()
    async def manga(self, ctx : commands.Context, mangadex_manga_id):
        if mangadex_manga_id:
            await send_manga(ctx, mangadex_manga_id)

    @commands.hybrid_command(
        name="sbr",
        description="send steel ball run",
        hidden=True
    ) 
    @commands.is_owner()
    async def steelballrun(self, ctx : commands.Context):
        await send_manga(ctx,'1044287a-73df-48d0-b0b2-5327f32dd651')

    @commands.command(
        name="pingkneecap",
        description="ghost ping kneecap",
        hidden=True,
        aliases=['atkneecap']
    )
    async def pingkneecap(self, ctx):
        await ctx.message.delete()
        await ctx.send(f'<@{114112473430360070}>', delete_after=0)

    @commands.command(
        name="pingflashlight",
        description="ghost ping flashlight",
        hidden=True,
        aliases=['atflashlight','atezo','atezogaming']
    )
    async def pingflashlight(self, ctx : commands.Context):
        await ctx.message.delete()
        await ctx.send(f'<@{158418656861093888}>', delete_after=0)

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))