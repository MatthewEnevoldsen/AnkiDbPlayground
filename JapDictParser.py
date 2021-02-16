import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Set, Pattern, Tuple

from Utils.windows import *
import pandas as pd

@dataclass
class EdictEntry:
    @dataclass
    class Entry:
        text: str
        tags: List[str]

    kanji: List[Entry]
    kana: List[Entry]
    pos: List[str]
    engdefs: List[Entry]
    p: bool
    id: int

    def __hash__(self):
        return self.id
    def __eq__(self, other):
        return self.id == other.id

@dataclass()
class VocabDeck:
    Kanji1: str
    Kanji2: str
    definitions: str

def getwordconjugations(word:str, pos:str) -> Set[str]:
    # def mainverbforms():
    #     @dataclass()
    #     class V1Form:
    #
    #     class V5Forms:
    #         neg: str
    #         past: str
    #         te: str
    #         stem: str
    #         command: str
    #         vol: str
    #
    #         def __init__(self, word):
    #             x = {
    #                 'う':  ('わ', 'った', 'って', 'い', 'え', 'おう'),
    #                 'く': ('か', 'いた', 'いて', 'き', 'け', 'こう'),
    #                 'ぐ': ('が', 'いだ', 'いで', 'ぎ', 'げ', 'ごう'),
    #                 'す': ('さ', 'した', 'して', 'し', 'せ', 'そう'),
    #                 'つ': ( 'た', 'った', 'って', 'ち', 'て', 'とう'),
    #                 'ぬ': ( 'な', 'んだ', 'んで', 'に', 'ね', 'のう'),
    #                 'ぶ': ( 'ば', 'んだ', 'んで', 'び', 'べ', 'ぼう'),
    #                 'む': ( 'ま', 'んだ', 'んで', 'み', 'め', 'もう'),
    #                 'る': ( 'ら', 'った', 'って', 'り', 'れ', 'ろう')
    #             }
    #             end = word[-1]
    #             self.neg = word[0: -1] + x[end][0]
    #             self.past = word[0: -1] + x[end][1]
    #             self.te = word[0: -1] + x[end][2]
    #             self.stem = word[0: -1] + x[end][3]
    #             self.command = word[0: -1] + x[end][4]
    #             self.vol = word[0: -1] + x[end][5]
    #
    #         def passive(self):
    #             return self.neg + 'れる'
    #         def causive(self):
    #             return self.neg + 'せる'
    #         def neg(self):
    #             return self.neg + 'ない'
    #         def pastneg(self):
    #             return self.neg + 'なかった'
    #         def mas(self):
    #             return self.stem + 'ます'
    #         def maspast(self):
    #             return self.stem + 'ました'
    #         def masneg(self):
    #             return self.stem + 'ません'
    #         def masnegpast(self):
    #             return self.stem + 'ませんでした'
    #         def accidential(self):
    #             return self.te + 'しまう'
    #         def accidentialabbrev(self):
    #             return self.accidential().replace('てし','ちゃ').replace('でし','じゃ')
    #         def ifba(self):
    #             return self.command + 'ば'
    #         def negte(self):
    #             return self.na + 'くて'
    #         def negifbe(self):
    #             return self.neg + 'ければ'
    #         def negteabbrev(self):
    #             return self.neg + 'くちゃ'
    #         def negifbeabbrev(self):
    #             return self.stem + 'きゃ'
    #         def enders(self):
    #             return ['', '']
    #
    #     x = {'v1': ['', 'た', 'て', '', 'られ', 'ろ', 'よう'],
    #            'v5u': ['わ', 'った', 'って', 'い', 'え', 'わせ', 'われ', 'おう', 'わない', 'わなかった', 'わなきゃ', 'わなくちゃ', 'わなくて', 'わければ', 'じゃた', '', '', ''],
    #            'v5k': ['か', 'いた', 'いて', 'き', 'け', 'かせ', 'かれ', 'こう', 'かない', 'かなかった', 'かなきゃ', 'かなくちゃ', 'かなくて', ''],
    #            'v5g': ['が', 'いだ', 'いで', 'ぎ', 'げ', 'がせ', 'がれ', 'ごう', 'がない', 'がなかった', 'がなきゃ', 'がなくちゃ', 'がなくて', ''],
    #            'v5s': ['さ', 'した', 'して', 'し', 'せ', 'させ', 'され', 'そう', 'さない', 'さなかった', 'さなきゃ', 'さなくちゃ', 'さなくて', ''],
    #            'v5t': ['た', 'った', 'って', 'ち', 'て', 'たせ', 'たれ', 'とう', 'たない', 'たなかった', 'たなきゃ', 'たなくちゃ', 'たなくて', ''],
    #            'v5n': ['な', 'んだ', 'んで', 'に', 'ね', 'なせ', 'なれ', 'のう', 'なない', 'ななかった', 'ななきゃ', 'ななくちゃ', '', ''],
    #            'v5b': ['ば', 'んだ', 'んで', 'び', 'べ', 'ばせ', 'ばれ', 'ぼう', 'ばない', 'ばなかった', 'ばなきゃ', 'ばなくちゃ', '', ''],
    #            'v5m': ['ま', 'んだ', 'んで', 'み', 'め', 'ませ', 'まれ', 'もう', 'まない', 'まなかった', 'まなきゃ', 'まなくちゃ', '', ''],
    #            'v5r': ['ら', 'った', 'って', 'り', 'れ', 'らせ', 'られ', 'ろう', 'らない', 'らなかった', 'てください', 'て', 'らなきゃ', 'らなくちゃ', '', ''],
    #            }
    #     def wordforms(word, neg, past, te, stem, command, vol) -> V5Forms:
    #         return V5Forms(word[0:-1] + neg, word[0:-1] + past, word[0:-1] + te, word[0:-1] + stem, word[0:-1] + command, word[0:-1] + vol)
    #     v5forms: Dict[str, V5Forms] = {
    #            'v5u': wordforms(word, 'わ', 'った', 'って', 'い', 'え', 'おう'),
    #            'v5k': wordforms(word, 'か', 'いた', 'いて', 'き', 'け', 'こう'),
    #            'v5g': wordforms(word, 'が', 'いだ', 'いで', 'ぎ', 'げ', 'ごう'),
    #            'v5s': wordforms(word, 'さ', 'した', 'して', 'し', 'せ', 'そう'),
    #            'v5t': wordforms(word, 'た', 'った', 'って', 'ち', 'て', 'とう'),
    #            'v5n': wordforms(word, 'な', 'んだ', 'んで', 'に', 'ね', 'のう'),
    #            'v5b': wordforms(word, 'ば', 'んだ', 'んで', 'び', 'べ', 'ぼう'),
    #            'v5m': wordforms(word, 'ま', 'んだ', 'んで', 'み', 'め', 'もう'),
    #            'v5r': wordforms(word, 'ら', 'った', 'って', 'り', 'れ', 'ろう')
    #     }
    #
    #
    #     def negcommand(form: Forms):
    #         return form.dictionary + 'な'
    #
    #     return {f.past, f.te, f.pos, f.neg + 'せ', f.neg + 'れ', f.vol, f.neg + 'ない', f.neg + 'なかった', f.neg + 'なきゃ',f.neg + 'なくちゃ',
    #             f.neg + 'なければ', f.te + 'しまった', (f.te + 'しまった').replace('てしま','ちゃ').replace('でしま','じゃ'), f.neg + 'なければ'}
    #

    verbEndings = {'v1': ['た','て','られ','させ','られ','よう','ない','なかった','てください','なきゃ','なくちゃ','なければ','じゃう','てしま'],
                'v5u': ['わな','った','って','い','え','わせ','われ','おう','わない','わなかった','わなきゃ','わなくちゃ','わなくて','わければ','じゃた'],
                'v5k': ['かな','いた','いて','き','け','かせ','かれ','こう','かない','かなかった','かなきゃ','かなくちゃ','かなくて'],
                'v5g': ['がな','いだ','いで','ぎ','げ','がせ','がれ','ごう','がない','がなかった','がなきゃ','がなくちゃ','がなくて'],
                'v5s': ['さな','した','して','し','せ','させ','され','そう','さない','さなかった','さなきゃ','さなくちゃ','さなくて'],
                'v5t': ['たな','った','って','ち','て','たせ','たれ','とう','たない','たなかった','たなきゃ','たなくちゃ','たなくて'],
                'v5n': ['なな','んだ','んで','に','ね','なせ','なれ','のう','なない','ななかった','ななきゃ','ななくちゃ'],
                'v5b': ['ばな','んだ','んで','び','べ','ばせ','ばれ','ぼう','ばない','ばなかった','ばなきゃ','ばなくちゃ'],
                'v5m': ['まな','んだ','んで','み','め','ませ','まれ','もう','まない','まなかった','まなきゃ','まなくちゃ'],
                'v5r': ['らな','った','って','り','れ','らせ','られ','ろう','らない','らなかった','てください','て','らなきゃ','らなくちゃ'],
                }
    adjEndings = {'adj': ['さ','く','げ','な','か','くない','くなかった','くなく', 'くては', 'くて'],
                  'adj-i': ['さ','く','げ','な','か','くない','くなかった','くなく', 'くては', 'くて'],
                  'adj-s': ['さ','く','げ','な','か','くない','くなかった','くなく', 'くては', 'くて'],
                  }
    nounEndings = {'n':['だった','だって','の','も', 'は', 'が', 'に', 'を', 'と','で'],
                   'n-t': ['だった', 'だって', 'の', 'も', 'は', 'が', 'に', 'を', 'と', 'で'],
                   'n-adv': ['だった', 'だって', 'な', 'を', 'と','で'],
                   }
    suruends = ['します','しません','した','しない','しなかった','して','してる','している','しました','しませんでした','させる','させない','される','されない','しろ','するな']
    #if 'uk' in s and len(kana) > 0:
    #    dictforms = kana

    allforms = set()
    def add(w):
        allforms.add(w)
    add(word)
    if 'vs' in pos:
        for e in suruends:
            add(word + e)
    if 'vs-i' in pos:
        for e in suruends:
            add(word[0:-2] + e)
    if pos in verbEndings:
        for e in verbEndings[pos]:
            add(word[0:-1] + e)
    if pos in adjEndings:
        for e in adjEndings[pos]:
            add(word[0:-1] + e)
    if pos in nounEndings:
        for e in nounEndings[pos]:
            for s in ['', '御', 'お', 'ご']:
                add(s + word + e)

    return allforms

def getEntires() -> Set[EdictEntry]:
    path = "C:\\Users\matte\Downloads\edict2\edict2Orig.txt"
    reg = re.compile(r'(?P<kanji>.*?) (\[(?P<kana>.*)\] )?/\((?P<pos>.*?)\)(?P<eng>.*?)(?P<common>/\(P\))?/Ent.*?/')
    tagsregex: Pattern[str] = re.compile(r'\(([a-zA-Z]{1,5}?)\)')


    def splitter(s: str, id: int) -> EdictEntry:
        def getentry(entry: str) -> EdictEntry.Entry:
            return EdictEntry.Entry(tagsregex.sub('', entry), tagsregex.findall(entry))
        

        match = reg.search(s)
        p = match.group('common') is not None
        if match.group('kana'):
            kanji = [getentry(s) for s in match.group('kanji').split(';')]
            kana = [getentry(s) for s in match.group('kana').split(';')]
        else:
            kanji = []
            kana = [getentry(s) for s in match.group('kanji').split(';')]
        pos = match.group('pos').split(',')
        eng = [getentry(s) for s in  re.split('\(\d+\)', match.group('eng'))]
        return EdictEntry(kanji, kana, pos, eng, p, id)

    with open(path, "r", encoding='utf-8') as f:
        res = set()
        id = 0
        for l in f.readlines():
            id += 1
            entry = splitter(l, id)
            if len(entry.kana + entry.kanji) > 0 and len(entry.engdefs) > 0:
                res.add(entry)
        return res


def getmergedentries() -> Tuple[Dict[str, Set[EdictEntry]], Dict[str,str]]:
    entries = getEntires()
    p1: List[Tuple[str, EdictEntry]] = []
    p2: List[Tuple[str, EdictEntry]] = []
    p3: List[Tuple[str, EdictEntry]] = []

    def getpriorities(ee: EdictEntry):
        kanji = [k for k in ee.kanji if 'oK' not in k.tags]
        kana = [k for k in ee.kana if 'ok' not in k.tags]
        if len(kanji) == 0:
            p1 = []
            p2 = []
            if not any('P' in k.tags for k in kana):
                return [kana[0:1], kana[1:], set()]
            for k in kana:
                if 'P' in k.tags:
                    p1.append(k)
                else:
                    p2.append(k)
            return [p1, p2, set()]
        if not any('P' in k.tags for k in kanji):
            return [kanji[0:1], kanji[1:], [k for k in kana if len(k.text) >= 3]]
        p1 = []
        p2 = []
        for k in kanji:
            if 'P' in k.tags:
                p1.append(k)
            else:
                p2.append(k)
        return [p1 + [k for k in kana if 'P' in k.tags] ,p2, [k for k in kana if len(k.text) >= 3 and 'P' not in k.tags]]

    for e in entries:
        if all('arch' in ed.tags or 'obsc' in ed.tags for ed in e.engdefs):
            continue
        forms = getpriorities(e)
        for k in forms[0]:
            p1.append((k.text, e))
        for k in forms[1]:
            p2.append((k.text, e))
        for k in forms[2]:
            p3.append((k.text, e))

    conjtoword: Dict[str,str] = dict()
    wordtoentries: Dict[str, Set[EdictEntry]] = dict()

    addnewtodicts(conjtoword, p1, wordtoentries)
    addnewtodicts(conjtoword, p2, wordtoentries)
    addnewtodicts(conjtoword, p3, wordtoentries)
    return wordtoentries, conjtoword


def addnewtodicts(conjtoword, p1, wordtoentries):
    def getoverlaps(entries: List[Tuple[str, EdictEntry]]) -> Dict[str, Set[EdictEntry]]:
        res = dict()
        for i in entries:
            res.setdefault(i[0], []).append(i[1])
        return res

    for k, ees in getoverlaps(p1).items():
        if k in wordtoentries:
            continue
        wordtoentries[k] = ees
        for c in {conj for entry in ees for p in entry.pos for conj in getwordconjugations(k, p)}:
            if c not in conjtoword:
                conjtoword[c] = k

def getfcdict(basetoentries: Dict[str, Set[EdictEntry]]) -> Dict[str, str]:
    return {k: formatentries(k, v, 100) for k, v in basetoentries.items()}

def formatentries(word:str,  es: Set[EdictEntry], maxdefs: int) -> str:
    def singleentry(edict: EdictEntry):
        dictforms = [k.text for k in edict.kanji + edict.kana]
        dictforms.remove(word)
        q = '"'
        qq = '\''
        return f'{" ".join([word] + dictforms)} {" ".join(edict.pos)}: {" ".join(d.text.replace(q, qq) for d in edict.engdefs[0:maxdefs])}'

    return '\n'.join({singleentry(e) for e in es})