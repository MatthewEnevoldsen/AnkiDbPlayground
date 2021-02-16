import datetime
import glob
import json
import operator
import os
import re
import string
import JapDictParser as jdp
import Tokeniser
import KanjiXmlParser as kxp
from collections import namedtuple
from collections import Counter
from typing import List, Tuple, Set, Dict

import pandas as pd

from AnkiDbHelper import AnkiDbHelper
from AnkiDbReader import AnkiDbReader, AnkiVocab, AnkiSentence
from AnkiDb import AnkiDb

def main():
    with AnkiDb() as db:
        #a = AnkiDbHelper(db)
        #dbr = AnkiDbReader(a)
        #a.move_furi_and_clear()
        buildSenDict(db)
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
    basetoentry, conjugtobase = jdp.getmergedentries()


    allsentences  = r.getAllSentences()
    #jpod = [s for s in allsentences if s.id < 1000000000]
    #sentences = set(r.getNextWeekSentences() + jpod)
    sentences = allsentences


    def getbasewords(sen) -> List[str]:
        allwords = Tokeniser.maxlensqtokens(sen, conjugtobase)
        uniquewords = []
        for w in allwords:
            baseform = conjugtobase[w]
            if baseform not in uniquewords:
                uniquewords.append(baseform)
        return uniquewords

    senidtobasevocab: Dict[str, List[str]] = {s.id: getbasewords(s.jap) for s in sentences}
    wordCounts = Counter((v for vocab in senidtobasevocab.values() for v in vocab))
    for sen, vocab in senidtobasevocab.items():
        for w in [w for w in vocab if wordCounts[w] > 100]:
            vocab.remove(w)

    sentowords = {sen: '\n\n'.join((jdp.formatentries(baseword, basetoentry[baseword], 4) for baseword in basevocab)) for sen, basevocab in senidtobasevocab.items()}
    for s in allsentences:
        if s.id not in sentowords:
            sentowords[s.id] = '...'
    sentobasevocab: Dict[str, List[str]] = {s.jap: getbasewords(s.jap) for s in sentences}
    wordstosen: Dict[str, List[str]] = dict()
    for s, ws in sentobasevocab.items():
        for w in ws:
            if w in wordstosen:
                wordstosen[w].append(s)
            else:
                wordstosen[w] = [s]
    for w,s in wordstosen.items():
        s.sort(key=len)

    fcd = jdp.getfcdict(basetoentry)
    kanji = kxp.getKanji()
    def wordkanji(word):
        return [f'{kanji[w][0]} | {kanji[w][1]} | {kanji[w][2]} | {kanji[w][3]}' for w in word if w in kanji]

    chartowords = dict()
    for word, e in wordstosen.items():
        for c in word:
            if c in chartowords:
                chartowords[c].append(word)
            else:
                chartowords[c] = [word]

    for k, v in kanji.items():
        egs =  chartowords[k] if k in chartowords else []
        egs = sorted(egs,key= lambda eg: len(eg))
        egstext = [jdp.formatentries(w, basetoentry[w], 4) for w in egs]
        egtext = '\n\n'.join(egstext)
        v.append(egtext)





    #fcdict = [[w, fcd[w], '', len(s), 'jpod'] for w, s in wordstosen.items() if w in fcd and len(s) >= 0]
    #fcdict = [[w, fcd[w], '\n'.join(s[0:5])] for w, s in wordstosen.items() if w in fcd and len(s) >= 3]
    fcdict = [[w, fcd[w], '\n\n'.join(s[0:5]),  len(s), '\n'.join(wordkanji(w))] for w, s in wordstosen.items() if w in fcd and len(s) >= 3]
    print(len(fcdict))


    df = pd.DataFrame.from_dict(sentowords, orient='index')
    df.to_csv('c:/japanese/sentenceWithEDict.csv', header=False)
    dfv = pd.DataFrame.from_records(fcdict)
    dfv.to_csv('c:/japanese/jpodmissingvocab.csv', header=False, index=False)
    dfk = pd.DataFrame.from_dict(kanji, orient='index')
    dfk.to_csv('c:/japanese/kanji.csv', header=False)


    #emptydicts = {sen: '...' for sen, words in senVocab.items()}
    #dfclear = pd.DataFrame.from_dict(emptydicts, orient='index')
    #dfclear.to_csv('c:/japanese/clearsentencedicts.csv', header=False)
main()






