#!/usr/bin/env python3
# Pythoven 2 / tehdog
# Writes music

# Notes stored as a list of tuples of the form (start, step)
# The first entry in a track is the track's length
# time in measure is on a scale of sixteenth notes (0x0 -> 0xF)
# measures are therefore measured hexadecimally as well.
# This convention is not required, but is recommended for anything
# written in a binary time (4/4, 2/4, etc...)

# note is an integer representing the number of half-steps off the
# base note

'''
@author: darkspork,tehdog
'''

from __future__ import print_function # for python2 compatibility
import random, os, errno, sys, Waves
from random import randint      # Used in wrand

def replaceprint(s):
    sys.stdout.write("\r" + str(s) + " "*20)
    sys.stdout.flush()

curprogress = 0 
  
def startprogress(s):
    sys.stdout.write('\r' + (len(s) + 30) * ' ' + ']')
    sys.stdout.write('\r' + s + '[')
    sys.stdout.flush()
    global curprogress
    curprogress = 0
def updateprogress(prog):
    global curprogress
    if int(prog * 30) > curprogress:
        curprogress = int(prog * 30)
        sys.stdout.write('=')
        sys.stdout.flush()
    
def makeScale(rawScale):
    """makeScale
        rawScale - a raw version of the scale to use
        returns a scale: a tuple such that the
            first item is a list of acceptable offsets,
            and the second is the size of the scale"""
    note = 0
    li = []
    for n in rawScale:
        li.append(note)
        note += n
    return (li, sum(rawScale))

# The scale of notes, represented in text form
NOTES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')


# Various scales
MAJOR = makeScale((2, 2, 1, 2, 2, 2, 1))
NATURAL_MINOR = makeScale((2, 1, 2, 2, 1, 2, 2))
MELODIC_MINOR = makeScale((2, 1, 2, 2, 2, 2, 1))
HARMONIC_MINOR = makeScale((2, 1, 2, 2, 1, 3, 1))
WHOLE_TONE = makeScale((2, 2, 2, 2, 2, 2))
PENTATONIC = makeScale((2, 3, 2, 2))
CHROMATIC = makeScale((1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1))

# Notes and quality
# Basically, measure the amount of dissonance, in half-steps
# Higher number = worse sound
# If dissonance becomes too high, then remake this note
# dissonance = melodic dissonance + average harmonic dissonance

# Half-steps:              -C  -B  -A  -9  -8  -7  -6  -5  -4  -3  -2  -1   0   1   2   3   4   5   6   7   8   9   A   B   C
# In the key of C:         C   C#  D   D#  E   F   F#  G   G#  A   A#  B   C   C#  D   D#  E   F   F#  G   G#  A   A#  B   C

MELODIC_INTERVAL = ((-12, 5), (-11, 6), (-10, 4), (-9, 3), (-8, 2), (-7, 3),
                    (-6, 4), (-5, 1), (-4, 1), (-3, 2), (-2, 2), (-1, 3),
                    (0, 0),
                    (1, 3), (2, 2), (3, 2), (4, 1), (5, 1), (6, 4),
                    (7, 3), (8, 2), (9, 3), (10, 4), (11, 6), (12, 5))

# Half-steps:               0   1   2   3   4   5   6   7   8   9   A   B
# In the key of C:         C   C#  D   D#  E   F   F#  G   G#  A   A#  B
HARMONIC_INTERVAL = (0, 10, 8, 3, 2, 1, 8, 1, 2, 3, 7, 9)

def getLastNote(track, position):
    """getLastNote
        track    - a list of notes
        position - the position (int) to start from
        return a tuple (time, note)
            of the most recent note from position"""
    return [(time, note) for (time, note) in track[1:] if time <= position][-1]

def noteString(note, key='C', padded=False):
    """noteString
        note - a number indicating the halfstep offset from the key
        key - the key to print the track in as a string (i.e. 'F#')
        return a string representation of a note"""
    i = note + NOTES.index(key)
    g = len(NOTES)
    n = 0
    s = ''
    while i < 0:
        i += g
        n -= 1
    while i >= g:
        i -= g
        n += 1
    if n > 0:
        s = "+%d%s" % (n, NOTES[i])
    elif n < 0:
        s = "%d%s" % (n, NOTES[i])
    else:
        s = "%s%s" % (padded and '  ' or '', NOTES[i])
    if padded:
        return s.ljust(4)
    return s

def trackString(track, key='C', measure=16):
    """trackString
        track   - a list of notes
        key     - the key to print the track in as a string (i.e. 'F#')
        measure - length of measure
                    note: if given, makes output easier to read
        return a string representation of a track"""
    #return "".join(["%s%s"%("".ljust(2*time),noteString(note, key).ljust(2)) for (time, note) in track]).replace(" ", "-")
    if measure:
        i = 0
        li = []
        for (time, note) in track[1:]:
            while i < time:
                if not i % measure: # on measure break
                    li.append('\n')
                li.append('    ')
                i += 1
            if not i % measure: # on measure break
                li.append('\n')
            li.append(noteString(note, key, True))
            i += 1
        return "".join(li)
    return ", ".join(["0x%X:%s" % (time, noteString(note, key, False)) for (time, note) in track[1:]])

def vprint(o):
    print(str(o),end='')

def wrap(li, i):
    """wrap
        li - a list
        i  - an index
        return li[i] (if i is out of range, wrap around)"""
    return li[i % len(li)]

def inScale(note, scale=MAJOR):
    """inScale
        note  - a numeric key offset note
        scale - scale to investigate
        size  - # of half steps in scale
        return true if note is in scale"""
    n = note
    while n < 0:
        n += scale[1]
    while n > scale[1]:
        n -= scale[1]
    return n in scale[0]

def wrand(d):
    """Find a value with a weighted average
        d - a wrand dictionary
        returns a random value in d"""
    i = randint(0, d['max'])
    while i >= 0 and i not in d:
        i -= 1
    return d[i]

def melodic2wrand(melodic=MELODIC_INTERVAL):
    """melodic2wrand
        melodic - a melodic interval to use"""
    d = {}
    weight = 0
    for (interval, freq) in melodic:
        d[weight] = interval
        weight += 10 - freq
    d['max'] = weight
    return d

def mktimes(measure, beat, sync, length):
    """mktimes
        measure  - number of beats in a measure
        beat     - default beats per note (must be < measure, should be divisible by measure)
        sync     - % chance that each beat will be split
        length   - how many measures to create
        returns a list of times that a note should appear"""
    li = []
    for i in range(0, length * measure // beat):
        li.append(i * beat)
        if (randint(0, 100) < sync):
            li.append(i * beat + beat // 2)
    return li

def loop(track, length):
    """loop
        track - the track to loop
        length - the number of ticks to loop to
        returns a new track"""
    newtrack = [length]
    i = 0;
    while i < length:
        newtrack.extend([(time + i, note) for (time, note) in track[1:]])
        i += track[0]
    while newtrack[-1][0] > length:
        del(newtrack[-1])
    return newtrack

def avgdissonance(sheet, time, mainnote, harmonic):
    """avgdissonance
        sheet    - a music sheet
        time     - a time to count dissonance at
        mainnote - the note to check dissonance against
        harmonic - a harmonic interval to use
        returns the average dissonance between
            the last track's last note and the rest"""
    notes = [getLastNote(track, time) for track in sheet]
    return sum([wrap(harmonic, abs(n[1] - mainnote)) for n in notes]) // len(sheet)

def shift(track, halfsteps):
    """shift
        track     - the track to shift
        halfsteps - number of half-steps (positive or negative) to shift the track
        returns None, shifts track"""
    for i in range(1, len(track)):
        note = track[i]
        track[i] = (note[0], note[1] + halfsteps)

def compose(measure=16, beat=4, sync=14, length=1, stray=10, scale=MAJOR, melodic=MELODIC_INTERVAL, seed=None, offset=0):
    """compose
        measure  - number of beats in a measure
        beat     - default beats per note (must be < measure, should be divisible by measure)
        sync     - % chance that each beat will be split
        length   - how many measures to create
        stray    - how many half-steps the notes are allowed to stray from 0
        scale    - a musical scale to use
        melodic  - melodic interval frequency
        seed     - random seed
        returns a track"""
    random.seed(seed) # initialize the random
    mwrand = melodic2wrand(melodic)
    track = [length * measure, (0, 0)]
    times = mktimes(measure, beat, sync, length)
    del(times[0])
    for i in times:
        note = track[-1][1] + wrand(mwrand) # because the last note in the track will always be the prev.
        while note > stray or note < -stray or not inScale(note, scale):
            note = track[-1][1] + wrand(mwrand) # choose next note as a melodic of the previous
        track.append((i, note))
    if offset != 0 :shift(track, offset)
    return track

def counterpoint(sheet, start=0, measure=16, beat=4, sync=27, length=1, stray=7, dissonance=3,
                 scale=MAJOR, melodic=MELODIC_INTERVAL, harmonic=HARMONIC_INTERVAL, seed=None):
    """compose
        sheet      - a list of other tracks in the song
        start      - a note (offset) to begin on
        measure    - number of beats in a measure
        beat       - default beats per note (must be < measure, should be divisible by measure)
        sync       - % chance that each beat will be split
        length     - how many measures to create. Note: all tracks will be looped to appropriate
                        length before calculation
        stray      - how many half-steps the notes are allowed to stray from the first
        dissonance - maximum average dissonance allowed per note
        scale      - a musical scale to use
        melodic    - melodic interval frequency
        harmonic   - harmonic dissonance
        seed       - random seed
        returns None, adds new track to sheet"""
    random.seed(seed) # initialize the random
    mwrand = melodic2wrand(melodic)
    track = [length * measure, (0, start)]
    tsheet = [loop(t, measure * length) for t in sheet] # create a temporary bastardized loop version
    times = mktimes(measure, beat, sync, length)
    highstray = start + stray
    lowstray = start - stray
    del(times[0])
    for i in times:
        note = track[-1][1] + wrand(mwrand)
        while note > highstray or note < lowstray or not inScale(note, scale) or avgdissonance(tsheet, i, note, harmonic) > dissonance:
            note = track[-1][1] + wrand(mwrand)
        track.append((i, note))
    sheet.append(track)

def bass(scale=MAJOR, length=4):
    track = compose(beat=16, sync=0, length=length, scale=scale)
    shift(track, -12)
    return track

def notbass(scale=MAJOR, length=4):
    track = compose(beat=16, sync=0, length=length, scale=scale)
    shift(track, +12)
    return track
    
def rlen(e):
    l = 0
    if isinstance(e, (list, tuple)):
        for i in e: l += rlen(i)
        return l
    return 1
        
def midiSing(sheet, instruments, key, ticktime, filename):
    from midiutil.MidiFile import MIDIFile
    offset = NOTES.index(key) + 60 # Middle C is MIDI note #60    
    midi=MIDIFile(len(sheet))
    replaceprint('Creating midi...')
    for t in range(0,len(sheet)): 
        midi.addTrackName(t, 0, "Track %s"%t)
        midi.addTempo(t, 0, 60000/(ticktime))
        sheet[t]=sheet[t][1:]+[(sheet[t][0],0)]
        tracklen=len(sheet[t])
        for n in range(0,tracklen-1):
            time, note = sheet[t][n]
            duration = sheet[t][(n+1)%tracklen][0]-time
            midi.addNote(t,0,offset+note,time,duration,100)#MyMIDI.addNote(track,channel,pitch,time,duration,volume)
    replaceprint('Writing to file...')
    binfile = open(filename+".mid", 'wb')
    midi.writeFile(binfile)
    binfile.close()
    replaceprint('Synth complete!')
    print("\nMID output to: \"" + filename+ ".mid\"")
    
def mp3Sing(loopedsheet, instruments, key, ticktime, filename):
    wavSing(loopedsheet,instruments, key,ticktime,filename, True)
    replaceprint('Encoding mp3 with ffmpeg...')
    import subprocess
    hasffmpeg = subprocess.call(["which", "ffmpeg"], stdout=subprocess.PIPE) == 0
    if hasffmpeg:
        cmdline = ["ffmpeg", "-loglevel", "error"]
        cmdline += ["-i", filename+".wav", "-ab", "128k"]
        cmdline += ["-metadata", "title=" + filename.split('/')[-1], "-metadata", "artist=Pythoven 2", "-metadata", "album=" + instruments[0].capitalize()]
        cmdline += [filename+".mp3"]
        mp3success = subprocess.call(cmdline) == 0
        replaceprint('Synth complete!')
        if mp3success: print("\nMP3 output to: \"" + filename+ ".mp3\"")
        else: print("\nMP3 output failed")
    else:
        print("ffmpeg not found, no mp3 output")
    os.remove(filename+".wav") 
    
def wavSing(loopedsheet, instruments, key, ticktime, filename, hidefinal=False):
    from Waves import initArray, FREQS
    cues = []
    offset = NOTES.index(key) + 48 # Middle C is MIDI note #48    
    for track in loopedsheet:
        cuedtrack = track[1:]
        cuedtrack.append((track[0], 0)) # append tracklength to the end so i+1 still works for last note
        cues.append([(cuedtrack[i + 1][0] - cuedtrack[i][0], cuedtrack[i][1] + offset) for i in range(0, len(cuedtrack) - 1)])
    # cues now contains the sheet in a usable format
    startprogress('Generating waves: ')
    waves = []
    vol = 1.0 / len(cues)
    notecount = rlen(cues) // 2
    progress = 0.0
    instscpy=instruments[:]
    for track in cues:
        trackwave = initArray()
        instrument = instscpy.pop(0)
        for (duration, note) in track:
            trackwave.extend(Waves.cachedWaveGen(FREQS[note], duration * ticktime, instrument, vol))
            progress += 1.0
            updateprogress(progress / notecount)
        waves.append(trackwave)
    replaceprint('Creating mixdown...' + ' ' * 30)
    wave = Waves.mergeWaves(waves)
    replaceprint('Writing file...')
    Waves.makeWavFile(wave, filename+".wav")
    replaceprint('Synth complete!')
    if not hidefinal: print "\nWAV output to: \"" + filename + ".wav\""

# removing this for now: def waveGenII(freq, length, instruments):
outformats={'mid':midiSing,'wav':wavSing, 'mp3':mp3Sing}

def sing(sheet, key='C', ticktime=125, instruments=(), filename='./test.wav', fmt='wav'):
    """sing
        sheet       - a music sheet to sing
        key         - the key to sing in
        ticktime    - the time each tick in the
                        sheet should take, in milliseconds.
                        The default 125 with 16-tick measures
                        in 4/4 time will result in
                        120 beats per minute
        instruments - a list of instruments to use
        filename    - the name of the wav file to make
        return None, create a wav file from the sheet"""
    
    vprint('Calculating track length...')
    lens = [track[0] for track in sheet]
    length = max(lens)
    replaceprint('\rFile will be approx. %d seconds' % (length * ticktime // 1000))
    vprint("\nLooping tracks...") 
    loopedsheet = [loop(track, length) for track in sheet]
    # Convert the sheet from absolute times to relative times, and
    # relative notes to MIDI style absolute notes
    replaceprint('Calculating cues...')
    if not instruments:
        instruments = [Waves.DEFAULT_INSTRUMENT] * len(sheet)
    singer=outformats[fmt]
    singer(loopedsheet, instruments, key, ticktime, filename)
    
def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST: pass
        else: raise


def makeSong(instrument, songname, fmt):
    if not songname: songname = randomname()
    print('Seed and trackname: ' + songname)
    # okay so I'm going to try something here:
    # first I will generate a "theme" with the length of two measures
    theme = compose(length=2, seed=songname)
    # and put it in the sheet
    sheet = [theme]
    # this theme will now get a few minor variations, but be repeated through 10 measures:
    counterpoint(sheet, dissonance=1, beat=16, length=10, seed=songname + "bass")
    # which will be our bass track
    basstrack = sheet[1]
    shift(basstrack, -12)
    sheet.pop(0)
    counterpoint(sheet, beat=2, dissonance=3, length=20, seed=songname + "melody")
    # todo: more stuff here

    dirname = 'output'
    mkdirp(dirname)
    outname = dirname + "/Pythoven - %s" % songname
    
    sing(sheet, key='C', ticktime=125, instruments=[instrument] * len(sheet), filename=outname, fmt=fmt)

############################## MAIN #####################################
from RandomName import randomname
from datetime import datetime
from Waves import INSTRUMENTS
import argparse

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Generate a song')
        parser.add_argument('instrument', default='guitar', choices=INSTRUMENTS, help='use this instrument/waveform; will be ignored when using midi (default: %(default)s)')
        parser.add_argument('-s', '--seed', metavar='name', help='use a special songname/seed (default: random)')
        parser.add_argument('-f', metavar='wav/mid', default='wav', choices=outformats.keys(), help='output format (default: %(default)s)')
        args=parser.parse_args()
        starttime = datetime.now()
        makeSong(args.instrument, args.seed, args.f)
        print("Generation took " + str(round((datetime.now() - starttime).total_seconds(), 3)) + "s")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        pass
    
