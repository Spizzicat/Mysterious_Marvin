import json
import random
from datetime import *

import discord
from discord.ext import commands

from config import * 
import asyncio

# things to do:
# make update_companies() handle the money in nonexistent companies before deletion
# maybe add check to the pay command that does not allow you to go into debt

# maybe rewrite bank as its own class

# make sure these have a capital letter
# alternatively you could make a companies dict with an id and a name
companies_list = ['Peepslart','Geepslart','Snorp','Beeple','Poopslart']

async def update_companies():
    '''Updates companies json based on the list above. This function should run when the cog starts up.'''

    bank = read_bank()

    real_company_keys_list = [x.lower() for x in companies_list]

    for company_name in companies_list:

        company_key = company_name.lower()

        # removes nonexistent company info from companies section of dict
        del_list = []
        for key in bank['companies']:
            if key not in real_company_keys_list:
                del_list.append(key)
        for key in del_list:
            bank['companies'].pop(key)

        # removes nonexistent companies from portfolios
        for account_id in bank['accounts'].keys():
            if company_key in bank['accounts'][account_id]['portfolio'] and company_key not in real_company_keys_list:
                bank['accounts'][account_id]['portfolio'][company_key].pop(company_key)

        # puts default company info in companies section of dict
        bank['companies'].setdefault(company_key, {'name':company_name,'price':1})

        # puts default company info in portfolios
        for account_id in bank['accounts'].keys():
            bank['accounts'][account_id]['portfolio'].setdefault(company_key,0)

    write_bank(bank)

async def handle_no_account(bank, member):
    '''Helper function that makes an account for a member if they do not have one yet.'''
    
    # adds account
    bank['accounts'].setdefault(str(member.id), {'name':str(member),'balance':0,"lastdaily":None,'portfolio':{}})
    bank['accounts'][str(member.id)].setdefault('lastdaily', None)

    # adds companies with default investments to the account's portfolio
    for company_name in companies_list:
        company_key = company_name.lower()
        bank['accounts'][str(member.id)]['portfolio'].setdefault(company_key, 0)

    write_bank(bank)

async def get_balance(ctx, member: discord.Member = None):

    bank = read_bank()
        
    member = ctx.author if not member else member

    await handle_no_account(bank,member)

    bal = int(bank['accounts'][str(member.id)]['balance'])

    write_bank(bank)

    return bal

async def deposit(ctx, amount=0, member=None):

    bank = read_bank()

    member = ctx.author if not member else member
    amount = round(float(amount))

    await handle_no_account(bank,member)

    bank['accounts'][str(member.id)]['balance'] += amount

    write_bank(bank)

    return

async def pay(ctx, member, amount):

    bank = read_bank()

    amount = round(float(amount))

    await handle_no_account(bank,ctx.author)
    await handle_no_account(bank,member)
    bank['accounts'][str(ctx.author.id)]['balance'] -= amount
    bank['accounts'][str(member.id)]['balance'] += amount
    
    write_bank(bank)

class Economy(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nECONOMY COG READY")
        await update_companies()

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, member: discord.Member = None):

        member = ctx.author if not member else member
        
        bal = await get_balance(ctx,member)
        await ctx.reply(f'{member} has {bal} Marvin Coin(s) in their account.')

    @commands.command(aliases=['give'])
    async def pay(self, ctx, member: discord.Member=None, amount=None):

        if not (member and amount):
            await ctx.reply(f'Please provide both a recipient and an amount.')
        
        await pay(ctx, member, amount)
        await ctx.reply(f'{amount} Marvin Coins have been transfered from {ctx.author}\'s account to {member}\'s account.')

    @commands.command(aliases=['game'])  
    async def gamble(self, ctx): # maybe change to m.bet amount condition

        await ctx.reply("Pick a number from 1 to 10.")

        bank = read_bank()

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
    
        answer = await self.bot.wait_for("message",check=check)

        if not answer.content.isdigit() and (not answer.content.startswith('m.')):
            
            await ctx.reply('Oh no! All of your Marvin Coins have been removed from your account.')
            if bank['accounts'][str(ctx.author.id)]['balance'] >= 0:
                await deposit(ctx, int(-1*bank['accounts'][str(ctx.author.id)]['balance']), ctx.author)
            
            return
        if int(answer.content) == random.randint(1,10):

            await ctx.reply('Correct! Nine Marvin Coins have been deposited into your account.')
            await deposit(ctx, 9, ctx.author)
        else:

            await ctx.reply('Incorrect! One Marvin Coin has been removed from your account.')
            await deposit(ctx, -1, ctx.author)

    @commands.command(aliases=['listcompanies','market','stockmarket'])
    async def companies(self, ctx):

        bank = read_bank()

        message = f'Companies:\n'
        for company in companies_list: # change this to read the json
            name = bank['companies'][company.lower()]['name']
            price = bank['companies'][company.lower()]['price']
            message += f'\n{name.capitalize()} - {price} Marvin Coin(s) per stock'

        await ctx.reply(message)

    @commands.command(aliases=['investments'])
    async def portfolio(self, ctx, member: discord.Member=None):
        
        member = ctx.author if not member else member

        bank = read_bank()

        await handle_no_account(bank,member)

        tot_coins_owned = 0
        bank_coins = await get_balance(ctx, member)
        tot_coins_owned += bank_coins
        
        message = f'{member}\'s Portfolio:\n'
        for company_key,num_shares in bank['accounts'][str(member.id)]['portfolio'].items():
            name = bank['companies'][company_key]['name']
            mc_value = bank['companies'][company_key]['price'] * num_shares
            message += f'\n{num_shares} {name} share(s) ({mc_value} Marvin Coins)'
            tot_coins_owned += mc_value
        
        message += f'\n\n{member} owns a total of {tot_coins_owned} Marvin Coins.'

        await ctx.reply(message)

    @commands.command(aliases=['buy','buystock'])  
    async def invest(self, ctx, company = None, shares = None):
        
        member = ctx.author

        # handles lack of arguments
        if not (shares and company):
            await ctx.reply("Please provide both a company and a number of shares.")
            return

        bank = read_bank() 

        company_key = str(company).lower()

        # handles invalid arguments
        if company_key not in bank['companies'] or not shares.isdigit():
            await ctx.reply("Invalid company provided.\nUse the companies command to view a list of valid companies.")
            return
        if not shares.isdigit():
            await ctx.reply("Invalid amount provided.")
            return

        await handle_no_account(bank,member)

        amount = round(float(shares))
        total = int(amount * int(bank['companies'][company_key]['price']))

        # company_name is defined after the argument checks to ensure that it works
        company_name = bank['companies'][company_key]['name']

        # checks if investor is in debt and does not let them invest if they are
        if bank['accounts'][str(member.id)]['balance'] < total or bank['accounts'][str(member.id)]['balance'] < 0:
            await ctx.reply("Insufficient Funds.")
            return

        # removes coins from account
        bank['accounts'][str(member.id)]['balance'] -= total
        # adds stock to portfolio
        bank['accounts'][str(member.id)]['portfolio'][company_key] += amount
        
        write_bank(bank)

        await ctx.reply(f'You purchased {amount} {company_name} share(s) for a total of {total} Marvin Coins.')

    @commands.command(aliases=['sellstock'])  
    async def sell(self, ctx, company = None, shares = None):
        
        member = ctx.author

        # handles lack of arguments
        if not (shares and company):
            await ctx.reply("Please provide both a company and a number of shares.")
            return

        bank = read_bank() 

        company_key = str(company).lower()

        # handles invalid arguments
        if not shares.isdigit():
            await ctx.reply("Invalid amount provided.")
            return
        if company_key not in bank['companies']:
            await ctx.reply("Invalid company provided.\nUse the companies command to view a list of valid companies.")
            return
        
        await handle_no_account(bank,member)

        amount = round(float(shares))
        total = int(amount * int(bank['companies'][company_key]['price']))
        
        # company_name is defined after the argument checks to ensure that it works
        company_name = bank['companies'][company_key]['name']

        # checks if you have enough coins in your portfolio to sell the specified amount
        amout_in_portfolio = bank['accounts'][str(member.id)]['portfolio'][company_key]
        if amout_in_portfolio - amount < 0:
            await ctx.reply(f"You cannot sell {amount} {company_name} share(s) because you only own {amout_in_portfolio} {company_name} share(s).")
            return

        # removes stock from portfolio
        bank['accounts'][str(member.id)]['portfolio'][company_key] -= amount
        # adds coins to account
        bank['accounts'][str(member.id)]['balance'] += total
        
        write_bank(bank)

        await ctx.reply(f'You sold {amount} {company_name} share(s) for a total of {total} Marvin Coins.')

    @commands.command(aliases=['claimdaily'])  
    async def daily(self, ctx):

        bank = read_bank()

        await handle_no_account(bank,ctx.author)
        
        msg_time = ctx.message.created_at
        last_claim_time_str = bank['accounts'][str(ctx.author.id)]['lastdaily']
        daily_amount = 3
        
        # handles null value for last claim time
        # note: null is the default value for last claim time
        if last_claim_time_str != None:
            
            # calculates time difference
            last_claim_time = datetime.fromisoformat(last_claim_time_str)
            delta_t = msg_time - last_claim_time
            cooldown_interval = timedelta(days=1)

            # for formatting
            tot_secs_left = round(cooldown_interval.total_seconds() - delta_t.total_seconds())

            if delta_t >= cooldown_interval:
                bank['accounts'][str(ctx.author.id)]['lastdaily'] = str(msg_time)
                write_bank(bank)
                await deposit(ctx, daily_amount, ctx.author)
                await ctx.reply(f'Your daily bonus of {daily_amount} Marvin Coins has been deposited into your account.')
            else:
                seconds_left = (tot_secs_left % 60)
                minutes_left = (tot_secs_left % 3600)//60
                hours_left = (tot_secs_left % 86400)//3600
                await ctx.reply(f'You have already claimed your daily bonus.\
                \nYou can claim your next daily bonus in {hours_left} hours, {minutes_left} minutes, and {seconds_left} seconds.')
        else:
            bank['accounts'][str(ctx.author.id)]['lastdaily'] = str(msg_time)
            write_bank(bank)
            await deposit(ctx, daily_amount, ctx.author)
            await ctx.reply(f'Your daily bonus of {daily_amount} Marvin Coins has been deposited into your account.')

    @commands.command()
    @commands.is_owner()
    async def updatebank(self, ctx):
        bank = read_bank()
        await update_companies()
        await ctx.reply('Bank updated.')

async def setup(bot):
    await bot.add_cog(Economy(bot))