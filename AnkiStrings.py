import datetime
import glob
import json
import operator
import os
import re
import string
from Utils.JsonCacher import setDiskCache
from collections import namedtuple
from typing import List, Tuple, Set, Sequence, Dict

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

class AnkiStrings:
    def getSenRatios(self, sentences:Sequence[str], allwords:Set[str], knownwords:Set[str]) -> Dict[str,float]:
        def getter():
            allbasewords = {self.toBaseVocab(s) for s in allwords}
            knownbasewords = {self.toBaseVocab(s) for s in knownwords}
            tokens = self.tokenise(sentences, allbasewords)
            res = dict()
            for t in tokens.items():
                allCount = len(t[1])
                knownCount = len(set((v for v in t[1] if v in knownbasewords)))
                res[t[0]] = 0 if allCount == 0 else knownCount / allCount
            return res

        return setDiskCache('senRatios.json', getter, lambda o: o)

    def tokenise(self, sentences: Sequence[str], tokens: Set[str])->Dict[str, Set[str]]:
        def getter():
            return  {s:set((v for v in self.splitDownWord(s) if v in tokens)) for s in sentences}
        def fix(o):
            return {t[0]:t[1] for t in o.items()}
        return setDiskCache('tokenised.json', getter, fix)

    def splitDownWord(self, sentence: str):
        max = min(len(sentence) + 1, 10)
        res = set()
        for l in range(1, max):
            for s in range(0, len(sentence) - l + 1):
                res.add(sentence[s:s + l])
        return res

    def toBaseVocab(self, raw: str) -> str:
        ends = "うくづつるぬむすぐぶい"
        if len(raw) == 0:
            return raw
        return raw[0:-1] if raw[-1] in ends else raw

    def find_all(self, a_str, sub):
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1: return
            yield start
            start += len(sub)

    def stripNoise(self, s: str) -> str:
        furi = re.compile('(?:\[[ぁ-んァ-ン]{1,8}?\])|(<\/?b>)| |\t')
        return furi.sub("", s).strip()

    def stripTags(self, s: str) -> str:
        furi = re.compile('(<\/?b>)|\t')
        return furi.sub("", s).strip()

    def splitJapEng(self, s: str) -> Tuple[str, str]:
        split = self.findSplit(s)
        return (self.stripNoise(s[0:split]), s[split + 1:].strip())

    def findSplit(self, s: str):
        def countEng(s: str):
            letters = set(string.ascii_letters)
            return len(list(filter(lambda c: c in letters, s)))
        scores = dict()
        for split in self.find_all(s, " "):
            left = s[split - 1::-1]
            right = s[split:]
            leftEngRatio = countEng(left) / (len(left) + 1)
            rightEngRatio = countEng(right) / (len(right) + 1)
            scores[split] = rightEngRatio - leftEngRatio
        return max(scores.items(), key=operator.itemgetter(1))[0]