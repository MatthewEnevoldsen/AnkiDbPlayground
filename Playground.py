import shutil
import sqlite3
import json
import re
import glob
import string
import operator
import os
import datetime
from typing import List, Tuple, Set
from collections import namedtuple
from itertools import islice
import requests


for r in res:
    try:
        dir = f'c:\\japanese\\{r[0]}'
        if not os.path.exists(dir):
            os.mkdir(dir)
        d = r[1]
        filename = os.path.basename(d)
        downloadPath = f'{dir}\\{filename}'
        if not os.path.exists(downloadPath):
            r = requests.get(d, allow_redirects=True)
            
            open(downloadPath, 'wb').write(r.content)
    except:
        print(r)

def dl():
    res = set()
    for i in range(0, data['pathways-href'].count()):    
        season =  re.findall('.*/(.*?)/', data['pathways-href'][i])[0]
        dia = data['dialogue'][i]
        res.add((season, dia))
def getDialogs(season: str):
    dir = f'C:\\Japanese\\{season}'
    if not os.path.exists(dir):
        os.mkdir(dir)
    text = open(f'{dir}.csv', "r", encoding="UTF-8").read()
    dialogs = re.findall(f'https://mdn\\.illops\\.net/.*?dialog\\.mp3' ,text)
    for d in dialogs:
        filename = os.path.basename(d)
        downloadPath = f'{dir}\\{filename}'
        if not os.path.exists(downloadPath):
            r = requests.get(d, allow_redirects=True)
            open(downloadPath, 'wb').write(r.content)

def getJPodLinkedFiles(ext: str):
    jpod = "C:\Pod\Level2\lesson"
    allmp3s = set()
    for file in  glob.glob(jpod + '\**\*.htm', recursive=True):
        text = open(file, "r", encoding="UTF-8").read()
        matches = re.findall(f'http.*?\.{ext}' ,text)
        if not matches is None:
            for m in matches:
                allmp3s.add(m)
    print (len(allmp3s))
    for mp3 in allmp3s:
        filename = os.path.basename(mp3)
        downloadDir = 'E:\\Japanese\\AllJPod\\'
        downloadPath = downloadDir + filename
        if not os.path.exists(downloadPath):
            r = requests.get(mp3, allow_redirects=True)
            open(downloadPath, 'wb').write(r.content)
        courseDir = f'{downloadDir}level2jap'
        if not os.path.exists(courseDir):
            os.mkdir(courseDir)
        newPath = f'{courseDir}\\{filename}'
        if not os.path.exists(newPath):
            shutil.copyfile(downloadPath, newPath)
    print(len(allmp3s))
    print(len(glob.glob(courseDir + '\*')))
#getJPodLinkedFiles('pdf') 
#getJPodLinkedFiles('mp3')
