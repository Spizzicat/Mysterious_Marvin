import json
import random
from datetime import *

import discord
from discord.ext import commands

from config import * 
import asyncio

# things to do:
# make update_companies() handle the money in nonexistent companies before deletion
# maybe add a check to the pay command that does not allow you to go into debt

# note: 
# do not use the name in the json for anything it is just so you can look into
# the file and see a name instead of just an ID

companies_list = ['Peepslart','Geepslart','Snorp','Beeple','Poopslart']

class Economy(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open(f'{DIR}/data/bank.json','r') as file:
            self.bank = json.loads(file.read())
        self.bank.setdefault('companies',{}) 
        self.bank.setdefault('accounts',{}) 

    def read_bank(self):
        '''Stores data from bank.json in self.bank.'''

        with open(f'{DIR}/data/bank.json','r') as file:
            self.bank = json.loads(file.read())

        self.bank.setdefault('companies',{}) 
        self.bank.setdefault('accounts',{}) 

    def write_bank(self):
        '''Writes self.bank to bank.json.'''

        with open(f'{DIR}/data/bank.json','w') as file:
            json.dump(self.bank, file, indent=4)
        file.close()

    def handle_no_account(self, member):
        '''Helper function that makes an account for a member if they do not have one yet.'''
        
        # adds account
        self.bank['accounts'].setdefault(str(member.id), {'name':str(member),'balance':0,"lastdaily":None,'portfolio':{}})
        self.bank['accounts'][str(member.id)].setdefault('lastdaily', None)

        # adds companies with default investments to the account's portfolio
        for company_name in companies_list:
            company_key = company_name.lower()
            self.bank['accounts'][str(member.id)]['portfolio'].setdefault(company_key, 0)

        self.write_bank()

    def get_balance(self, ctx, member: discord.Member = None):

        self.read_bank()

        member = ctx.author if not member else member
        self.handle_no_account(member)
        bal = int(self.bank['accounts'][str(member.id)]['balance'])

        self.write_bank()

        return bal
    
    def transfer_coins(self, ctx, member, amount):

        self.read_bank()

        amount = round(float(amount))
        self.handle_no_account(ctx.author)
        self.handle_no_account(member)
        self.bank['accounts'][str(ctx.author.id)]['balance'] -= amount
        self.bank['accounts'][str(member.id)]['balance'] += amount

        self.write_bank()

    def deposit(self, ctx, amount=0, member=None):

        self.read_bank()

        member = ctx.author if not member else member
        amount = round(float(amount))
        self.handle_no_account(member)
        self.bank['accounts'][str(member.id)]['balance'] += amount

        self.write_bank()
    
    def update_companies(self):
        '''Updates companies based on the company list. This function should run when the cog starts up.'''

        self.read_bank()

        real_company_keys_list = [x.lower() for x in companies_list]

        for company_name in companies_list:

            company_key = company_name.lower()

            # removes nonexistent company info from companies section of dict
            del_list = []
            for key in self.bank['companies']:
                if key not in real_company_keys_list:
                    del_list.append(key)
            for key in del_list:
                self.bank['companies'].pop(key)

            # removes nonexistent companies from portfolios
            for account_id in self.bank['accounts'].keys():
                if company_key in self.bank['accounts'][account_id]['portfolio'] and company_key not in real_company_keys_list:
                    self.bank['accounts'][account_id]['portfolio'][company_key].pop(company_key)

            # puts default company info in companies section of dict
            self.bank['companies'].setdefault(company_key, {'name':company_name,'price':1})

            # puts default company info in portfolios
            for account_id in self.bank['accounts'].keys():
                self.bank['accounts'][account_id]['portfolio'].setdefault(company_key,0)

        self.write_bank()

    @commands.Cog.listener()
    async def on_ready(self):

        print("\nECONOMY COG READY")
        self.update_companies()

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, member: discord.Member = None):

        member = ctx.author if not member else member
        bal = self.get_balance(ctx, member)
        await ctx.reply(f'{member.nick} ({member}) has {bal} Marvin Coin(s) in their account.')

    @commands.command(aliases=['give'])
    async def pay(self, ctx, member: discord.Member=None, amount=None):

        if not (member and amount):
            await ctx.reply(f'Please provide both a recipient and an amount.')
        
        self.transfer_coins(ctx, member, amount)
        await ctx.reply(f'{amount} Marvin Coins have been transfered from {ctx.author}\'s account to {member}\'s account.')

    @commands.command(aliases=['game'])  
    async def gamble(self, ctx): # maybe change to m.bet amount condition

        await ctx.reply("Pick a number from 1 to 10.")

        self.read_bank()

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
    
        answer = await self.bot.wait_for("message",check=check)

        if not answer.content.isdigit() and (not answer.content.startswith('m.')):
            
            await ctx.reply('Oh no! All of your Marvin Coins have been removed from your account.')
            if self.bank['accounts'][str(ctx.author.id)]['balance'] >= 0:
                self.deposit(ctx, int(-1 * self.bank['accounts'][str(ctx.author.id)]['balance']), ctx.author)
            return
        if int(answer.content) == random.randint(1,10):

            await ctx.reply('Correct! Nine Marvin Coins have been deposited into your account.')
            self.deposit(ctx, 9, ctx.author)
        else:

            await ctx.reply('Incorrect! One Marvin Coin has been removed from your account.')
            self.deposit(ctx, -1, ctx.author)

    @commands.command(aliases=['listcompanies','market','stockmarket'])
    async def companies(self, ctx):

        self.read_bank()

        message = f'Companies:\n'
        for company in companies_list: # change this to read the json
            name = self.bank['companies'][company.lower()]['name']
            price = self.bank['companies'][company.lower()]['price']
            message += f'\n{name.capitalize()} - {price} Marvin Coin(s) per stock'

        await ctx.reply(message)

    @commands.command(aliases=['investments'])
    async def portfolio(self, ctx, member: discord.Member=None):
        
        member = ctx.author if not member else member

        self.read_bank()

        self.handle_no_account(member)

        tot_coins_owned = 0
        bank_coins = self.get_balance(ctx, member)
        tot_coins_owned += bank_coins
        
        message = f'{member}\'s Portfolio:\n'
        for company_key,num_shares in self.bank['accounts'][str(member.id)]['portfolio'].items():
            name = self.bank['companies'][company_key]['name']
            mc_value = self.bank['companies'][company_key]['price'] * num_shares
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

        self.read_bank() 

        company_key = str(company).lower()

        # handles invalid arguments
        if company_key not in self.bank['companies'] or not shares.isdigit():
            await ctx.reply("Invalid company provided.\nUse the companies command to view a list of valid companies.")
            return
        if not shares.isdigit():
            await ctx.reply("Invalid amount provided.")
            return

        self.handle_no_account(member)

        amount = round(float(shares))
        total = int(amount * int(self.bank['companies'][company_key]['price']))

        # company_name is defined after the argument checks to ensure that it works
        company_name = self.bank['companies'][company_key]['name']

        # checks if investor is in debt and does not let them invest if they are
        if self.bank['accounts'][str(member.id)]['balance'] < total or self.bank['accounts'][str(member.id)]['balance'] < 0:
            await ctx.reply("Insufficient Funds.")
        else:
            # removes coins from account
            self.bank['accounts'][str(member.id)]['balance'] -= total
            # adds stock to portfolio
            self.bank['accounts'][str(member.id)]['portfolio'][company_key] += amount
        
        self.write_bank()

        await ctx.reply(f'You purchased {amount} {company_name} share(s) for a total of {total} Marvin Coins.')

    @commands.command(aliases=['sellstock'])  
    async def sell(self, ctx, company = None, shares = None):
        
        # handles lack of arguments
        if not (shares and company):
            await ctx.reply("Please provide both a company and a number of shares.")
            return

        self.read_bank() 

        company_key = str(company).lower()

        # handles invalid arguments
        if not shares.isdigit():
            await ctx.reply("Invalid amount provided.")
            return
        if company_key not in self.bank['companies']:
            await ctx.reply("Invalid company provided.\nUse the companies command to view a list of valid companies.")
            return
        
        self.handle_no_account(ctx.author)

        amount = round(float(shares))
        total = int(amount * int(self.bank['companies'][company_key]['price']))
        
        # company_name is defined after the argument checks to ensure that it works
        company_name = self.bank['companies'][company_key]['name']

        # checks if you have enough coins in your portfolio to sell the specified amount
        amout_in_portfolio = self.bank['accounts'][str(ctx.author.id)]['portfolio'][company_key]
        if amout_in_portfolio - amount < 0:
            await ctx.reply(f"You cannot sell {amount} {company_name} share(s) because you only own {amout_in_portfolio} {company_name} share(s).")
            return

        # removes stock from portfolio
        self.bank['accounts'][str(ctx.author.id)]['portfolio'][company_key] -= amount
        # adds coins to account
        self.bank['accounts'][str(ctx.author.id)]['balance'] += total
        
        self.write_bank()

        await ctx.reply(f'You sold {amount} {company_name} share(s) for a total of {total} Marvin Coins.')

    @commands.command(aliases=['claimdaily'])  
    async def daily(self, ctx):

        self.read_bank()

        self.handle_no_account(ctx.author)
        
        msg_time = ctx.message.created_at
        last_claim_time_str = self.bank['accounts'][str(ctx.author.id)]['lastdaily']
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
                self.bank['accounts'][str(ctx.author.id)]['lastdaily'] = str(msg_time)
                self.deposit(ctx, daily_amount, ctx.author)
                await ctx.reply(f'Your daily bonus of {daily_amount} Marvin Coins has been deposited into your account.')
            else:
                seconds_left = (tot_secs_left % 60)
                minutes_left = (tot_secs_left % 3600)//60
                hours_left = (tot_secs_left % 86400)//3600
                await ctx.reply(f'You have already claimed your daily bonus.\
                \nYou can claim your next daily bonus in {hours_left} hours, {minutes_left} minutes, and {seconds_left} seconds.')
        else:
            self.bank['accounts'][str(ctx.author.id)]['lastdaily'] = str(msg_time)
            self.deposit(ctx, daily_amount, ctx.author)
            await ctx.reply(f'Your daily bonus of {daily_amount} Marvin Coins has been deposited into your account.')

        self.write_bank()

    @commands.command()
    @commands.is_owner()
    async def updatebank(self, ctx):

        self.update_companies()
        
        for account_id in self.bank['accounts'].keys():
            user = await self.bot.fetch_user(int(account_id))
            self.bank['accounts'][account_id]['name'] = user.name
        
        self.write_bank()
        self.read_bank()

        await ctx.reply('Bank updated.')

async def setup(bot):
    await bot.add_cog(Economy(bot))