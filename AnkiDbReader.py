import datetime
import json
import re
from collections import namedtuple
from dataclasses import dataclass
from typing import List, Set

from AnkiStrings import AnkiStrings
from AnkiDb import AnkiDb


@dataclass
class AnkiVocab:
    eng: str
    jap: str
    furi: str

    def baseVocab(self) -> str:
        ends = "うくづつるぬむすぐぶい"
        if len(self.jap) == 0:
            return self.jap
        return self.jap[0:-1] if self.jap[-1] in ends else self.jap
    def dictForm(self) -> str:
        return f'{self.furi}: {self.eng}'

@dataclass
class AnkiSentence:
    eng: str
    jap: str
    id: str

    def potentialWords(self) -> Set[str]:
        max = min(len(self.jap) + 1, 10)
        res = set()
        for l in range(1, max):
            for s in range(0, len(self.jap) - l + 1):
                res.add(self.jap[s:s + l])
        return res

class AnkiDbReader:

    def __init__(self, db: AnkiDb):
        self.ankiStrings = AnkiStrings()
        self.notes = db.notes
        self.cards = db.cards
        self.col = db.col
        self.revlog = db.revlog
        self.session = db.session
        self.vocabNoteDef = self.getNoteFields('Core10K')
        self.sentenceNoteDef = self.getNoteFields('AllSentences')

    def getAllSentences(self):
        return [self.getSentence(n.flds) for n in self.getNotesOfType('AllSentences')]

    def allVocab(self) -> List[AnkiVocab]:
        return [self.get10KVocab(n.flds) for n in self.getNotesOfType('Core10K')]

    def getKnownVocabSet(self) -> List[AnkiVocab]:
        def getcards(n):
            return set(self.session.query(self.cards).filter(self.cards.nid == n.id).all())
        return [self.get10KVocab(n.flds) for n in self.getNotesOfType('Core10K')
                if sum((c.reps for c in getcards(n))) > 0]

    def cardFromNote(self, note, ord):
        return next(x for x in self.session.query(self.cards).filter(self.cards.nid == note.id).all() if x.ord == ord)

    def cardsFromNote(self, note):
        return self.session.query(self.cards).filter(self.cards.nid == note.id).all()

    def cardCount(self, notename):
        noteid = self.getNoteId(notename)
        return len(self.session.query(self.cards).filter(self.cards.nid == noteid).all())

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
        noteDefs = json2obj(re.sub('\"(\d+)\":', '\"Id\\1\":', models))
        return list(filter(lambda i: i.name.lower() == noteName.lower(), noteDefs))[0]

    def getNoteFields(self, name: str):
        return {f.name: f.ord for f in self.getNoteDef(name).flds}

    def get10KVocab(self, flds: str):
        return AnkiVocab(self.getField(flds, self.vocabNoteDef['VocabEng']),
                         self.getField(flds, self.vocabNoteDef['Vocab']),
                         self.getField(flds, self.vocabNoteDef['VocabFuri']))

    def getSentence(self, flds: str):
        return AnkiSentence(self.getField(flds, self.sentenceNoteDef['English']),
                            self.getField(flds, self.sentenceNoteDef['Japanese']),
                            self.getField(flds, self.sentenceNoteDef['Id']))

    def getField(self, fields: str, index: int):
        return self.getFields(fields)[index]

    def getFields(self, fields: str):
        return fields.split("\u001f")

    def toFields(self, fields: List[str]):
        return "\u001f".join(fields)
