import datetime
import glob
import json
import operator
import os
import re
import string
from collections import namedtuple
from typing import List, Tuple, Set

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

core10kId = 1342706442509
realDbPath = f"C:/Users/matte/AppData/Roaming/Anki2/Tirinst/collection.anki2"
dbPath = realDbPath


def fuckWithStuff():
    Base = automap_base()
    engine = create_engine(f"sqlite:///{dbPath}")
    Base.prepare(engine, reflect=True)
    Notes = Base.classes.notes
    Cards = Base.classes.cards
    Col = Base.classes.col
    Revlog = Base.classes.revlog
    session = Session(engine)
    setSource(session, Col,Notes, "taekim", 3)
    # tagjpod(session, Notes)
    # r = getSenKnownRatios(session, Notes, Cards, Col)
    # tagSenRatios(session,Notes,Cards, Col, r)
    # knownWords = getKnownVocabSet(session, Notes,Cards)
    # Tag10KWhere(session, Notes, lambda vocab: toBaseVocab(vocab) in knownWords, "Known")
    # tagSenRatios(session, Col,Notes, Cards)
    session.close()


def setSource(session, Col, Notes, deck, sourceId):
    notes = getNotesOfType("AllSentences", session, Col, Notes)
    for n in notes:
        flds = getFields(n.flds)
        if flds[sourceId] == '':
            flds[sourceId] = deck
            n.flds = toFields(flds)
    session.commit()


def getSenRatios(session, Col, Notes, Cards):
    def getter():
        tokens = tokenise(session, Col, Notes)
        known = getKnownVocabSet(session, Notes, Cards)
        res = dict()
        for t in tokens.items():
            allCount = len(t[1])
            knownVocab = set((v for v in t[1] if v in known))
            knownCount = sum((1 for v in knownVocab))
            res[t[0]] = 0 if allCount == 0 else knownCount / allCount
        return res

    return setDiskCache('senRatios.json', getter, lambda o: o)


def tagSenRatios(session, Col, Notes, Cards):
    jap = 0
    ratios = getSenRatios(session, Col, Notes, Cards)
    known = 'Known'
    unknown = 'Unknown'
    for n in getNotesOfType("AllSentences", session, Col, Notes):
        sentence = stripNoise(getField(n.flds, jap))
        if sentence in ratios:
            ratio = int(ratios[sentence])
            if ratio > 0.99:
                delTag(n, unknown)
                addTag(n, known)
            else:
                delTag(n, known)
                addTag(n, unknown)
    session.commit()


def tokenise(session, Col, Notes):
    def getter():
        allVocab = getAllVocabSet(session, Notes)
        results = dict()
        for sentence in getAllSentences(session, Col, Notes):
            parts = splitDownWord(sentence)
            sentenceVocab = set((v for v in parts if v in allVocab))
            results[sentence] = list(sentenceVocab)
        return results

    def fix(o):
        results = dict()
        for t in o.items():
            results[t[0]] = t[1]
        return results

    return setDiskCache('tokenised.json', getter, fix)


def getAllSentences(session, Col, Notes):
    def getter():
        jap = 0
        sen = set()
        for n in getNotesOfType("AllSentences", session, Col, Notes):
            sen.add(stripNoise(getField(n.flds, jap)))
        return list(sen)

    def fix(o):
        return set(o)

    return setDiskCache('allSen.json', getter, fix)


def getAllVocabSet(session, Notes) -> Set[str]:
    def getter():
        vocabFld = 1
        allVocab = set()
        for n in get10kNotes(session, Notes):
            flds = getFields(n.flds)
            vocab = toBaseVocab(flds[vocabFld])
            allVocab.add(vocab)
        return list(allVocab)

    def fix(o):
        return set(o)

    return setDiskCache('allVocab.json', getter, fix)


def getKnownVocabSet(session, Notes, Cards) -> Set[str]:
    def getter():
        vocabFld = 1
        known = set()
        for n in get10kNotes(session, Notes):
            flds = getFields(n.flds)
            vocab = toBaseVocab(flds[vocabFld])
            cards = set(session.query(Cards).filter(Cards.nid == n.id).all())
            if sum((c.reps for c in cards)) > 0:
                known.add(vocab)
        return list(known)

    def fix(o):
        return set(o)

    return setDiskCache('knownVocab.json', getter, fix)


def setDiskCache(filePath, setGetter, toPython):
    if not os.path.isfile(filePath):
        with open(filePath, "w", encoding="UTF-8") as fp:
            json.dump(setGetter(), fp, ensure_ascii=False)
    with open(filePath, "r", encoding="UTF-8") as read_file:
        return toPython(json.load(read_file))


def splitDownWord(sentence: str):
    max = min(len(sentence) + 1, 10)
    res = list()
    for l in range(1, max):
        for s in range(0, len(sentence) - l + 1):
            res.append(sentence[s:s + l])
    return res


def toBaseVocab(raw: str) -> str:
    ends = "うくづつるぬむすぐぶい"
    if len(raw) == 0:
        return raw
    return raw[0:-1] if raw[-1] in ends else raw


def archiveRevlog(session, Revlog):
    #     CREATE TABLE revlog (
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
    session.query(Revlog).filter(Revlog.id < yearAgo).delete()
    session.commit()


def getCore10KAudioSen(session, Col, Notes):
    senEng = 5
    senJap = 7
    senAudio = 9
    res = set()
    for n in getNotesOfType("Core10K", session, Col, Notes):
        flds = getFields(n.flds)
        if not flds[senEng] == '':
            res.add(f'{stripTags(flds[senEng])}\t{stripTags(flds[senJap])}\t{flds[senAudio]}\t10KAudio')
    # 9567
    writeFile("core10Ksen.tsv", res)


def combineCore10KKanjiAndKana(session, Col, Notes):
    # those don't match nay more
    vocab = 1
    vocabKanji = 11
    kana = 2
    furi = 7
    eng1 = 3
    eng2 = 4
    for n in getNotesOfType("Core10K", session, Col, Notes):
        flds = getFields(n.flds)
        if flds[vocab] == '':
            flds[vocab] = flds[vocabKanji]
        if flds[furi].startswith('[') and flds[furi].endswith(']'):
            flds[furi] = ''
        if flds[furi] == '':
            flds[furi] = f'{flds[vocab]}[{flds[kana]}]'
        if flds[eng2] == '0':
            flds[eng2] = ''
        if flds[eng1].endswith(',0'):
            flds[eng1] = flds[eng1][0: -2]
        if flds[eng2] != '' and not flds[eng2] in flds[eng1]:
            flds[eng1] = flds[eng1] + ',' + flds[eng2]
        newFlds = toFields(flds)
        n.flds = newFlds
    session.commit()


def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())


def json2obj(data): return json.loads(data, object_hook=_json_object_hook)


def moveCards(session, Col, Notes, Cards, RevLog, fromNote: str, fromCard: str, toNote: str, toCard: str, toKey,
              fromKey):
    # eg
    # moveCards(session, Col, Notes, Cards, Revlog, "Core10K", "SentanceAudio", "AllSentences", "Audio",
    # lambda s: s[0], lambda s: stripTags(s[7]))

    fromCardOrd = getNoteCardDefs(fromNote, session, Col)[fromCard]
    toCardOrd = getNoteCardDefs(toNote, session, Col)[toCard]

    toNotesDict = dict()
    for n in getNotesOfType(toNote, session, Col, Notes):
        flds = getFields(n.flds)
        toNotesDict[toKey(flds)] = n

    for n in getNotesOfType(fromNote, session, Col, Notes):
        flds = getFields(n.flds)
        key = fromKey(flds)
        if key in toNotesDict:
            deadCard = cardFromNote(session, Cards, n, fromCardOrd)
            nextCard = cardFromNote(session, Cards, toNotesDict[key], toCardOrd)
            mergeInCard(deadCard, nextCard, session, RevLog)
            session.delete(deadCard)

    session.commit()


def cardFromNote(session, Cards, note, ord):
    return next(x for x in session.query(Cards).filter(Cards.nid == note.id).all() if x.ord == ord)


def mergeTkCore10kVocab(session, Col, Notes, Cards, RevLog):
    audio = "Audio"
    kanji = "Kanji"
    english = "English"

    uniqueTk = getUniqueVocab(getNotesOfType("TkVocab", session, Col, Notes), 0)
    uniqueCore = getUniqueVocab(getNotesOfType("Core10K", session, Col, Notes), 1)
    coreCardDef = getNoteCardDefs("Core10K", session, Col)
    tkCardDef = getNoteCardDefs("TkVocab", session, Col)
    allDead = list()
    for tkKey, tkNote in uniqueTk.items():
        if tkKey in uniqueCore:
            print(tkKey)
            deadNote = tkNote
            targetNote = uniqueCore[tkKey]
            deadCards = list(session.query(Cards).filter(Cards.nid == deadNote.id).all())
            targetCards = list(session.query(Cards).filter(Cards.nid == targetNote.id).all())
            if len(deadCards) == 3:
                for cardName in [audio, kanji, english]:
                    deadCard = next(x for x in deadCards if x.ord == tkCardDef[cardName])
                    targetCard = next(x for x in targetCards if x.ord == coreCardDef[cardName])
                    mergeInCard(deadCard, targetCard, session, RevLog)
                    allDead.append(deadCard)
            if len(deadCards) == 2:
                for cardName in [kanji, english]:
                    deadCard = next(x for x in deadCards if x.ord == tkCardDef[cardName])
                    targetCard = next(x for x in targetCards if x.ord == coreCardDef[cardName])
                    mergeInCard(deadCard, targetCard, session, RevLog)
                    allDead.append(deadCard)
    for d in allDead:
        session.delete(d)
    session.commit()


def mergeWkCore10kVocab(session, Col, Notes, Cards, RevLog):
    audio = "Audio"
    kanji = "Kanji"
    english = "English"

    uniqueTk = getUniqueVocab(getNotesOfType("WkVocab", session, Col, Notes), 0)
    uniqueCore = getUniqueVocab(getNotesOfType("Core10K", session, Col, Notes), 1)
    coreCardDef = getNoteCardDefs("Core10K", session, Col)
    tkCardDef = getNoteCardDefs("TkVocab", session, Col)
    allDead = list()
    i = 1
    total = len(uniqueTk)
    cardsByNid = dict()
    for c in session.query(Cards).all():
        if c.nid in cardsByNid:
            cardsByNid[c.nid].append(c)
        else:
            cardsByNid[c.nid] = [c]
    for tkKey, tkNote in uniqueTk.items():
        if tkKey in uniqueCore:
            print(f'{tkKey}:{i}/{total}')
            i = i + 1
            deadNote = tkNote
            targetNote = uniqueCore[tkKey]
            deadCards = cardsByNid[deadNote.id]
            targetCards = cardsByNid[targetNote.id]
            for cardName in [audio, kanji, english]:
                deadCard = next((x for x in deadCards if x.ord == tkCardDef[cardName]), None)
                targetCard = next((x for x in targetCards if x.ord == coreCardDef[cardName]), None)
                if deadCard != None and targetCard != None:
                    mergeInCard(deadCard, targetCard, session, RevLog)
                    allDead.append(deadCard)
    for d in allDead:
        session.delete(d)
    session.commit()


def getUniqueVocab(vocabNotes, vocabIndex):
    groupedNotes = dict()
    for note in vocabNotes:
        flds = getFields(note.flds)
        vocab = flds[vocabIndex]
        if vocab in groupedNotes:
            groupedNotes[vocab].append(note)
        else:
            groupedNotes[vocab] = [note]
    uniqueNotes = dict()
    for key, value in groupedNotes.items():
        if len(value) == 1:
            uniqueNotes[key] = value[0]
    return uniqueNotes


def mergeEthSen(session, Col, Notes, Cards, RevLog):
    # Merged two cards from the same note
    cn = getNoteCardDefs("ethSen", session, Col)
    dead = cn['Listening']
    target = cn['Reading']
    allDead = list()
    for note in getNotesOfType("ethsen", session, Col, Notes):
        ethCards = list(session.query(Cards).filter(Cards.nid == note.id).all())
        deadCard = list(filter(lambda c: c.ord == dead, ethCards))[0]
        targetCard = list(filter(lambda c: c.ord == target, ethCards))[0]
        mergeInCard(deadCard, targetCard, session, RevLog)
        allDead.append(deadCard)
    for d in allDead:
        session.delete(d)
    session.commit()


def mergeInCard(deadCard, targetCard, session, Revlog):
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

    for review in session.query(Revlog).filter(Revlog.cid == deadCard.id):
        # print (f"review {review.id} changing {review.cid} to {targetCard.id}")
        review.cid = targetCard.id


def getNotesOfType(noteName, session, Col, Notes):
    nid = getNoteId(noteName, session, Col)
    return list(session.query(Notes).filter(Notes.mid == nid).all())


def getNoteId(noteName, session, Col):
    return getNoteDef(noteName, session, Col).id


def getNoteCardDefs(noteName, session, Col):
    cards = getNoteDef(noteName, session, Col).tmpls
    nameToOrd = dict()
    for c in cards:
        nameToOrd[c.name] = c.ord
    return nameToOrd


def getNoteDef(noteName, session, Col):
    models = list(session.query(Col))[0].models
    noteDefs = json2obj(re.sub('\"(\d+)\":', '\"Id\\1\":', models))
    return list(filter(lambda i: i.name.lower() == noteName.lower(), noteDefs))[0]


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)


def writeFile(path: str, content: List[str]):
    o = open(path, "w", 100, "UTF-8")
    for s in content:
        o.write(f"{s}\n")
    o.close()


def stripNoise(s: str) -> str:
    furi = re.compile('(?:\[[ぁ-んァ-ン]{1,8}?\])|(<\/?b>)| |\t')
    return furi.sub("", s).strip()


def stripTags(s: str) -> str:
    furi = re.compile('(<\/?b>)|\t')
    return furi.sub("", s).strip()


def splitJapEng(s: str) -> Tuple[str, str]:
    split = findSplit(s)
    return (stripNoise(s[0:split]), s[split + 1:].strip())


def findSplit(s: str):
    scores = dict()
    for split in find_all(s, " "):
        left = s[split - 1::-1]
        right = s[split:]
        leftEngRatio = countEng(left) / (len(left) + 1)
        rightEngRatio = countEng(right) / (len(right) + 1)
        scores[split] = rightEngRatio - leftEngRatio
    return max(scores.items(), key=operator.itemgetter(1))[0]


def countEng(s: str):
    letters = set(string.ascii_letters)
    return len(list(filter(lambda c: c in letters, s)))


def combineWkVocab(session, notes, cards, revlog):
    wkDeckId = 1468747180218
    wkNotes = session.query(notes).filter(notes.mid == wkDeckId).all()
    count = 0
    for wkNote in wkNotes:
        wkCards = session.query(cards).filter(cards.nid == wkNote.id).all()
        if len(wkCards) == 4:
            deadCard = wkCards[3]
            replaceCard = wkCards[1]
            for review in session.query(revlog).filter(revlog.cid == deadCard.id):
                # print (f"review {review.id} changing {review.cid} to {replaceCard.id}")
                count += 1
                review.cid = replaceCard.id
    print(count)
    session.commit()


def opmSeason1():
    res = []
    originals = os.listdir("C:\\subs\\One-Punch.Man")
    for file in originals:
        match = re.match("One-Punch.Man.S01E\d\d.WEBRip.Netflix.ja\[cc\].vtt", file)
        if match:
            res.append("C:\\subs\\One-Punch.Man" + "\\" + file)
    return res


def tagjpod(session, notes):
    for level in [1, 2, 3]:
        jpod = f'C:\Pod\Level{level}\lesson'
        combined = []
        for file in glob.glob(jpod + '/**/*.htm', recursive=True):
            combined.append(open(file, "r", encoding="UTF-8").read())
        combinedPath = f'c:\pod\level{level}\combined.txt'
        if os.path.exists(combinedPath):
            os.remove(combinedPath)
        writeFile(combinedPath, combined)
        Tag10K(session, notes, combinedPath, [f'JPod{level}'])


def getSeenNotes(session, notes, cards, deckId):
    seenCards = set()
    for c in session.query(cards):
        if c.reps > 0:
            seenCards.add(c.nid)
    seen = []
    for n in getNotes(session, notes, deckId):
        if n.id in seenCards:
            seen.append(n)
    return seen


def getAudio():
    # var files = GetSeenCards(1342706442509).Select(GetField(10)).
    # Concat(GetSeenCards(1468747180218).Select(GetField(4))).Concat(GetSeenCards(1491307188322).
    # Select(GetField(5))).ToList();

    # var res = files.Select(s => s.TrimStart("[sound:".ToCharArray()).TrimEnd("]".ToCharArray())).ToList();
    # res.ForEach(
    #     fileName =>
    #     {
    #         var path = $@"E:\Anki2\Tirinst\collection.media\{fileName}";
    #         var dest = $@"E:\AnkiVocab\{fileName}";
    #         if (!File.Exists(dest))
    #             try
    #             {
    #                 File.Copy(path, dest);
    #             }
    #             catch (Exception e)
    #             {
    #             }
    #     });
    return None


def Tag10K(session, notes, path: str, tags: List[str]):
    notes = get10kNotes(session, notes)
    text = open(path, "r", encoding="UTF-8").read()
    for note in notes:
        vocab = get10KVocab(note.flds)
        if vocab in text:
            for tag in tags:
                if not tag in note.tags:
                    note.tags = f"{note.tags} {tag} "
    session.commit()


def addTag(note, tag):
    if not tag in note.tags.split(' '):
        note.tags = f"{note.tags} {tag}"


def delTag(note, tag):
    allTags = note.tags.split(' ')
    if tag in allTags:
        allTags.remove(tag)
        note.tags = ' '.join(allTags)


def Tag10KWhere(session, notes, condition, tag: str):
    notes = get10kNotes(session, notes)
    for note in notes:
        vocab = get10KVocab(note.flds)
        if condition(vocab):
            if not tag in note.tags:
                note.tags = f"{note.tags} {tag} "
    session.commit()


def SingleTag10K(session, notes, paths: List[str], tag: str):
    texts = []
    for p in paths:
        texts.append(open(p, "r", encoding="utf-8").read())

    def getIndex(vocab):
        for text in texts:
            if vocab in text:
                return texts.index(text)
        return None

    notes = get10kNotes(session, notes)
    for note in notes:
        vocab = get10KVocab(note.flds)
        index = getIndex(vocab)
        if not index == None:
            note.tags = f"{note.tags} {tag}_{index} "
    session.commit()


def get10kNotes(session, notes):
    return session.query(notes).filter(notes.mid == core10kId)


def getNotes(session, notes, deckId):
    return session.query(notes).filter(notes.mid == deckId)


def updateField(note, fldId: int, value: str):
    flds = getFields(note.flds)
    flds[fldId] = value
    note.fields = toFields(flds)


def getField(fields: str, index: int):
    return getFields(fields)[index]


def getFields(fields: str):
    return fields.split("\u001f")


def toFields(fields: List[str]):
    return "\u001f".join(fields)


def get10KVocab(fields: str):
    return toBaseVocab(getField(fields, 1))


fuckWithStuff()
