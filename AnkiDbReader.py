import json
import re
from collections import namedtuple
from datetime import datetime
from typing import List, Set, Dict

from AnkiDb import AnkiDb
from AnkiStrings import AnkiStrings


def split(flds: str) -> List[str]:
    return flds.split("\u001f")


def to_flds(flds: List[str]) -> str:
    return "\u001f".join(flds)


def get_flds(note_def: Dict[str, int], flds: str) -> Dict[str, str]:
    values = split(flds)
    return {fieldname: values[index] for fieldname, index in note_def.items()}


class AnkiVocab:
    noteDef: Dict[str, int] = None
    hirareg = re.compile('[ぁ-ん]{0,2}')

    def __init__(self, flds: str):
        fields = get_flds(AnkiVocab.noteDef, flds)
        self.eng = fields['VocabEng']
        self.jap = fields['Vocab']
        self.furi = fields['VocabFuri']
        self.id = fields['Id']
        self.pos = fields['PartOfSpeech']

    def baseVocab(self) -> List[str]:
        if AnkiVocab.hirareg.fullmatch(self.jap) is not None:
            return ['this wont appear in examplesentend']
        if 'noun' in self.pos or 'adverb' in self.pos:
            return [self.jap]
        # if 'adj' in self.pos:
        if self.jap[-1] == 'い':
            return [self.jap[0:-1] + e for e in ['く', 'か', 'い']]
        ved = {'う': ['う', 'い', 'った', 'わ', 'え'],
               'く': ['く', 'き', 'いた', 'か', 'け'],
               'つ': ['つ', 'ち', 'った', 'た', 'て'],
               'づ': ['づ', 'ぢ', 'っだ', 'だ', 'で'],
               'る': [''],
               'ぬ': ['ぬ', 'に', 'んだ', 'な', 'ね'],
               'む': ['む', 'み', 'んだ', 'ま', 'め'],
               'す': ['す', 'し', 'した', 'さ', 'せ'],
               'ぐ': ['ぐ', 'ぎ', 'いだ', 'が', 'げ'],
               'ぶ': ['ぶ', 'び', 'んだ', 'ば', 'べ'],
               'する': [''],
               }
        return [self.jap[0:-1] + end for end in ved[self.jap[-1]]] if self.jap[-1] in ved else [self.jap]

    def dictForm(self) -> str:
        return f'{self.furi}: {self.eng}'

    def __hash__(self):
        return id.__hash__()


class AnkiSentence:
    furireg = re.compile(r'\[.*?\]')
    noteDef: Dict[str, int] = None

    def __init__(self, flds: str):
        fields = get_flds(AnkiSentence.noteDef, flds)
        self.eng = fields['English']
        self.jap = fields['Japanese']
        self.id =  int(fields['Id']) if fields['Id'].isnumeric() else 2000000000

    def potentialWords(self) -> Set[str]:
        defuri = AnkiSentence.furireg.sub('', self.jap)
        max = min(len(defuri) + 1, 7)
        res = set()
        for l in range(1, max):
            for s in range(0, len(defuri) - l + 1):
                res.add(defuri[s:s + l])
        return res

    def __hash__(self):
        return id.__hash__()


class AnkiDbReader:

    def __init__(self, db: AnkiDb):
        self.ankiStrings = AnkiStrings()
        self.notes = db.notes
        self.cards = db.cards
        self.col = db.col
        self.revlog = db.revlog
        self.session = db.session
        AnkiVocab.noteDef = self.getNoteFields('Core10K')
        AnkiSentence.noteDef = self.getNoteFields('AllSentences')

    def getAllSentences(self):
        return [self.getSentence(n.flds) for n in self.getNotesOfType('AllSentences')]

    def getNextWeekSentences(self):
        oneweekfromtodayinanki = (datetime.utcnow() - datetime(1970,1,1)).days - 17001 + 17 + 7
        def isCardDueInNetWeek(n) -> bool:
            for c in self.cardsFromNote(n):
                if c.queue in [0, 1, 3]:
                    return True
                if c.queue == 2 and c.due < oneweekfromtodayinanki:
                    return True
            return False
        return [self.getSentence(n.flds) for n in self.getNotesOfType('AllSentences') if isCardDueInNetWeek(n)]

    def allVocab(self) -> List[AnkiVocab]:
        return [AnkiVocab(n.flds) for n in self.getNotesOfType('Core10K')]

    def getKnownVocabSet(self) -> List[AnkiVocab]:
        def getcards(n):
            return set(self.session.query(self.cards).filter(self.cards.nid == n.id).all())

        return [AnkiVocab(n.flds) for n in self.getNotesOfType('Core10K')
                if sum((c.reps for c in getcards(n))) > 0]

    def cardFromNote(self, note, ord):
        return next(x for x in self.session.query(self.cards).filter(self.cards.nid == note.id).all() if x.ord == ord)

    def cardsFromNote(self, note):
        return self.session.query(self.cards).filter(self.cards.nid == note.id).all()

    def cardCount(self, notename):
        noteid = self.getNoteId(notename)
        return len(self.session.query(self.cards).filter(self.cards.nid == noteid).all())

    def get_vocab_notes(self):
        return self.getNotesOfType('Core10K')

    def getNotesOfType(self, noteName: str):
        nid = self.getNoteId(noteName)
        return list(self.session.query(self.notes).filter(self.notes.mid == nid).all())

    def getNoteId(self, noteName: str):
        return self.getNoteDef(noteName).id

    def getCardDefs(self, noteName: str):
        cards = self.getNoteDef(noteName).tmpls
        return {c.name: c.ord for c in cards}

    def getNoteDef(self, noteName: str):
        def _json_object_hook(d):
            return namedtuple('X', d.keys())(*d.values())

        def json2obj(data):
            return json.loads(data, object_hook=_json_object_hook)

        models = list(self.session.query(self.col))[0].models
        noteDefs = json2obj(re.sub(r'\"(\d+)\":', '\"Id\\1\":', models))
        return list(filter(lambda i: i.name.lower() == noteName.lower(), noteDefs))[0]

    def getNoteFields(self, name: str):
        return {f.name: f.ord for f in self.getNoteDef(name).flds}

    def get10KVocab(self, flds: str):
        return AnkiVocab(flds)

    def getSentence(self, flds: str):
        return AnkiSentence(flds)

    def getField(self, fields: str, index: int):
        return self.getFields(fields)[index]

    def getFields(self, fields: str):
        return fields.split("\u001f")

    def toFields(self, fields: List[str]):
        return "\u001f".join(fields)
