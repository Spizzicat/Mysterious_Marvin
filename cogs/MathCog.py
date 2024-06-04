import math
import random
import string
from typing import List, Optional

import discord
import matplotlib as mpl
import matplotlib.image as mpimg
import matplotlib.pylab as plt
import numpy as np
from cycler import cycler
from discord.ext import commands
from scipy.special import gamma
import sympy as sym
from scipy.fft import fft, ifft, fftfreq

from helpers import *
from constants import DIR

LEGAL = {
            # constants
            'pi': plt.pi, 'e': plt.e,

            # exponents
            'pow': np.power, 'power': np.power, 
            'sqrt': plt.sqrt, 'exp': plt.exp, 'ln': plt.log, 'log': plt.log10,

            # statistics
            'factorial': gamma, 'gamma': gamma,

            # trigonometry
            'sin': plt.sin, 'cos': plt.cos, 'tan': plt.tan,
            'arcsin': plt.arcsin, 'arccos': plt.arccos, 'arctan': plt.arctan,
            'sinh': plt.sinh, 'cosh': plt.cosh, 'tanh': plt.tanh,
            'arcsinh': plt.arcsinh, 'arccosh': plt.arccosh, 'arctanh': plt.arctanh,

            # number theory
            # 'lcm': plt.lcm, 'gcd': plt.gcd,
            'abs': plt.absolute, 'absolute': plt.absolute, 'sign': plt.sign, 
            'mod': plt.mod, 'floor': plt.floor, 'ceil': plt.ceil, 
            # 'round': round
        }

class MathCog(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("\nMATH COG READY")

    @commands.hybrid_command(
        name="plot",
        description="simple graphing calculator",
        aliases=['graph']
    )
    async def plot(self, ctx : commands.Context, x_min : float = -10.0, x_max : float = 10.0, y_min : float = -10.0, y_max : float = 10.0):

        # initialize variables and functions
        x, y = np.meshgrid(np.linspace(x_min, x_max, 400), np.linspace(y_min, y_max, 400))
        legal_local = LEGAL
        legal_local['x'] = x
        legal_local['y'] = y
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        # get left side of equation
        await ctx.reply("Input left side of equation.")
        left = await self.bot.wait_for("message",check=check)
        left_str = left.content.strip().replace(' ','').replace('^','**')
        left = eval(left_str,None,legal_local)

        # get right side of equation
        await ctx.reply("Input right side of equation.")
        right = await self.bot.wait_for("message",check=check)
        right_str = right.content.strip().replace(' ','').replace('^','**')
        right = eval(right_str,None,legal_local)
        print(x)
        print('hi')
        
        plt.rcParams['axes.grid'] = True
        plt.rcParams['axes.titlesize'] = 30
        plt.rcParams['axes.labelsize'] = 30
        plt.rcParams['figure.figsize'] = 10,10
        
        fig = plt.figure()
        fig.clf()
        ax = fig.add_subplot()
        ax.cla()

        ax.set_aspect('auto')
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.title(f'{left_str}={right_str}'.replace('**','^'))
        
        # plot equation
        equation = left - right
        plt.contour(x, y, equation, [0], colors='#000000')

        # save and upload plot
        plt.savefig(f'{DIR}/temp/implicit.png')
        await ctx.reply(content='',file=discord.File(f'{DIR}/temp/implicit.png'))
        
    @commands.hybrid_command(
        name="harvest",
        description="fun data display",
    )
    async def harvest(self, ctx : commands.Context, member : Optional[discord.Member] = None):

        # initialize variables
        s = 12
        rows,cols = s,s
        value_text_size = 6.5
        # 85 * 1/np.sqrt(rows*cols)

        # create randomly generated fake vegetable and farmer names
        vegetables = [''.join(random.choices(string.ascii_lowercase,k=random.randint(3,7))).capitalize() for row in range(rows)]
        farmers = [''.join(random.choices(string.ascii_lowercase, k=random.randint(4,8))).capitalize()
        +' '+''.join(random.choices(string.ascii_lowercase, k=random.randint(4,8))).capitalize() 
        for col in range(cols)]

        # create array of random values from 0 to 1 & round them to two decimal places
        # harvest = [[round(j,1) for j in i] for i in np.random.random_sample((rows,cols))]
        harvest = [[round(np.sqrt(i*j),1) for j in range(1,cols+1)] for i in range(1,rows+1)]

        # create plots
        fig = plt.figure()
        fig.clf()
        ax = fig.add_subplot()
        ax.cla()
        im = ax.imshow(harvest,cmap='plasma',norm=mpl.colors.Normalize(vmin=np.min(harvest)-abs(np.max(harvest))/3,vmax=np.max(harvest)+abs(np.max(harvest)/2)))

        # formatting
        ax.set_title("Harvest of local farmers (in tons/year)")
        ax.set_xlabel('Farmers')
        ax.set_ylabel('Vegetables')
        ax.set_xticks(np.arange(cols),labels=farmers)
        ax.set_yticks(np.arange(rows),labels=vegetables)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        plt.rcParams['axes.grid'] = False
        plt.tight_layout()

        # create text for values
        for i in range(rows):
            for j in range(cols):
                ax.text(j,i,harvest[i][j],ha="center",va="center",color="w",size=value_text_size)

        # send plot
        plt.savefig(f'{DIR}/temp/harvest.png')
        await ctx.reply(content='',file=discord.File(f'{DIR}/temp/harvest.png'))

async def setup(bot):
    await bot.add_cog(MathCog(bot))