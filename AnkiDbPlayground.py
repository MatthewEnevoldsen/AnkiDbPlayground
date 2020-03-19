import datetime
import glob
import json
import operator
import os
import re
import string
from collections import namedtuple
from typing import List, Tuple, Set
from AnkiDbWrapper import AnkiDbHelper
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

core10kId = 1342706442509
realDbPath = f"C:/Users/matte/AppData/Roaming/Anki2/Tirinst/collection.anki2"
dbPath = realDbPath


def fuckWithStuff():
    with AnkiDbHelper() as a:
        a.Unsuspend10k("C:\\Japanese\\begsen.csv")
        #a.combineNotes('KanjiRTK', lambda f: f[0])
        #x = a.getAllVocabSet()
        #y = a.getKnownVocabSet()


    #setSource(session, Col,Notes, "taekim", 3)
    # tagjpod(session, Notes)
    # r = getSenKnownRatios(session, Notes, Cards, Col)
    # tagSenRatios(session,Notes,Cards, Col, r)
    # knownWords = getKnownVocabSet(session, Notes,Cards)
    # Tag10KWhere(session, Notes, lambda vocab: toBaseVocab(vocab) in knownWords, "Known")
    # tagSenRatios(session, Col,Notes, Cards)
fuckWithStuff()