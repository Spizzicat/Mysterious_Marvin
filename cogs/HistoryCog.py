import discord
from discord.ext import commands
from helpers import get_relevant_attachment_url
from constants import DIR

class HistoryCog(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("\nHISTORY COG READY")

    @commands.hybrid_command(
        name="history",
        description="show message history",
    )
    async def history(self, ctx : commands.Context):
        '''Shows message history.'''

        messages = []
        async for msg in ctx.message.channel.history(limit = 10):
            messages.append(msg.content)
        
        messages_string = ''
        for m in messages[::-1]:
            messages_string += m+'\n'

        await ctx.reply(messages_string)

async def setup(bot):
    await bot.add_cog(HistoryCog(bot))