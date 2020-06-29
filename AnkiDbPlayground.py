import datetime
import glob
import json
import operator
import os
import re
import string
import JapDictParser as jdp
import Tokeniser
from collections import namedtuple
from typing import List, Tuple, Set, Dict

import pandas as pd

from AnkiDbHelper import AnkiDbHelper
from AnkiDbReader import AnkiDbReader, AnkiVocab, AnkiSentence
from AnkiDb import AnkiDb

def fuckWithStuff():
    with AnkiDb() as db:
        a = AnkiDbHelper(db)
        #a.move10ktoedict()
        buildSenDict(db)
        #dbr = AnkiDbReader(a)
        #print(a.Unsuspend10k("C:\\Japanese\\intsen_anki.csv", 50000000))

        #notes = dbr.getNotesOfType('WordKanjiStats')
        # for n in notes:
        #     h = a.getField(n.flds, 0)
        #     new = re.sub('</?h1>', '', h)
        #     a.updateField(n, 0, new)
        #a.session.commit()
        #print(a.negativeCards())
        #a.archiveRevlog()
        #print(a.suspend_unseen())
        #a.remove_bad_furi()
        #print(a.UnsuspendSeen())
        #a.reindex('Core10K', force=True)
        #a.reindex('AllSentences')
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
    sentences = [s for s in r.getAllSentences() if s.id < 1000000000]
    japengdict = jdp.getsentencedict()
    senVocab: Dict[str, List[str]] = {s.id: list() for s in sentences}
    for s in sentences:
        allwords = Tokeniser.splittowords(s.jap, japengdict)
        uniquewords = []
        for w in allwords:
            if w not in uniquewords:
                uniquewords.append(w)
        senVocab[s.id] = uniquewords
    result = {sen: '\n\n'.join((japengdict[word] for word in words)) for sen, words in senVocab.items()}
    fcd = jdp.getfcdict()

    allwords = {v for vocab in senVocab.values() for v in vocab}



    limitedfcdict = {w: japengdict[w] for w in allwords if w in fcd}

    
    df2 = pd.DataFrame.from_dict(limitedfcdict, orient='index')

    df = pd.DataFrame.from_dict(result, orient='index')
    #df['sen'] = df.apply(lambda r: sentences[int(r[0])].jap)
    df.to_csv('c:/japanese/sentenceWithEDict.csv', header=False)
    df2.to_csv('c:/japanese/jpodmissingvocab.csv', header=False)
fuckWithStuff()






