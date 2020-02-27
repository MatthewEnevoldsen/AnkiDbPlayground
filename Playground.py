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
getJPodLinkedFiles('mp3')
