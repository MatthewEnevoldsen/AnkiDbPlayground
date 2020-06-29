import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List
import pandas as pd
from operator import or_
from functools import reduce

df = pd.read_csv('c:/japanese/kwswords.csv')
df['xml'] = df['html'].apply(lambda h: f'<all>{h}</all>')





@dataclass
class Meaning:
    pos: str
    eng: str

@dataclass
class Word:
    reading: str
    meanings: List[Meaning]

    def meaning(self):
        return' '.join([f'({i + 1}):{self.meanings[i].eng}' for i in range(0, min(4, len(self.meanings)))])

    def allpos(self):
        pos =  {p for m in self.meanings for p in m.pos.strip('[]').split(',')}
        return ','.join(pos)


def getwords(str) -> List[Word]:
     xml = ET.fromstring(str)
     words = [getword(child) for child in xml if iswordcard(child)]
     return words

def iswordcard(xml) -> bool:
     wc = 'word-card'
     c = 'class'
     d = 'div'
     return xml.tag == d and c in xml.attrib and wc in xml.attrib[c]



def findbyclass(xml, attrib):
    ctag = 'class'
    for c in xml:
        if ctag in c.attrib and c.attrib[ctag] == attrib:
            return c

def getword(xml) -> Word:
    r = xml.find('h3').text
    meanings = [Meaning(findbyclass(li, 'pos-desc').text, findbyclass(li, 'gloss-desc').text) for li in xml.find('div').find('ol').findall('li')]
    return Word(r, meanings)


def getorblank(ws: List[Word], i: int, prop) -> str:
    if len(ws) > i:
        return prop(ws[i])
    else:
        return ''
for i in range(0,4):
     df[f'reading{i+1}'] = df['xml'].apply(getwords).apply(lambda ws: getorblank(ws, i, lambda w: w.reading))
     df[f'reading{i+1}'] = df['xml'].apply(getwords).apply(lambda ws: getorblank(ws, i, lambda w: w.reading))
     df[f'pos{i+1}'] = df['xml'].apply(getwords).apply(lambda ws: getorblank(ws, i, lambda w: w.allpos()))
     df[f'eng{i+1}'] = df['xml'].apply(getwords).apply(lambda ws: getorblank(ws, i, lambda w: w.meaning()))
 df[['vocab', 'reading1', 'pos1', 'eng1', 'reading2', 'pos2', 'eng2', 'reading3', 'pos3', 'eng3', 'reading4', 'pos4', 'eng4']].to_csv('c:/japanese/testyboy.csv')