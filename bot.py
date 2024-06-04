import asyncio
import os
import random
import sys
import discord
from discord.ext import commands
from termcolor import colored
import numpy as np
import requests
import random
from dotenv import load_dotenv

from constants import *
from helpers import *

with open(f'{DIR}/token.txt') as f:
    TOKEN = f.read()

LOGGING = True
DETECTING_SLURS = True
COG_NAMES = ['GeneralCog', 'EconomyCog', 'MathCog', 'FishingCog', 'AudioCog', 'ImageCog', 'HistoryCog']

# use the @commands.is_owner() decorator 
# ujson
# add csc sec cot

# use help_command = None to disable default help command
bot = commands.Bot(command_prefix = "m.", intents = discord.Intents.all(), help_command = None)

@bot.event
async def on_ready():
    print("\nBOT READY")
    command_sync = await bot.tree.sync()
    print(f"\nSYNCED {len(command_sync)} SLASH COMMANDS")

@bot.event
async def on_message(ctx : commands.Context):

    if ctx.author.bot:
        return

    msg_txt = ctx.content
    author = ctx.author
    channel = ctx.channel
    server = ctx.guild
    attachments = ctx.attachments
    mentions = ctx.mentions
    role_mentions = ctx.role_mentions
    channel_mentions = ctx.channel_mentions
    formatted_msg_txt = msg_txt

    # detects phrases
    if not msg_txt.startswith('m.'):
        strings = [x.lower().replace(' ','') for x in [msg_txt,author.display_name]]
        infractions = sum([string.count(word) for word in ZAMN_LIST for string in strings])
        if infractions > 0:
            asyncio.create_task(ctx.reply(" ".join(["ZAMN!" for x in range(infractions)])))
    
    for pair in [[SLUR_LIST, '😡'], [PEE_LIST, '🍺']]:
        if any(word in msg_txt.lower().replace(' ','') for word in [word.replace(' ','') for word in pair[0]]):
            await ctx.add_reaction(pair[1])

    # formats mentions in message correctly 
    for mention in mentions:
        formatted_msg_txt = formatted_msg_txt.replace(mention.mention,'@'+str(mention))
    for role_mention in role_mentions:
        formatted_msg_txt = formatted_msg_txt.replace(role_mention.mention,'@'+str(role_mention))
    for channel_mention in channel_mentions:
        formatted_msg_txt = formatted_msg_txt.replace(channel_mention.mention,'#'+str(channel_mention))

    # formats attachments
    if attachments:
        if msg_txt: f_att = ' '
        else: f_att = ''
        f_att += ' '.join([str(x) for x in attachments])
    else:
        f_att = ''

    # puts chat messages in terminal
    if LOGGING:
        print(
        '\n' +
        colored(f'\033[1m{author}\033[0m', 'light_green') +
        colored(f' said ', 'white') +
        colored(f'\033[1m{formatted_msg_txt}\033[0m','light_yellow') +
        colored(f'\033[1m{f_att}\033[0m', 'light_magenta') +
        colored(f' in the ', 'white') +
        colored(f'\033[1m#{channel}\033[0m', 'light_green') +
        colored(f' channel in ', 'white') +
        colored(f'\033[1m{server}.\033[0m', 'light_green') +
        '\n' +
        colored(f'Author: ','cyan') +
        colored(f'{author.id}        ','cyan') +
        colored(f'Channel: ','cyan') +
        colored(f'{channel.id}        ','cyan') +
        colored(f'Server: ','cyan') +
        colored(f'{server.id}','cyan') 
        )

    # blacklist
    # if ctx.author.id not in BANNED_USER_IDS:
    #     bot.process_commands(ctx)
    # else:
    #     await ctx.reply(random.choice(SLUR_LIST))

    await bot.process_commands(ctx)

@bot.event
async def on_command_error(ctx : commands.Context, error):
    print(error)
    await ctx.reply(error)

@bot.event
async def on_raw_reaction_add(reaction : discord.Reaction):
    if reaction.user_id == OWNER_ID and str(reaction.emoji) == '🔖':
        channel = bot.get_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)
        asyncio.create_task(msg.remove_reaction('🔖',reaction.member))
        files = []
        for attachment in msg.attachments:
            try:
                url = attachment.url
            except:
                print('could not get attachment')
                break
            else:
                with open(f'{DIR}/attachments/{attachment.filename}', 'wb') as f:
                    f.write(requests.get(url).content)
                    f.close
                files.append(discord.File(f'{DIR}/attachments/{attachment.filename}'))
        bookmarks = bot.get_channel(1093347898110005280)
        await bookmarks.send(content=msg.content,files=files)
        await bookmarks.send(content=f'<{msg.jump_url}>')

@bot.command(aliases=['rl'])
@commands.is_owner()
async def reload(ctx : commands.Context, cog : str = ''):
    cog = cog.lower().capitalize()
    if cog in COG_NAMES:
        await bot.unload_extension(f"cogs.{cog}")
        await bot.load_extension(f"cogs.{cog}")
        await ctx.reply(f"{cog} cog reloaded.")
    else:
        for cog in COG_NAMES:
            await bot.unload_extension(f"cogs.{cog}")
            await bot.load_extension(f"cogs.{cog}")
        await ctx.reply(f"All cogs reloaded.")

@bot.hybrid_command(
    name="help",
    description="get information about commands",
    hidden=False
)
async def help(ctx : commands.Context):
    print('someone used the help command')

async def load():
    for cog in COG_NAMES:
        await bot.load_extension('cogs.' + cog)

async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)

asyncio.run(main())