import glob
import os
import shutil

playerDrive = 'g'
# files = ['C:\\Users\\matte\\Documents\\Sound recordings\\1.m4a','C:\\Users\\matte\\Documents\\Sound recordings\\2.m4a']
files = glob.glob('E:\Japanese\AllJPod\mp3\*.mp3', recursive=True)
# music = ['C:\\Users\\matte\\Documents\\Sound recordings\\3.m4a']
music = glob.glob('E:\music\mp3\*.mp3', recursive=True)
# shuffle(files)
# shuffle(music)
dialogLen = len(files)
musicLen = len(music)

for f in glob.glob(f'{playerDrive}:\\*.mp3', recursive=True):
    os.remove(f)

songEvery = 2
songCount = 0
for i in range(0, 10):
    if i % songEvery == 0:
        shutil.copyfile(music[songCount % musicLen], f'{playerDrive}:\\a{(i + songCount):03d}.mp3')
        songCount += 1
    shutil.copyfile(files[i % dialogLen], f'{playerDrive}:\\a{(i + songCount):03d}.mp3')
