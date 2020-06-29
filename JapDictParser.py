import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Set

from Utils.windows import *
import pandas as pd

@dataclass
class EdictEntry:
    kanji: List[str]
    kana: List[str]
    pos: List[str]
    engdefs: List[str]
    p: bool
    usuallykana: bool
    usuallykanji: bool

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
                'v5u': ['わ','った','って','い','え','わせ','われ','おう','わない','わなかった','わなきゃ','わなくちゃ','わなくて','わければ','じゃた'],
                'v5k': ['か','いた','いて','き','け','かせ','かれ','こう','かない','かなかった','かなきゃ','かなくちゃ','かなくて'],
                'v5g': ['が','いだ','いで','ぎ','げ','がせ','がれ','ごう','がない','がなかった','がなきゃ','がなくちゃ','がなくて'],
                'v5s': ['さ','した','して','し','せ','させ','され','そう','さない','さなかった','さなきゃ','さなくちゃ','さなくて'],
                'v5t': ['た','った','って','ち','て','たせ','たれ','とう','たない','たなかった','たなきゃ','たなくちゃ','たなくて'],
                'v5n': ['な','んだ','んで','に','ね','なせ','なれ','のう','なない','ななかった','ななきゃ','ななくちゃ'],
                'v5b': ['ば','んだ','んで','び','べ','ばせ','ばれ','ぼう','ばない','ばなかった','ばなきゃ','ばなくちゃ'],
                'v5m': ['ま','んだ','んで','み','め','ませ','まれ','もう','まない','まなかった','まなきゃ','まなくちゃ'],
                'v5r': ['ら','った','って','り','れ','らせ','られ','ろう','らない','らなかった','てください','て','らなきゃ','らなくちゃ'],
                }
    adjEndings = {'adj': ['さ','く','げ','な','か','くない','くなかった','くなく'],
                  'adj-i': ['さ','く','げ','な','か','くない','くなかった','くなく',],
                  'adj-s': ['さ','く','げ','な','か','くない','くなかった','くなく',],
                  }
    nounEndings = {'n':['だった','だって','の', 'は', 'が', 'に', 'を', 'と'],
                   'n-adv': ['だった', 'だって', 'な', 'を', 'と'],
                   }
    suruends = ['します','しません','した','して','してる','しました','しませんでした','させる','させない','される','されない','しろ','するな']
    #if 'uk' in s and len(kana) > 0:
    #    dictforms = kana

    allforms = set()
    def add(w):
        allforms.add(w)
    allforms.add(word)
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

def getEntires() -> List[EdictEntry]:
    path = "C:\\Users\matte\Downloads\edict2\edict2Orig.txt"
    reg = re.compile(r'(?P<kanji>.*?) (\[(?P<kana>.*)\] )?/\((?P<pos>.*?)\)(?P<eng>.*?)/Ent.*?/')
    clearTagREg = re.compile(r'\(.*?\)')
    preg = re.compile(r'\(P\)')
    usuallykanareg = re.compile(r'\(uk\)')
    usuallykanjireg = re.compile(r'\(uK\)')

    def splitter(s: str) -> EdictEntry:
        match = reg.search(s)
        p = preg.search(s) is not None
        usuallykana = usuallykanareg.search(s) is not None
        usuallykanji = usuallykanjireg.search(s) is not None
        kanji = clearTagREg.sub('', match.group('kanji')).split(';')
        if match.group('kana'):
            kana = clearTagREg.sub('', match.group('kana')).split(';')
        else:
            kana = []
        pos = match.group('pos').split(',')
        eng = re.split('\(\d+\)', match.group('eng'))

        return EdictEntry(kanji, kana, pos, eng, p, usuallykana, usuallykanji)

    with open(path, "r", encoding='utf-8') as f:
        return list(splitter(l) for l in f.readlines())

def getmergedentries() ->Dict[str, List[EdictEntry]] :
    entries = getEntires()
    wordstoentries: Dict[str, List[EdictEntry]] = dict()
    for e in entries:
        for k in e.kanji:
            if k in wordstoentries:
                wordstoentries[k].append(e)
            else:
                wordstoentries[k] = [e]
    for e in entries:
        if e.usuallykana:
            for k in e.kana:
                if k in wordstoentries:
                    wordstoentries[k].append(e)
                else:
                    wordstoentries[k] = [e]
    return wordstoentries

def getfcdict() -> Dict[str, str]:
    wordstoentries = getmergedentries()
    def multientry(word: str, es: List[EdictEntry]):
        def singleentry(word: str, edict: EdictEntry):
            alt = set(edict.kanji) - {word}
            q = '"'
            qq = '""'
            return f'{word} {" ".join(alt)} {" ".join(edict.kana)} {" ".join(edict.pos)}: {" ".join(d.replace(q,qq) for d in  edict.engdefs)}'
        return '\n'.join(singleentry(word, e) for e in es)
    return {k: multientry(k, v) for k, v in wordstoentries.items()}

def getsentencedict() -> Dict[str, str]:
    entries = getEntires()
    result: Dict[str, List[EdictEntry]] = dict()
    def addorappend(w, e):
        if w in result:
            result[w].append(e)
        else:
            result[w] = [e]
    def addifempty(w, e):
        if w not in result:
            result[w] = [e]
    # main word
    for e in entries:
        for p in e.pos:
            for c in getwordconjugations(e.kanji[0], p):
                addorappend(c, e)
    # other forms
    for e in entries:
        for w in e.kanji[1:] + e.kana:
            for p in e.pos:
                for c in getwordconjugations(w, p):
                    addifempty(c, e)

    def multientry(word: str, es: List[EdictEntry]):
        def singleentry(word: str, edict: EdictEntry):
            dictforms = list(edict.kanji + edict.kana)
            main = edict.kanji[0]
            for writing in dictforms:
                if writing in word:
                    main = writing
            dictforms.remove(main)
            q = '"'
            qq = '""'
            return f'{" ".join([main] + dictforms)} {" ".join(edict.pos)}: {" ".join(d.replace(q,qq) for d in  edict.engdefs[0:4])}'
        return '\n'.join({singleentry(word, e) for e in es})
    return {k: multientry(k, v) for k,v in result.items()}