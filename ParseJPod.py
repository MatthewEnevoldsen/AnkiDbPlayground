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

allMp3s = set()
for course in glob.glob('C:\Pod\level1\lesson\**\index.htm', recursive=true):
    html = open(course, "r", encoding="UTF-8").read()
    matches = re.findall('http.*?mp3', testHtml)
    if not matches is None:
            for m in matches:
                allmp3s.add(m)
