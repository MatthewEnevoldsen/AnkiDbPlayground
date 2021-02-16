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
        self.fields = db.fields
        self.notetypes = db.notetypes
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

        fromCardOrd = self.dbReader.getCardDefs(fromNote)[fromCard]
        toCardOrd = self.dbReader.getCardDefs(toNote)[toCard]

        toNotesDict = dict()
        for n in self.dbReader.getNotesOfType(toNote):
            flds = self.getFields(n.flds)
            toNotesDict[toKey(flds)] = n

        for n in self.dbReader.getNotesOfType(fromNote):
            flds = self.getFields(n.flds)
            key = fromKey(flds)
            if key in toNotesDict:
                deadCard = self.dbReader.cardFromNote(n, fromCardOrd)
                nextCard = self.dbReader.cardFromNote(toNotesDict[key], toCardOrd)
                self.mergeInCard(deadCard, nextCard)
                self.session.delete(deadCard)
        self.session.commit()

    def combineNotes(self, notename: str, keyyer):
        # eg
        # moveCards(session, Col, Notes, Cards, Revlog, "Core10K", "SentanceAudio", "AllSentences", "Audio",
        # lambda s: s[0], lambda s: stripTags(s[7]))
        toNotesDict = dict()
        for n in self.dbReader.getNotesOfType(notename):
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
            for o in range(len(self.dbReader.getCardDefs(notename))):
                cards1 = self.dbReader.cardFromNote(n1, o)
                cards2 = self.dbReader.cardFromNote(n2, 0)
                self.mergeInCard(cards1, cards2)
                self.session.delete(cards1)
                self.session.commit()

    def cardCount(self, notename):
        noteid = self.dbReader.getNoteId(notename)
        return len(self.session.query(self.cards).filter(self.cards.nid == noteid).all())

    def mergeCardsFromSameNote(self, note: str, deadcard: str, newcard: str):
        cn = self.dbReader.getCardDefs(note)
        dead = cn[deadcard]
        target = cn[newcard]
        allDead = list()
        for note in self.dbReader.getNotesOfType(note):
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

    def reindex(self, notename: str, field: str = 'Id', force: bool = False):
        notes = self.dbReader.getNotesOfType(notename)
        id = self.dbReader.getNoteFields(notename)[field]
        for i in range(len(notes)):
            n = notes[i]
            # if force or self.dbReader.getField(n.flds, id) == '':
            if 'sen' in self.dbReader.getField(n.flds, id):
                self.updateField(n, id, str(1000000000 + i))
        self.session.commit()

    def move10ktoedict(self):
        wordtocard = {self.dbReader.getFields(n.flds)[0]: self.dbReader.cardFromNote(n, 0) for n in self.dbReader.getNotesOfType('EdictVocab')}

        core10kvocabdeckid = 1495451679055
        edicttempdeckid = 1592774635155
        for n in self.dbReader.getNotesOfType('Core10K'):
            core10kcard = self.dbReader.cardFromNote(n, 0)
            word = self.dbReader.getFields(n.flds)[1].strip('~').strip('～').strip('<br>')

            if core10kcard.did == core10kvocabdeckid: #core10k deck id
                if word in wordtocard:
                    if wordtocard[word].did == core10kvocabdeckid:
                        core10kcard.did = edicttempdeckid
                        core10kcard.queue = -1
                    else:
                        core10kid = core10kcard.nid
                        core10kcard.nid = wordtocard[word].nid
                        wordtocard[word].nid = core10kid
                        #now we've switched so this is for the core10kcard
                        wordtocard[word].queue = -1  # suspend
        self.session.commit()

    def Tag10K(self, path: str, tags: List[str]):
        notes = self.dbReader.getNotesOfType('Core10K')
        text = open(path, "r", encoding="UTF-8").read()
        for note in notes:
            vocab = self.dbReader.get10KVocab(note.flds)
            if vocab in text:
                for tag in tags:
                    if not tag in note.tags:
                        note.tags = f"{note.tags} {tag} "
        self.session.commit()

    emptyfurireg = re.compile(r'\[\]')

    def remove_bad_furi(self):
        def fix(nn, fn):
            ind = self.dbReader.getNoteFields(nn)[fn]
            for n in self.dbReader.getNotesOfType(nn):
                vocab = self.dbReader.getField(n.flds, ind)
                new = AnkiDbHelper.emptyfurireg.sub('', vocab)
                if new != vocab:
                    self.updateField(n, ind, new)

        fix('Core10K', 'VocabFuri')
        self.session.commit()
        fix('AllSentences', 'Japanese')
        self.session.commit()

    def move_furi_and_clear(self):
        nn = 'AllSentences'
        noteFields = self.dbReader.getNoteFields(nn)
        japind = noteFields['Japanese']
        furiind = noteFields['MaybeReading']
        furiregex = re.compile('\[[ぁ-んァ-ン]+?\]')
        for n in self.dbReader.getNotesOfType(nn):
            senwithfuri =self.dbReader.getField(n.flds, furiind)
            sen = self.dbReader.getField(n.flds, japind)
            if furiregex.search(sen) is not None and senwithfuri == '':
                self.updateField(n, furiind, sen)
                self.updateField(n, japind, furiregex.sub('', sen))

        self.session.commit()

    def suspend_unseen(self):
        def getcards(n):
            return set(self.session.query(self.cards).filter(self.cards.nid == n.id).all())
        count = 0
        for n in self.dbReader.get_vocab_notes():
            cards = getcards(n)
            if sum(c.reps for c in cards) == 0:
                for c in cards:
                    if c.queue == 0:
                        c.queue = -1
                        count = count + 1
        self.session.commit()
        return count

    def Unsuspend10k(self, path: str, max: int = 9999999):
        notes = self.dbReader.getNotesOfType('Core10K')
        text = open(path, "r", encoding="UTF-8").read()[0: max]
        count = 0
        for note in notes:
            vocab = self.dbReader.get10KVocab(note.flds)
            if sum(1 for v in vocab.baseVocab() if v in text) > 0:
                for c in self.dbReader.cardsFromNote(note):
                    if c.queue == -1:
                        c.queue = 0
                        count = count + 1
        self.session.commit()
        return count

    def UnsuspendSeen(self):
        notes = self.dbReader.getNotesOfType('Core10K')
        count = 0
        for note in notes:
            cards = self.dbReader.cardsFromNote(note)
            if sum(c.reps for c in cards) > 0:
                for c in cards:
                    if c.queue == -1:
                        c.queue = 0
                        count = count + 1
        self.session.commit()
        return count

    def negativeCards(self):
        notes = self.dbReader.getNotesOfType('Kanji')
        count = 0
        for note in notes:
            for c in self.dbReader.cardsFromNote(note):
                if c.type == 3:
                    if c.left % 1000 > 10:
                        count = count + 1
                        c.left = c.left - c.left % 1000 + 10
                else:
                    if c.left % 1000 > 20:
                        count = count + 1
                        c.left = c.left - c.left % 1000 + 20
                #c.queue = 0
        self.session.commit()
        return count

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
