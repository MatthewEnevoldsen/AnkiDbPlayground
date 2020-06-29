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
    sentences = [s for s in r.getNextWeekSentences()]#r.getAllSentences()]# if s.id < 1000000000]
    merged = jdp.getmergedentries()
    japengdict: Dict[str,str] = jdp.getconjtoword(merged)

    def getwords(sen) -> List[str]:
        allwords = Tokeniser.splittowords(sen, japengdict)
        uniquewords = []
        for w in allwords:
            baseform = japengdict[w]
            if baseform not in uniquewords:
                uniquewords.append(baseform)
        return uniquewords
    senVocab: Dict[str, List[str]] = {s.id: getwords(s.jap) for s in sentences}

    sentowords = {sen: '\n\n'.join((jdp.formatentries(merged[word], 4) for word in words)) for sen, words in senVocab.items()}

    fcd = jdp.getfcdict()
    allwords = {v for vocab in senVocab.values() for v in vocab}
    limitedfcdict = {w: fcd[w] for w in allwords if w in fcd}




    df = pd.DataFrame.from_dict(sentowords, orient='index')
    df.to_csv('c:/japanese/sentenceWithEDict.csv', header=False)
    df2 = pd.DataFrame.from_dict(limitedfcdict, orient='index')
    df2.to_csv('c:/japanese/jpodmissingvocab.csv', header=False)

    #emptydicts = {sen: '...' for sen, words in senVocab.items()}
    #dfclear = pd.DataFrame.from_dict(emptydicts, orient='index')
    #dfclear.to_csv('c:/japanese/clearsentencedicts.csv', header=False)
fuckWithStuff()






