#########################################################################################################
# Simple tool I made for syncing visual effects to music for some animations I created                  #
# Make sure frame files are named numerically in suffix                                                 #
# Results vary greatly so you may want to use something like Audacity to enhance the qualities you want #
#########################################################################################################
debug = True

import sys
import subprocess
import os
import time

#Install dependencies
def installdependencies(modulename):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', modulename])
    except:
        print('Failed to install module "' + modulename + '"')
installdependencies('turtle')
installdependencies('simpleaudio')
installdependencies('Pillow')
installdependencies('numpy')
installdependencies('scipy')
os.system('cls')

import turtle
from scipy.io.wavfile import read
from PIL import Image
import simpleaudio as sa
import numpy

def smoothListGaussian(list, degree=3):
    window = degree*2-1
    weight = numpy.array([1.0]*window)
    weightGauss = []
    for i in range(window):
        i = i-degree+1
        frac = i/float(window)
        gauss = 1/(numpy.exp((4*(frac))**2))
        weightGauss.append(gauss)
    weight = numpy.array(weightGauss)*weight
    smoothed = [0.0]*(len(list)-window)
    for i in range(len(smoothed)):
        smoothed[i] = sum(numpy.array(list[i:i+window])*weight)/sum(weight)
    return smoothed

soundfilePath = input('Sound file path (.wav):')
answer = input('Use same sound file for previewing? (y/n)')
if(answer == 'y'):
    previewsoundfilepath = soundfilePath
else:
    previewsoundfilepath = input('Sound file path for preview (.wav):')
framefilepath = input('Frame folder directory:')
savefilepath = input('Frame output path:')

#Load sound preview
wave_object = sa.WaveObject.from_wave_file(previewsoundfilepath)
#Format directories
if savefilepath[-1:] != '\\':
    savefilepath += '\\'
if framefilepath[-1:] != '\\':
    framefilepath += '\\'
#Set variables
samplerate, data = read(soundfilePath)
length = data.shape[0] / samplerate
monodata = (abs(data[:,0]) + abs(data[:,1])) / 2
frames = int(len(os.listdir(framefilepath)))
datawindow = int(len(monodata) / frames)
averageperframe = []
highestvalue = 0
lowestvalue = int(monodata[0])
#Calculate average per frame
for i in range(0, frames):
    average = int(sum(monodata[(i * datawindow): ((i + 1)*datawindow)]) / datawindow)
    if average < lowestvalue and average != 0:
        lowestvalue = average
    if average > highestvalue:
        highestvalue = average
    averageperframe.append(average)
#Subtract lowest value so floor is at 0
for i in range(0, frames):
    averageperframe[i] -= lowestvalue
#Set new highest value with floor, calculate total average
highestvalue -= lowestvalue
totalaverage = int(sum(averageperframe) / frames)
adjusting = True
os.system('cls')
print('Audio average: ' + str(totalaverage) + ', max value of ' + str(highestvalue))

while adjusting:
    smoothammount = int(input('Output smoothness adjustment (helps w/ coherancy & reduces flicker):'))
    maxsuggestion = int(highestvalue - (highestvalue / 5))
    setmax = int(input('Set audio ceiling (a good value would be ~' + str(maxsuggestion) + '):'))
    tolerancelevel = int(input('Set tolerance level (a good value would be ~' + str(int(totalaverage)) + '):'))
    answer = input('Invert output?(y/n)')
    if answer == 'y':
        invert = True
    else:
        invert = False
    #More filtering
    for i in range(0, frames):
        frameavg = averageperframe[i]
        if frameavg < tolerancelevel:
            averageperframe[i] = 0
        elif frameavg > setmax:
            averageperframe[i] = setmax
        else:
            averageperframe[i] -= tolerancelevel
    #Add buffer and smooth data
    averageperframe += [0] * 50
    smoothedframeaverage = smoothListGaussian(averageperframe, smoothammount)
    #Order frames numerically
    framefiles = os.listdir(framefilepath)
    orderedframes = [None] * (len(framefiles) + 1)
    for i in range(0, len(framefiles)):
        if framefiles[i][-4:] == '.png' or framefiles[i][-4:] == '.jpg':
            framefilename = framefiles[i][:-4]
            cutindex = 0
            for char in reversed(range(0, len(framefilename))):
                if not framefilename[char:char+1].isdigit:
                    cutindex = char + 1
                    break
            framnum = int(framefilename[cutindex:])
            orderedframes[framnum] = framefiles[i]
    answer = input('Preview results?(y/n)')
    if answer == 'y':
        preview = True
    else:
        preview = False
    #Preview window
    if preview:
        wn = turtle.Screen()
        root = wn.getcanvas().winfo_toplevel()
        wn.title("Preview")
        wn.setup(width=500, height=500)
        wn.tracer(0)
        #Window close handler
        running = True
        def on_close():
            global running
            running = False
            wn.bye()
        if running:
            root.protocol("WM_DELETE_WINDOW", on_close)
            fps = frames / length
            frame = 1
            play_object = wave_object.play()
            start = time.time()
            while frame < frames and running:
                duration = (time.time() - start)
                frame = int(fps * duration)
                print('Frame ' + str(frame))
                alphavalue = (smoothedframeaverage[frame] / setmax)
                wn.bgcolor(alphavalue, alphavalue, alphavalue)
                wn.update()
                if not running:
                    break
    answer = input('Would you like to tweak the settings again?(y/n)')
    if answer == 'n':
        adjusting = False

answer = input('Save frame transparency data to ' + str(savefilepath) + '?(y/n)')
if answer == 'y':
    save = True
else:
    save = False
#Save alpha value to frames and copy to output destination
if save:
    start = time.time()
    for i in range(1, frames):
        file = str(orderedframes[i])
        if invert:
            alphavalue = int(255 - (255 * (smoothedframeaverage[i] / setmax)))
        else:
            alphavalue = int(255 * (smoothedframeaverage[i] / setmax))
        print(str(int((i / frames) * 100)) + '% ' + orderedframes[i])
        img = Image.open(str(framefilepath + file)).copy()
        img.putalpha(alphavalue)
        img.save(str(savefilepath + file))
    print('Processed in ' + str(int(time.time() - start)) + 's')