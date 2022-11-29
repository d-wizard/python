# Copyright 2022 Dan Williams. All Rights Reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
# to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
# 
import time
import wave
import struct
import os
import argparse

################################################################################

THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

################################################################################
def getFrames(wavFd, numFrames):
   numLeft = wavFd.getnframes() - wavFd.tell()
   numReadFrames = min(numLeft, numFrames)

   if numReadFrames <= 0:
      return []
   else:
      return struct.unpack("<" + "h" * numReadFrames, wavFd.readframes(numReadFrames))

def getAllFrames(wavFd):
   return getFrames(wavFd, wavFd.getnframes())

def splitToClips(wavFd, numSilenceForNewSound = 4410, silenceThreshold = 1):
   allFrames = getAllFrames(wavFd)
   retVal = []

   numSilenceCount = 0
   clipActive = False
   nonSilenceStartIndex = -1
   for index in range(len(allFrames)):
      if abs(allFrames[index]) > silenceThreshold:
         # Not a silence sample. Need to see if this starts a new clip
         if not clipActive:
            numSilenceCount = 0
            clipActive = True
            nonSilenceStartIndex = index
      else:
         # Silence Sample. Need to see if this ends a clip.
         numSilenceCount += 1
         if numSilenceCount >= numSilenceForNewSound:
            # Enough silence to indicate this is not part of a clip.
            if clipActive:
               clip = allFrames[nonSilenceStartIndex : index-numSilenceForNewSound+1]
               retVal.append(clip)
               clipActive = False
               nonSilenceStartIndex = -1

   return retVal

def saveClip(savePath, clipSamples, frameRate = 44100):
   wavFd = wave.open(savePath, 'wb')
   wavFd.setnchannels(1)
   wavFd.setsampwidth(2)
   wavFd.setframerate(frameRate)
   for samp in clipSamples:
      data = struct.pack('<h', samp)
      wavFd.writeframesraw(data)
   wavFd.close()


################################################################################
# Main start
if __name__== "__main__":
   # Config argparse
   parser = argparse.ArgumentParser()
   parser.add_argument("-s", type=str, action="store", dest="sourcePath", help="Path to the input wave file", default=None)
   parser.add_argument("-d", type=str, action="store", dest="destPath", help="Directory to store clips to.", default=None)
   args = parser.parse_args()

   # Validate input path
   filePath = args.sourcePath
   try:
      fileNameNoExt = os.path.splitext(os.path.split(filePath)[1])[0]
   except:
      print("Bad Input File Path")
      exit(0)

   # Validate output path
   outDir = args.destPath
   if outDir == None:
      outDir = os.path.join(THIS_SCRIPT_DIR, "clips")
   if not os.path.exists(outDir):
      os.makedirs(outDir)
   if not os.path.isdir(outDir):
      print("Bad Output Clip Directory")
      exit(0)

   # Read the file and split into clips
   wavFd = wave.open(filePath, 'rb')
   clips = splitToClips(wavFd)
   wavFd.close()

   # Save the clips as separate files.
   clipIndex = 0
   for clip in clips:
      savePath = os.path.join(outDir, fileNameNoExt + "_" + str(clipIndex) + ".wav")
      saveClip(savePath, clip, wavFd.getframerate())

      clipIndex += 1
   
