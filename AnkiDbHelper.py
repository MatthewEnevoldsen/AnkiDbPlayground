import datetime
import json
import re
from collections import namedtuple
from typing import List

from AnkiDb import AnkiDb
from AnkiStrings import AnkiStrings
from AnkiDbReader import AnkiDbReader


class AnkiDbHelper:

    def __init__(self, db: AnkiDb):

        self.ankiStrings = AnkiStrings()
        self.notes = db.notes
        self.cards = db.cards
        self.col = db.col
        self.revlog = db.revlog
        self.session = db.session
        self.dbReader = AnkiDbReader(db)


    def archiveRevlog(self):
        #     CREATEy TABLE revlog (
        #     id              integer primary key,
        #        -- epoch-milliseconds timestamp of when you did the review
        #     cid             integer not null,
        #        -- cards.id
        #     usn             integer not null,
        #         -- update sequence number: for finding diffs when syncing.
        #         --   See the description in the cards table for more info
        #     ease            integer not null,
        #        -- which button you pushed to score your recall.
        #        -- review:  1(wrong), 2(hard), 3(ok), 4(easy)
        #        -- learn/relearn:   1(wrong), 2(ok), 3(easy)
        #     ivl             integer not null,
        #        -- interval (i.e. as in the card table)
        #     lastIvl         integer not null,
        #        -- last interval (i.e. the last value of ivl. Note that this value is not necessarily equal to the actual interval between this review and the preceding review)
        #     factor          integer not null,
        #       -- factor
        #     time            integer not null,
        #        -- how many milliseconds your review took, up to 60000 (60s)
        #     type            integer not null
        #        --  0=learn, 1=review, 2=relearn, 3=cram
        # );
        dt = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        yearAgo = dt.timestamp() * 1000
        self.session.query(self.revlog).filter(self.revlog.id < yearAgo).delete()
        self.session.commit()

    def moveCards(self, fromNote: str, fromCard: str, toNote: str, toCard: str, toKey, fromKey):
        # eg
        # moveCards(session, Col, Notes, Cards, Revlog, "Core10K", "SentanceAudio", "AllSentences", "Audio",
        # lambda s: s[0], lambda s: stripTags(s[7]))

        fromCardOrd = self.getNoteCardDefs(fromNote)[fromCard]
        toCardOrd = self.getNoteCardDefs(toNote)[toCard]

        toNotesDict = dict()
        for n in self.getNotesOfType(toNote):
            flds = self.getFields(n.flds)
            toNotesDict[toKey(flds)] = n

        for n in self.getNotesOfType(fromNote):
            flds = self.getFields(n.flds)
            key = fromKey(flds)
            if key in toNotesDict:
                deadCard = self.cardFromNote(n, fromCardOrd)
                nextCard = self.cardFromNote(toNotesDict[key], toCardOrd)
                self.mergeInCard(deadCard, nextCard)
                self.session.delete(deadCard)
        self.session.commit()

    def combineNotes(self, notename: str, keyyer):
        # eg
        # moveCards(session, Col, Notes, Cards, Revlog, "Core10K", "SentanceAudio", "AllSentences", "Audio",
        # lambda s: s[0], lambda s: stripTags(s[7]))
        toNotesDict = dict()
        for n in self.getNotesOfType(notename):
            flds = self.getFields(n.flds)
            key = keyyer(flds)
            if key in toNotesDict:
                toNotesDict[key].append(n)
            else:
                toNotesDict[keyyer(flds)] = [n]
        for key in toNotesDict:
            if len(toNotesDict[key]) == 1:
                continue
            n1 = toNotesDict[key][0]
            n2 = toNotesDict[key][1]
            # flds1 = self.getFields(n1.flds)
            # flds2 = self.getFields(n2.flds)
            # def getNewfield(a,b):
            #     if a == key:
            #         return a
            #     else:
            #         return f'{a}{" " if a != "" and b != "" else ""}{b}'
            # newflds = [getNewfield(a,b) for a, b in zip(flds1, flds2)]
            # n1.flds = self.toFields(newflds)
            # n2.flds = self.toFields(newflds)
            # self.session.commit()
            for o in range(len(self.getNoteCardDefs(notename))):
                cards1 = self.cardFromNote(n1, o)
                cards2 = self.cardFromNote(n2, 0)
                self.mergeInCard(cards1, cards2)
                self.session.delete(cards1)
                self.session.commit()

    def cardFromNote(self, note, ord):
        return next(x for x in self.session.query(self.cards).filter(self.cards.nid == note.id).all() if x.ord == ord)

    def cardsFromNote(self, note):
        return self.session.query(self.cards).filter(self.cards.nid == note.id).all()

    def cardCount(self, notename):
        noteid = self.getNoteId(notename)
        return len(self.session.query(self.cards).filter(self.cards.nid == noteid).all())

    def mergeCardsFromSameNote(self, note: str, deadcard: str, newcard: str):
        cn = self.getNoteCardDefs(note)
        dead = cn[deadcard]
        target = cn[newcard]
        allDead = list()
        for note in self.getNotesOfType(note):
            ethCards = list(self.session.query(self.cards).filter(self.cards.nid == note.id).all())
            deadCard = list(filter(lambda c: c.ord == dead, ethCards))[0]
            targetCard = list(filter(lambda c: c.ord == target, ethCards))[0]
            self.mergeInCard(deadCard, targetCard)
            allDead.append(deadCard)
        for d in allDead:
            self.session.delete(d)
        self.session.commit()

    def mergeInCard(self, deadCard, targetCard):
        if targetCard.type == 3 or deadCard.type == 3:
            print("can't merge")
            return
        dueCard = deadCard
        if deadCard.type < targetCard.type:
            dueCard = targetCard
        # usn => target, Should be synced, confirm what this is when everything is synced
        # type => if neither 3, max, probably max anyway
        # queue => target, or -2 for saftey
        # due => max(type).due
        # ivl => min
        # factor => min
        # reps => sum
        # lapses => sum
        # left => max(type).left
        targetCard.type = dueCard.type
        targetCard.queue = -2
        targetCard.due = dueCard.due
        targetCard.ivl = min(targetCard.ivl, deadCard.ivl)
        targetCard.factor = dueCard.factor
        targetCard.reps = targetCard.reps + deadCard.reps
        targetCard.lapses = targetCard.lapses + deadCard.lapses
        targetCard.left = dueCard.left

        for review in self.session.query(self.revlog).filter(self.revlog.cid == deadCard.id):
            # print (f"review {review.id} changing {review.cid} to {targetCard.id}")
            review.cid = targetCard.id

    def getNotesOfType(self, noteName: str):
        nid = self.getNoteId(noteName)
        return list(self.session.query(self.notes).filter(self.notes.mid == nid).all())

    def getNoteId(self, noteName: str):
        return self.getNoteDef(noteName).id

    def getNoteCardDefs(self, noteName: str):
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

    def reindex(self, notename: str, field: str = 'Id', force: bool = False):
        notes = self.dbReader.getNotesOfType(notename)
        id = self.dbReader.getNoteFields(notename)[field]
        for i in range(len(notes)):
            n = notes[i]
            #if force or self.dbReader.getField(n.flds, id) == '':
            if 'sen' in self.dbReader.getField(n.flds, id):
                self.updateField(n, id, str(1000000000 + i))
        self.session.commit()



    def Tag10K(self, path: str, tags: List[str]):
        notes = self.getNotesOfType('Core10K')
        text = open(path, "r", encoding="UTF-8").read()
        for note in notes:
            vocab = self.get10KVocab(note.flds)
            if vocab in text:
                for tag in tags:
                    if not tag in note.tags:
                        note.tags = f"{note.tags} {tag} "
        self.session.commit()

    def Unsuspend10k(self, path: str):
        notes = self.getNotesOfType('Core10K')
        text = open(path, "r", encoding="UTF-8").read()
        for note in notes:
            vocab = self.get10KVocab(note.flds)
            if vocab in text:
                for c in self.cardsFromNote(note):
                    if c.queue == -1:
                        c.queue = 0
        self.session.commit()

    def addTag(note, tag):
        if not tag in note.tags.split(' '):
            note.tags = f"{note.tags} {tag}"

    def delTag(note, tag):
        allTags = note.tags.split(' ')
        if tag in allTags:
            allTags.remove(tag)
            note.tags = ' '.join(allTags)

    def Tag10KWhere(self, condition, tag: str):
        notes = self.getNotesOfType('Core10K')
        for note in notes:
            vocab = self.get10KVocab(note.flds)
            if condition(vocab):
                if not tag in note.tags:
                    note.tags = f"{note.tags} {tag} "
        self.session.commit()

    def get10KVocab(self, flds: str):
        return self.ankiStrings.toBaseVocab(self.getField(flds, 1))

    def SingleTag10K(self, paths: List[str], tag: str):
        texts = []
        for p in paths:
            texts.append(open(p, "r", encoding="utf-8").read())

        def getIndex(vocab):
            for text in texts:
                if vocab in text:
                    return texts.index(text)
            return None

        notes = self.getNotesOfType('Core10K')
        for note in notes:
            vocab = self.ankiStrings.toBaseVocab(note.flds[0])
            index = getIndex(vocab)
            if index is not None:
                note.tags = f"{note.tags} {tag}_{index} "
        self.session.commit()

    def updateField(self, note, fldId: int, value: str):
        flds = self.getFields(note.flds)
        flds[fldId] = value
        note.flds = self.toFields(flds)

    def getField(self, fields: str, index: int):
        return self.getFields(fields)[index]

    def getFields(self, fields: str):
        return fields.split("\u001f")

    def toFields(self, fields: List[str]):
        return "\u001f".join(fields)
