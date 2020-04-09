import datetime
import glob
import json
import operator
import os
import re
import string
from collections import namedtuple
from typing import List, Tuple, Set, Dict

import pandas as pd

from AnkiDbHelper import AnkiDbHelper
from AnkiDbReader import AnkiDbReader, AnkiVocab, AnkiSentence
from AnkiDb import AnkiDb

def fuckWithStuff():
    with AnkiDb() as db:
        a = AnkiDbHelper(db)
        #buildSenDict(db)
        x = 3
        #a.Unsuspend10k("C:\\Japanese\\begsen.csv")
        #a.reindex('Core10K', force=True)
        a.reindex('AllSentences')
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


def buildSenDict(db):
    r = AnkiDbReader(db)
    vocab = r.allVocab()
    vocabCache: Dict[str, List[AnkiVocab]] = dict()
    for v in vocab:
        if not v.baseVocab() in vocabCache:
            vocabCache[v.baseVocab()] = []
        vocabCache[v.baseVocab()].append(v)
    sentences = r.getAllSentences()
    senVocab: Dict[str, List[AnkiVocab]] = {s.id: [] for s in sentences}
    for s in sentences:
        for p in s.potentialWords():
            if p in vocabCache:
                for v in vocabCache[p]:
                    senVocab[s.id].append(v.dictForm())
    result = {s: '\n'.join(v) for s, v in senVocab.items()}
    df = pd.DataFrame.from_dict(result, orient='index')
    df.to_csv('sentenceWithDict.csv')

with AnkiDb() as db:
    buildSenDict(db)