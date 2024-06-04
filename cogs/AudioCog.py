import os
from typing import Optional
import requests
import mido

import discord
import matplotlib as mpl
import matplotlib.image as mpimg
import matplotlib.pylab as plt
import numpy as np
from discord.ext import commands
from scipy.io import wavfile
from scipy.fft import fft, ifft, fftfreq
from scipy import stats
from helpers import get_relevant_attachment_url
from bot import DIR

NOTE_NAMES = ['C','Db','D','Eb','E','F','Gb','G','A','Bb','B']

def note_from_name(name):
    if name.isdigit():
        return int(name)
    map = dict(zip([name.upper() for name in NOTE_NAMES],range(12)))
    return int(map[str(name).upper()])

def get_octave(note):

    return int(note) // 12

def flip_note(note, axis):

    flipped = (2 * axis - int(note))
    return int(flipped)

def get_most_common_note(midi : mido.MidiFile):

    notes = []
    for track in midi.tracks:
        for msg in track:
            if msg.type in ['note_on','note_off'] and msg.channel != 10:
                if msg.channel == 9:
                    continue
                notes.append(int(msg.note))

    m = stats.mode(tuple(notes), keepdims=False).mode # may break in scipy update
    if m:
        mode = m
    else:
        mode = None

    return mode

def flip_midi(midi : mido.MidiFile, axis):

    # organize messages by channel
    channels = [{'notes':[],'pitchwheel':[]} for x in range(0,16)]
    for track in midi.tracks:
        for msg in track:
            if msg.type in ['note_on']:
                channels[msg.channel-1]['notes'].append(msg)
            if msg.type in ['note_off']:
                channels[msg.channel-1]['notes'].append(msg)
            if msg.type in ['pitchwheel']:
                channels[msg.channel-1]['pitchwheel'].append(msg)

    for c, channel in enumerate(channels):

        # skip empty channels and drum channel
        if not channel or c == 8 or (not channel['notes'] and not channel['pitchwheel']):
            continue
        
        # get list of note offs
        note_off_msgs = [n for n in channel['notes'] if n.type == 'note_off']
        offs = [int(n.note) for n in note_off_msgs]
        
        if not offs:
            continue

        # get list of flipped note offs
        flipped_offs = [flip_note(note,axis) for note in offs]

        # get note durations (flipping does not change this)
        durations = [int(x.time) for x in note_off_msgs]

        # calculate octave adjustment
        adj_dict = {}
        in_wavg = np.average(a=offs,weights=durations)
        out_wavg = np.average(a=flipped_offs,weights=durations)
        for a in [12*x for x in range(-12,13)]:
            diff = int(np.round(np.abs(out_wavg+a-in_wavg)))
            adj_dict.update({diff:a})
        adj = adj_dict[min(list(adj_dict.keys()))]

        # adjust flipped notes
        flipped_notes = [flip_note(msg.note,axis)+adj for msg in channel['notes']]

        # flip notes
        for i, msg in enumerate(channel['notes']):
            if flipped_notes[i] >= 0 and flipped_notes[i] <= 127:
                msg.note = flipped_notes[i]
            else:
                for track in midi.tracks:
                    if msg in track:
                        track.remove(msg)

        # flip pitch events
        for msg in channel['pitchwheel']:
            if msg.pitch == 0:
                continue
            msg.pitch = min((msg.pitch+1)*-1,8191)

def process_signals(*signals : tuple):

    return_signals = []
    k_size = 1000
    kernel = [1/k_size for x in range(k_size)]

    # normal distribution
    # [(np.exp(-((x-k_size/2)/(k_size/5))**2))/k_size for x in range(k_size)]

    for signal in list(signals):
        return_signal = np.int32(np.convolve(signal,kernel,mode='same'))
        return_signals.append(return_signal)
        
    return return_signals

class AudioCog(commands.Cog):

    def __init__(self,bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nAUDIO COG READY")

    @commands.command()
    async def smurgle(self, ctx : commands.Context):

        in_filename = 'smurgle.wav'
        out_filename = 'out.wav'

        url = await get_relevant_attachment_url(ctx, 'audio')
        
        with open(f'{DIR}/temp/{in_filename}', 'wb') as f:
            f.write(requests.get(url).content)
            f.close

        # fix format
        os.system(f'ffmpeg -i ./temp/{in_filename} -c:a pcm_s32le -y ./temp/{out_filename}') 
        # read in the wav file
        sample_rate, data_in = wavfile.read(f'./temp/{out_filename}')

        left_in = data_in[:,0]
        right_in = data_in[:,1]

        left_out, right_out = process_signals(left_in,right_in)

        data_out = np.array([left_out, right_out]).transpose()

        # normalize data
        ratio = np.max(np.absolute(data_in)) / np.max(np.absolute(data_out)) 

        # write and send wav file
        data_out = np.int32(ratio*np.matrix(data_out))
        with open(f'{DIR}/temp/{out_filename}', 'wb') as f:
            wavfile.write(f'{DIR}/temp/{out_filename}', sample_rate, data_out)
        os.system(f'ffmpeg -i ./temp/{out_filename} -fs 10276048 -y ./temp/out.mp3')
        await ctx.reply(content='',file=discord.File(f'{DIR}/temp/out.mp3'))

    # @commands.command()
    # async def spectrum(self,ctx):

    #     in_filename = 'spectrum.wav'
    #     out_filename = 'out.wav'

    #     try:
    #         url = ctx.message.attachments[0].url
    #     except:
    #         await ctx.reply("dumbfuck")
    #         return None
    #     else:
    #         pass

    #     with open(DIR+'/spectrum.wav', 'wb') as f:
    #         f.write(requests.get(url).content)
    #         f.close

    #     # fix format
    #     try:
    #         os.remove(out_filename)
    #     except:
    #         print('could not find "out.wav"')
    #     os.system(f'ffmpeg -i {in_filename} -c:a pcm_s32le out.wav')
        
    #     # read in the wave file
    #     sample_rate, data_in = wavfile.read(str(out_filename))

    #     left_in, right_in = [data_in[:,0],data_in[:,1]]

    #     # process signals
    #     def process_signals(*signals):

    #         return_signals = []

    #         for y in list(signals):
                
    #             yt = fft(y)
    #             yt = np.abs(fft(y))

    #             yt = np.log(yt)
    #             # k = 1
    #             # yt = np.convolve(yt,np.ones(k),mode='same')/k
    #             yt = np.power(10,yt)

    #             return_signals.append(yt)
                
    #         return return_signals
        
    #     left_out,right_out = process_signals(left_in,right_in)

    #     # plot data
    #     data_out = np.array([left_out,right_out]).transpose()
    #     freqs = fftfreq(n=len(data_out),d=1/sample_rate)
    #     # plt.plot(time_in,left_in,label='Left channel in')
    #     # plt.plot(time_in,right_in,label='Right channel in')
    #     # plt.show()
    #     plt.clf()
    #     plt.xscale('log')
    #     plt.plot(freqs,left_out,label='Left channel out')
    #     plt.plot(freqs,right_out,label='Right channel out')

    #     # send spectrum image
    #     plt.savefig(f'{DIR}/images/spectrum.png')
    #     await ctx.reply(content='',file=discord.File(DIR+'/images/spectrum.png'))

    #     # normalize data
    #     ratio = np.max(np.absolute(data_in)) / np.max(np.absolute(data_out)) 
    #     data_out = np.int32(ratio*np.matrix(data_out))

    #     # write and send wav file
    #     wavfile.write(out_filename, sample_rate, data_out)
    #     wavfile.write('zoop.wav', sample_rate, data_out)
    #     await ctx.reply(content='',file=discord.File(DIR+'/out.wav'))

    @commands.command(aliases=['negharm','negative','neg','flip','midiflip','invert','inverse','inv'])
    async def negativeharmony(self, ctx : commands.Context, axis : Optional[str] =None):

        # make it error if it cannot read the midi (?)

        # get midi
        url = await get_relevant_attachment_url(ctx, 'audio', 'midi')

        with open(f'{DIR}/temp/neg_in.mid', 'wb') as f:
            f.write(requests.get(url).content)
            f.close
        midi = mido.MidiFile(f'{DIR}/temp/neg_in.mid')

        # get axis note
        if axis:
            axis = note_from_name(axis)
        else:
            root = get_most_common_note(midi)
            if root:
                axis = root
            else:
                axis = 60 # middle c

        # flip midi
        if not midi:
            return
        print('beginning flipping')
        flip_midi(midi,axis)
        print('done flipping')

        # send flipped midi
        filename = f'negative'
        with open(f'{DIR}/temp/{filename}.mid', mode='w') as f:
            midi.save(f'{DIR}/temp/{filename}.mid')
        # make sure you have fluidsynth
        os.system(f'fluidsynth ./data/general.sf2 ./temp/{filename}.mid -F ./temp/{filename}.wav')
        os.system(f'ffmpeg -i ./temp/{filename}.wav -acodec libmp3lame -y ./temp/{filename}.mp3')
        await ctx.reply(content='',files=[discord.File(f'{DIR}/temp/{filename}.{ext}') for ext in ['mid','mp3']])

async def setup(bot):
    await bot.add_cog(AudioCog(bot))