#needs patched wave:
import patchedwavelib as wave
import random, array, math
MAX = (1 << 15) - 1 # maximum short value, 32767
SAMPLE_RATE = 44100
DEFAULT_INSTRUMENT = 'square'

cache = dict()

'''Frequencies of notes
           C        C#       D        D#       E        F        F#       G        G#       A        A#       B
          16.35,   17.32,   18.35,   19.45,   20.60,   21.83,   23.12,   24.50,   25.96,   27.50,   29.14,   30.87, # 0
          32.70,   34.65,   36.71,   38.89,   41.20,   43.65,   46.25,   49.00,   51.91,   55.00,   58.27,   61.74, # 1
          65.41,   69.30,   73.42,   77.78,   82.41,   87.31,   92.50,   98.00,  103.83,  110.00,  116.54,  123.47, # 2
         130.81,  138.59,  146.83,  155.56,  164.81,  174.61,  185.00,  196.00,  207.65,  220.00,  233.08,  246.94, # 3
         261.63,  277.18,  293.66,  311.13,  329.63,  349.23,  369.99,  392.00,  415.30,  440.00,  466.16,  493.88, # 4 (Middle C)
         523.25,  554.37,  587.33,  622.25,  659.26,  698.46,  739.99,  783.99,  830.61,  880.00,  932.33,  987.77, # 5
        1046.50, 1108.73, 1174.66, 1244.51, 1318.51, 1396.91, 1479.98, 1567.98, 1661.22, 1760.00, 1864.66, 1975.53, # 6
        2093.00, 2217.46, 2349.32, 2489.02, 2637.02, 2793.83, 2959.96, 3135.96, 3322.44, 3520.00, 3729.31, 3951.07, # 7
        4186.01, 4434.92, 4698.64, 4978.03)'''
FREQS = [440 * 2 ** (x / 12.0) for x in range(-57, 43)]        

def squareWave(freq, sampleCount, vol):
    """sineWave
        freq - the frequency of the wave
        length - the length to play the wave for in milliseconds
        vol - the volume between 0 and 1"""
    innermult = 2 * freq / SAMPLE_RATE
    outermult = int(MAX * vol)
    values = initArray(sampleCount)
    for i in xrange(0, sampleCount):
        values[i] = (int(i * innermult) % 2 * 2 - 1) * outermult    
    return values

def guitarWave(freq, sampleCount, vol, damping=0.996):
    n = int(SAMPLE_RATE // freq) # noise loop filter length
    zn = array.array('h', [int((random.random() * 2 - 1) * MAX * vol) for i in xrange(0, n)]) # white noise (in real array for speed)
    
    values = initArray(sampleCount)
    for i in xrange(0, sampleCount):
        values[i] = zn[i % n] # read sample from current noise
        zn[i % n] = int((
                     zn[ i % n] * 2 + 
                     zn[(i + 1) % n] + 
                     zn[(i + 2) % n]
                    ) * 0.25 * damping) # an average filter (replacement for lowpass)
    return values
   

def sineWave(freq, sampleCount, vol):
    """sineWave
        freq - the frequency of the wave
        length - the length to play the wave for in milliseconds
        vol - the volume between 0 and 1"""
    # using the wavelength here would round it a lot, so we calculate 20 wavelengths
    # for example, instead of 440hz we actually use ~439.9
    calclength = min(sampleCount, int(round(20 * SAMPLE_RATE / freq)))
    innermult = 2 * math.pi * 20 / calclength
    outermult = MAX * vol
    values = initArray(sampleCount)
    for i in xrange(0, calclength):
        values[i] = int(math.sin(i * innermult) * outermult)
    for i in xrange(calclength, sampleCount):
        values[i] = values[i % calclength]
    
    smoothLength = min(sampleCount // 2, int(SAMPLE_RATE * 0.005))#smooth five seconds at the wave ends to remove cracking
    for i in xrange(0, smoothLength):
        values[i] = values[i] * i / smoothLength;
        values[-1 - i] = values[-1 - i] * i / smoothLength;
    return values

INSTRUMENTS = {'sine':sineWave, 'square':squareWave, 'guitar':guitarWave}

def cachedWaveGen(freq, length, waveType, vol=1):
    """cachedWaveGen
        note - the wave
        length - the length to play the wave for in milliseconds
        waveType - what kind of wave to make. This is a string.
        returns a string representing an 8 bit mono wave"""
    sampleCount = (SAMPLE_RATE * length) // 1000
    instrument = INSTRUMENTS.get(waveType, INSTRUMENTS.get(DEFAULT_INSTRUMENT))
    cachekey = (instrument, freq, sampleCount)
    if(cachekey not in cache):
        cache[cachekey] = instrument(freq, sampleCount, vol)
    return cache[cachekey]
    
def limit(n):
    """limit
        n - a number
        returns a number"""
    if (n > MAX):
        return MAX
    elif (n < -MAX):
        return -MAX
    return n

def mergeWaves(w1, w2):
    """mergeWaves - merge two waves together
        w1 - a wave
        w2 - a wave
        returns a new wave that is both combined"""
    l = max(len(w1), len(w2))
    w1.extend([0] * (l - len(w1))) # make sure they are long enough
    w2.extend([0] * (l - len(w2)))
    
    outwave = initArray(l)
    for i in xrange(0, l):
        outwave[i] = limit(w1[i] + w2[i]) # what todo: when one list is longer?
    return outwave
    #li=[schr(ord(a)+ord(b)-0x80) for (a,b) in izip_longest(wave1,wave2,fillvalue=0)]
    #return ''.join(li)
    
def initArray(size=0):
    return array.array('h', [0] * size)    

def makeWavFile(data, filename):
    """makeWave
        data - the wave to put into the file
        filename - the name of the file to open"""
    f = wave.open(filename, 'w')
    #f.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
    # don't use mono, sound will be cut off at half
    f.setparams((1, 2, SAMPLE_RATE, 0, 'NONE', 'not compressed'))
    f.writeframes(data)
    f.close()
    
    
''' int smoothLength = (int) (SAMPLE_RATE * 0.005);
        end--;
        for (int i = 0; i < smoothLength && i < end / 2; i++) {
            data[start + i] = (byte) (data[start + i] * i / smoothLength);
            data[end - i] = (byte) (data[end - i] * i / smoothLength);
        }'''
