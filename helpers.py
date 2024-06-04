import discord
from discord.ext import commands

MEDIA_TYPES = {'text' : [], 'image' : [], 'audio' : ['midi'], 'video' : [], 'application' : []}

# the following are helper functions that are used all over the place

async def get_nearby_attachment_url(ctx : commands.Context, type : str, subtype : str):
    
    if type not in MEDIA_TYPES:
        raise Exception(f'Invalid media type "{type}" passed as argument.')
    
    if subtype:
        if subtype not in MEDIA_TYPES[type]:
            raise Exception(f'Invalid media subtype "{subtype}" passed as argument.')
    
    async for message in ctx.channel.history(limit=25):
        for attachment in message.attachments:
            split_type = attachment.content_type.split('/')
            print(split_type)
            if not type or type == split_type[0]:
                if not subtype or subtype and subtype == split_type[1]:
                    return attachment.url

    return ''

async def get_relevant_attachment_url(ctx : commands.Context, type : str, subtype : str = ''):

    url = ''

    try:
        url = ctx.message.attachments[0].url
    except IndexError:
        url = await get_nearby_attachment_url(ctx, type, subtype)

    if not url:
        raise Exception(f'Could not find a relevant attachment attached to the command or to a recent message.')

    return url