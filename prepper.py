import os, sys
import scipy.io.wavfile as wave
import scipy.fftpack as fft
import numpy as np
import matplotlib.pyplot as plt

from math import log2, pow

A4 = 440
C0 = A4*pow(2, -4.75)
name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
def pitch(freq):
    p = (12*log2(freq/C0))
    h = round(p)
    rem = p - h
    rem = round( rem *100)
    
    octave = h // 12
    n = h % 12
    return name[n] + str(octave) + ' + ' + str(rem) + ' cents'


if '__file__' in locals():
    #print('running from file')
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

else:
    #print('running in IDE')
    os.chdir('C:/users/peter/Google Drive/sampler prep')


files = os.listdir(os.getcwd())
#print(files)
if not os.path.isfile('settings.txt'):
   
    f = open('settings.txt','w+')
    f.write('''zeroThreash=0.01
zeroLength=0.01
minSampleLength=0.2
preDelay=0.1
postDelay=1''')
    
    f.close()
else:
    f = open('settings.txt')
    settings = f.readlines()
    f.close()
    #print (settings)
    
    settingsDict= {}
    for line in settings:
        if '=' in line:
            line = line.replace(' ','')
            line = line.split('#', 1) [0]
            line = line.rstrip()
            #print (line)
            fields = line.split('=')
            #print (fields)
            settingsDict[fields[0]] = fields[1]
        
    #print (settingsDict)
    
    for file in files:
        if file.endswith('.wav'):
            
            #print (file)
            fs, data = wave.read(file)
            zeroLengthSamples = round(float(settingsDict['zeroLength']) * fs)
            

            
            preDelaySamples = int(float(settingsDict['preDelay']) * fs)
            postDelaySamples = int(float(settingsDict['postDelay']) * fs)
            minSampleLengthSamples = int(float(settingsDict['minSampleLength']) * fs)
            
            left = data[:,0]
            right = data[:,1]
            monoRectified = (abs(left) / 2) + (abs(right) / 2)
            monoRectified = monoRectified.astype('int')
            
            monoEnvelopeSmooth = np.convolve(monoRectified, np.ones((zeroLengthSamples,)) / zeroLengthSamples, mode = 'full')
            monoEnvelopeSmooth = monoEnvelopeSmooth.astype('int')
            
            waveMax = max( np.iinfo(left.dtype).max, -np.iinfo(left.dtype).min)
            zeroThreashWindow = round(float(settingsDict['zeroThreash']) * waveMax)
            
            
            clips = [] 
            currentclip = [0, 0]
            lastend = 0
            inclip = False
            for i in range(len(monoEnvelopeSmooth)):
                point = int(monoEnvelopeSmooth[i])
                if not inclip and point > zeroThreashWindow:
                     inclip = True
                     currentclip[0] = max (lastend, i - preDelaySamples)
                if inclip and point < zeroThreashWindow  :
                     inclip = False
                     lastend = min (i + preDelaySamples, len(monoEnvelopeSmooth) - 1)
                     currentclip[1] = lastend
                     length = currentclip[1] - currentclip[0]
                     if length > minSampleLengthSamples:
                        clips.append(currentclip) 
                        currentclip = [0, 0]                        
            print (clips)
                     
            
            plt.figure(figsize=(10,10))
            plt.plot(monoRectified)
            plt.plot(monoEnvelopeSmooth)
            plt.plot([0, monoRectified.size], [zeroThreashWindow, zeroThreashWindow], c = 'red')
            plt.scatter(np.array(clips)[:,0], zeroThreashWindow * np.ones(len(clips)), c = 'black', s = 2)
            plt.scatter(np.array(clips)[:,1], zeroThreashWindow * np.ones(len(clips)), c = 'grey', s = 2)
            plt.savefig(file +'.jpg', dpi = 500)
            
            clipno = 1
            if 'output' not in files:
                os.mkdir('output')
            os.chdir('output')
            for clip in clips:
                clipData = data[clip[0]:clip[1]]
                spec = abs(fft.rfft(clipData[:,0]))
                bins = fft.rfftfreq(clipData[:,0].shape[0], 1 / fs)
                freq = float(bins[spec.argmax()])
                if freq > 0:
                    clipFilename = str(clipno) + ' ' + file[0:-4] + ' ' + pitch(freq) + '.wav'
                    clipno += 1
                    wave.write(clipFilename, fs, clipData)
            os.chdir('..')
            
            