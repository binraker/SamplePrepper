import os, sys
import scipy.io.wavfile as wave
import scipy.fftpack as fft
import numpy as np
import matplotlib.pyplot as plt

from math import log2, pow

settingsDict={
'startThreash': '0.01',
'endThreash': '0.005',
'zeroLength': '0.01',
'minSampleLength': '0.2',
'preDelay': '0.1',
'postDelay': '0.25',
'retune' : 'true'
}

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
    
    basefreq = C0 * pow(2, h / 12 )   
    return name[n] + str(octave),  str(rem), basefreq
    
    
    
    
def getFreq(clipData, fs):
    spec = (abs(fft.rfft(clipData[:,0])) + abs(fft.rfft(clipData[:,1]))) / 2
    bins = fft.rfftfreq(clipData[:,0].shape[0], 1 / fs)
    return float(bins[spec.argmax()])




    
    
    
    
    
    
    

if '__file__' in locals():
    #print('running from file')
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

else:
    #print('running in IDE')
    os.chdir('C:/Users/User/Documents/GitHub/SamplePrepper')


files = os.listdir(os.getcwd())
#print(files)
if not os.path.isfile('settings.txt'):
   
    f = open('settings.txt','w+')
    f.write('# outputs data as <clip number> <filename> <note> <cents> <volume> <round robin>\n')
    for setting in settingsDict:
        f.write(setting + '=' + settingsDict[setting] +'\n')
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
            
            print (file)
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
            startThreashWindow = round(float(settingsDict['startThreash']) * waveMax)
            endThreashWindow = round(float(settingsDict['endThreash']) * waveMax)
            
            clips = [] 
            currentclip = [0, 0]
            lastend = 0
            inclip = False
            for i in range(len(monoEnvelopeSmooth)):
                point = int(monoEnvelopeSmooth[i])
                if not inclip and point > startThreashWindow:
                     inclip = True
                     currentclip[0] = max (lastend, i - preDelaySamples)
                if inclip and point < endThreashWindow  :
                     inclip = False
                     lastend = min (i + postDelaySamples, len(monoEnvelopeSmooth) - 1)
                     currentclip[1] = lastend
                     length = currentclip[1] - currentclip[0]
                     if length > minSampleLengthSamples:
                        clips.append(currentclip) 
                        currentclip = [0, 0]                        
            
            plt.figure(figsize=(10,10))
            plt.plot(monoRectified)
            plt.plot(monoEnvelopeSmooth)
            plt.plot([0, monoRectified.size], [startThreashWindow, startThreashWindow], c = 'red')
            plt.plot([0, monoRectified.size], [endThreashWindow, endThreashWindow], c = 'green')
            plt.scatter(np.array(clips)[:,0], startThreashWindow * np.ones(len(clips)), c = 'black', s = 6, zorder = 5)
            plt.scatter(np.array(clips)[:,1], endThreashWindow * np.ones(len(clips)), c = 'grey', s = 6, zorder = 5)
            plt.savefig(file +'.jpg', dpi = 500)
            
            clipno = 1
            if 'output' not in files:
                os.mkdir('output')
            os.chdir('output')
            
            notes = {}
            
            print ('clips found: ' + str(len(clips)))
            
            for clip in clips:
                clipData = data[clip[0]:clip[1]]
                freq = getFreq(clipData, fs)
               # spec = (abs(fft.rfft(clipData[:,0])) + abs(fft.rfft(clipData[:,1]))) / 2
               # bins = fft.rfftfreq(clipData[:,0].shape[0], 1 / fs)
               # freq = float(bins[spec.argmax()])
                note, cents, base = pitch(freq)
                if freq > 0:
                    if note in notes:
                        notes[note] += 1
                    else:
                        notes[note] = 0
                    
                    if settingsDict['retune'].lower() == 'true':
                        retuneAmount = freq / base
                        originalLength = clipData.shape [0]
                        retunedlength = int(originalLength * retuneAmount)
                        leftData = clipData[:, 0]
                        rightData = clipData[:, 1]
                        retuned = np.empty([retunedlength, 2])
                        retuned[:, 0] = np.interp(np.arange(retunedlength)/(retunedlength/originalLength),np.arange(originalLength), leftData)
                        retuned[:, 1] = np.interp(np.arange(retunedlength)/(retunedlength/originalLength),np.arange(originalLength), rightData)
                        clipData = retuned
                    
                    volume = int((float(max(clipData.max(), -clipData.min())) / waveMax) * 127)
                    clipFilename = str(clipno) + ' ' + file[0:-4] + ' ' + note + ' ' + cents + ' ' + str(volume)+ ' ' + str(notes[note]) + '.wav'
                    print ('saving: ' + clipFilename)
                    clipno += 1
                    wave.write(clipFilename, fs, clipData)
            os.chdir('..')