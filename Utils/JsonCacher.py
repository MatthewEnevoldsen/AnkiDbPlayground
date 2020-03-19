import datetime
import glob
import json
import operator
import os
import re
import string
from collections import namedtuple
from typing import List, Tuple, Set

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

def setDiskCache(filePath, setGetter, toPython):
    if not os.path.isfile(filePath):
        with open(filePath, "w", encoding="UTF-8") as fp:
            json.dump(setGetter(), fp, ensure_ascii=False)
    with open(filePath, "r", encoding="UTF-8") as read_file:
        return toPython(json.load(read_file))



