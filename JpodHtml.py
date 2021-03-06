import re
from typing import Sequence, Tuple, List

import pandas as pd

import JpodHtmlParser as jp
from Utils.windows import downloadFile


class dialog:
    class sentences:
        def __init__(self, df, transid: int, col: str):
            self.df = df
            self.col = col
            self.transid = transid

        def getval(self, dialogid: int):
            return self.df.loc[(self.df.transid == self.transid) & (self.df.dialogid == dialogid), self.col].values[0]

        def setValue(self, did, value: str = ''):
            self.df.loc[(self.df.transid == self.transid) & (self.df.dialogid == did), self.col] = value

        def dialogCount(self):
            return self.df.loc[(self.df.transid == self.transid)].dialogid.max()

        def shift(self, fromto: Sequence[Tuple[int, int]]):
            values = {m[0]: self.getval(m[0]) for m in fromto}
            for m in fromto:
                self.setValue(m[1], values[m[0]])

        def remove(self, dids: Sequence[int]):
            # 1,2,3 remove 2 => 1 = 1, 2 = 3, 3 = ''
            for did in sorted(dids, reverse=True):
                self.shift([(i + 1, i) for i in range(did, self.dialogCount())])
                self.setValue(self.dialogCount(), '')

        def add(self, did: int, val: str = ''):
            # 1,2,3 add 2 => 1 = 1, 2 = '', 3 = 2, 4 = 3
            self.shift([(i, i + 1) for i in range(did, self.dialogCount())])
            self.setValue(did, val)

        def split(self, did: int, len: int):
            val = self.getval(did)
            self.add(did + 1, val[len:])
            self.setValue(did, val[:len])

        def splits(self, did: int, lens: List[int]):
            for i in range(0, len(lens)):
                self.split(did + i, lens[i])

        def adjmerge(self, did: int):
            self.setValue(did, f'{self.getval(did)} {self.getval(did + 1)}')
            self.remove([did + 1])

        def mergesomeup(self, did: int, length: int):
            p1 = self.getval(did)
            p2 = self.getval(did + 1)
            self.setValue(did, (p1 + p2)[0:len(p1) + length])
            self.setValue(did + 1, (p1 + p2)[len(p1) + length:])

        def adjmerges(self, dids: List[int]):
            for did in dids:
                self.adjmerge(did)

    def __init__(self, df, transid: int):
        self.jap = self.sentences(df, transid, 'japanese')
        self.eng = self.sentences(df, transid, 'english')
        self.audio = self.sentences(df, transid, 'ankiaudio')

    def remove(self, dids: Sequence[int]):
        self.eng.remove(dids)
        self.jap.remove(dids)

    def add(self, did: int):
        self.eng.add(did)
        self.jap.add(did)

    def clear(self, dids: Sequence[int]):
        # don't really want to delete, just want it to be clear in anki
        for did in dids:
            self.jap.setValue(did, 'a')
            self.eng.setValue(did, 'a')
            self.audio.setValue(did, 'a')


class JpodToAnki:
    def parseJodLevelDump(self, fileNameNoExt, level):
        data = pd.read_csv(f"c:/japanese/{fileNameNoExt}.csv")
        seasonreg = re.compile('.*/(.*?)/')
        whitespacereg = re.compile(r'\W+')

        def getseason(row):
            season = seasonreg.findall(row['pathways-href'])[0]
            return whitespacereg.sub('', season)

        lessonreg = re.compile('(.*?)\s*\n')
        def getlesson(row):
            lesson = lessonreg.findall(row['lesson'])[0]
            return whitespacereg.sub('', lesson)

        dialogmp3reg = re.compile('https\:\/\/mdn\.illops\.net\/japanesepod101\/(.*?101.*?)\.mp3')


        data['japanese'] = data['kanjisen'].apply(jp.getsen)
        data['mp3Url'] = data.apply(lambda row: jp.getmp3(row['kanjisen']) or jp.getmp3(row['engsen']), axis=1)
        data['english'] = data.apply(lambda row: jp.getsen(row['engsen']), axis=1)
        data['lesson2'] = data.apply(getlesson, axis=1)
        data['season'] = data.apply(getseason, axis=1)
        #data['fulldialog'] = data['dialogue'].apply(lambda l: next((e for e in dialogmp3reg.finditer(l)), ''))
        data.drop(data[data.mp3Url.isnull()].index, inplace=True)
        data.drop(columns=data.columns[0:9], inplace=True)
        data.rename(columns={'lesson2': 'lesson'}, inplace=True)

        mp3Only = data[data.english.isnull()][data.japanese.isnull()]

        assert mp3Only.count()[0] == 0  # suprised this is empty; ignoring it simplifies the below

        j = data[data.english.isnull()].sort_values(['mp3Url', 'japanese']).groupby(data.mp3Url).first()
        j.drop(columns=['english'], axis=1, inplace=True)

        e = data[data.japanese.isnull()].sort_values(['mp3Url', 'english']).groupby(data.mp3Url).first()
        e.drop(columns=['japanese'], axis=1, inplace=True)

        j = j.reset_index(level=0, drop=True).reset_index()
        e = e.reset_index(level=0, drop=True).reset_index()

        m = pd.merge(j, e, left_on='mp3Url', right_on='mp3Url', how='outer')

        dupcols = ['season', 'lesson']
        for dc in dupcols:
            m[dc] = m.apply(lambda r: r[f'{dc}_x'] or r[f'{dc}_y'], axis=1)
            m.drop(columns=[f'{dc}_x', f'{dc}_y'], inplace=True)
        m.drop(columns=[f'index_x', f'index_y'], inplace=True)
        m['transid'] = m.apply(lambda row: int(re.findall('transcript_(\d*)', row['mp3Url'])[0]), axis=1)
        m['dialogid'] = m.apply(lambda row: int(re.findall('(\d*)\\.mp3', row['mp3Url'])[0]), axis=1)
        m['filename'] = m.apply(lambda r: f"{r['season']}_{r['lesson']}_{r['transid']}_{r['dialogid']}.mp3", axis=1)
        m['tags'] = m.apply(lambda r: f"JPod {level} JPod_Season_{r['season']} JPod_Lesson_{r['lesson']}", axis=1)
        m['ankiaudio'] = m.apply(lambda r: f"[sound:{r['filename']}]", axis=1)
        m['ankiid'] = m.apply(lambda row: int(row['transid']) * 1000 + int(row['dialogid']), axis=1)
        m.sort_values(['season', 'lesson', 'transid', 'dialogid'], inplace=True)
        return m

    def save(self, df, fileNameNoExt):
        df[['ankiid', 'japanese', 'english', 'ankiaudio', 'tags']].to_csv(f"c:/japanese/{fileNameNoExt}_anki.csv",
                                                                          index=False)

    def download(self, df):
        todl = set()
        df[['mp3Url', 'filename']].apply(lambda r: todl.add(
            (r['mp3Url'], f"C:\\Users\\matte\\AppData\\Roaming\\Anki2\\Tirinst\\collection.media\\{r['filename']}")),
                                         axis=1)

        def df(d):
            downloadFile(d[0], d[1])

        # for d in todl:
        #    df(d)
        jp.Parallel(n_jobs=32)(jp.delayed(df)(d) for d in todl)

    def fixBeg(self, beg):
        # english offset for last 2
        cache = dict()

        def d(tid):
            if not tid in cache:
                cache[tid] = dialog(beg, tid)
            return cache[tid]

        d(2430).eng.remove([10])
        d(2430).clear([14])
        d(2429).jap.remove([8])
        d(2429).clear([13])

        d(534).eng.add(2)
        d(716).eng.add(1)
        d(760).eng.add(3)
        d(459).eng.adjmerge(2)
        d(459).eng.setValue(3, 'I like animation......')
        d(459).eng.remove([4])
        d(459).eng.setValue(5, 'something')
        d(459).eng.remove([10])

        d(992).eng.remove([1, 6])
        d(992).jap.remove([1])
        d(992).clear([11, 12])
        d(904).jap.remove([1])
        d(904).eng.remove([1])
        d(904).eng.split(3, 35)
        d(904).eng.split(9, 52)
        d(905).eng.remove([3, 5])
        d(962).remove([2])
        d(964).eng.remove([3])
        d(965).remove([2])
        d(967).remove([2])
        d(988).jap.remove([1])
        d(988).eng.remove([1, 2, 8])
        d(988).eng.split(3, 39)
        d(988).eng.split(7, 20)
        d(988).eng.split(8, 39)
        d(988).clear([11])
        d(989).add(1)
        d(989).add(1)
        d(989).eng.split(5, 36)
        d(990).remove([1])
        d(990).clear([10])
        d(991).remove([1])
        d(991).eng.split(2, 100)
        d(991).clear([11])
        d(994).eng.split(4, 57)
        d(994).eng.split(5, 61)
        d(994).eng.split(8, 58)
        d(1040).remove([1])
        d(1040).eng.split(2, 36)
        d(1040).eng.split(6, 55)
        d(1040).eng.split(8, 55 + len('esident officer in the New York office'))
        d(516).eng.shift([(9, 10)])
        d(516).eng.setValue(9)
        d(1039).eng.split(1, 46)
        d(1039).eng.split(4, 30)
        d(1039).eng.split(5, 78)
        d(1039).eng.split(8, 63)
        d(1039).eng.split(9, 67)
        d(1039).eng.split(10, 57)
        d(1040).eng.split(12, 39)
        d(1040).clear([14])
        d(1099).eng.remove([9])
        d(1523).eng.adjmerge(11)
        d(1670).eng.add(3)

        # find noises etc
        for a in beg.loc[(beg.english.str.contains('^\([^\(]*\)$', na=False)) & (
                beg.japanese.str.contains('^\([^\(]*\)$', na=False)), ['dialogid', 'transid']].values:
            d(a[1]).clear([a[0]])
        # dialogs
        beg.loc[(beg.japanese.str.contains('Listen to the full conversation.', na=False)), 'japanese'] = ''
        beg.loc[(beg.japanese.str.contains('Listen to the full conversation.', na=False)), 'ankiaudio'] = ''
        beg.loc[(beg.japanese.str.contains('Listen to the full conversation.', na=False)), 'english'] = ''
        #
        setEngValues = [(1459, 10, 'Alright, then let\'s go to the all you can eat Korean place.'),
                        (1459, 11, 'Can you meet me in the lobby in 15 minutes?'),
                        (1459, 12, 'Yes, that should be fine. Alright, I\'ll see you in 15 minutes.'),
                        (995, 7, 'This is great!! I have never had food this good in my life! '),
                        (995, 8, 'This is even better than the Yakiniku restaurant Keith Kim recommended! '),
                        (995, 9,
                         'Yo, I will never go to any other restaurants. From now on, I will have every meal here.'),
                        (995, 10, 'Thank you'),
                        (522, 6, 'That\'s alright. I always watch (the TV series) "Ge Ge Ge No Kitaro." I want to see what kind of ghosts pop out.'),
                        (557, 12, 'Because he always tries to cross a red light, saying "It\'s not scary if we all cross a red light together."'),
                        (905, 4, 'Not at all...I\'m hopeless. I have spent 20 thousand yen...Oh, I\'m taking that!'),

                        ]
        # (1279, 1, 74), (1279, 2, 32),, (1292, 3, 35)
        engshifts: List[Tuple[int, int, int]] = \
            [(114, 3, 51), (206, 13, 39), (206, 12, 40), (209, 1, 71), (211, 5, 55), (237, 1, 25), (421, 10, 58), (721, 2, 81), (903, 6, 71),
             (903, 9, 70), (961, 2, 40), (961, 4, 28), (962, 2, 75), (962, 7, 81), (963, 4, 84), (965, 3, 75), (966, 4, 124), (995, 1, 23),
             (1038, 1, 74), (1038, 8, 63), (1038, 10, 20), (1097, 2, 63), (1097, 4, 41), (1097, 5, 45), (1097, 7, 80), (1099, 4, 26),
             (1111, 3, 68), (1114, 1, 56), (1114, 3, 23), (1114, 4, 33), (1114, 8, 29), (1114, 9, 67), (1114, 11, 20), (1114, 14, 23),
             (1114, 15, 41), (1116, 3, 32), (1116, 4, 35), (1116, 5, 35), (1116, 7, 21), (1116, 8, 35), (1116, 9, 39), (1116, 11, 24),
             (1116, 12, 40), (1116, 14, 29), (1116, 16, 40), (1116, 17, 23), (1116, 18, 33), (1116, 20, 20), (1119, 3, 41), (1119, 4, 59),
             (1119, 6, 18), (1119, 7, 23), (1119, 9, 11), (1119, 11, 14), (1119, 13, 75), (1278, 1, 24), (1278, 2, 93), (1278, 3, 39),
             (1278, 4, 48), (1278, 5, 56), (1279, 6, 73), (1279, 7, 33), (1280, 1, 58), (1280, 2, 90), (1280, 7, 44), (1281, 6, 38),
             (1281, 9, 44), (1281, 9, 43), (1289, 3, 5), (1289, 5, 40), (1289, 6, 34), (1289, 10, 20), (1290, 2, 27), (1290, 3, 50),
             (1290, 4, 83), (1290, 7, 46), (1290, 9, 11), (1291, 3, 37), (1291, 6, 29), (1291, 9, 43), (1291, 10, 93), (1292, 3, 35),
             (1292, 5, 60), (1292, 6, 44), (1292, 10, 31), (1292, 11, 45), (1456, 2, 54), (1456, 4, 57), (1456, 6, 52), (1456, 8, 53),
             (1459, 3, 14), (1462, 4, 104), (1462, 7, 28), (1462, 10, 26), (1468, 6, 16), (1469, 3, 21), (1469, 4, 19), (1469, 6, 34),
             (1469, 8, 24), (1470, 11, 11), (1470, 16, 60), (1471, 6, 35), (1471, 7, 55), (1471, 10, 32), (1472, 2, 79), (1472, 6, 42),
             (1472, 7, 36), (1472, 8, 28), (1472, 9, 29), (1472, 10, 58), (1637, 12, 14), (1653, 1, 76), (1653, 3, 63), (1653, 6, 52),
             (1928, 3, 30), (1928, 10, 28), (1942, 1, 32), (1942, 5, 62), (1942, 6, 44), (1943, 5, 33), (1943, 12, 53), (1944, 7, 22),
             (1945, 2, 13), (1946, 4, 7), (1946, 10, 47), (1946, 12, 87), (1946, 15, 38)]

        sounds = [(236, 1), (995, 5)]
        fulldialogs = [(333, 9), (361, 11), (457, 18), (18, 18), (291, 6), (293, 12), (303, 9), (314, 6), (319, 8),
                       (327, 5), (353, 11), (363, 11), (364, 10), (367, 11), (372, 12), (391, 14)]
        for tid, did in fulldialogs:
            d(tid).clear([did])
        for tid, did in sounds:
            d(tid).clear([did])
        for tid, did, pos in engshifts:
            try:
                d(tid).eng.split(did, pos)
            except:
                print(f'{tid} {did}')
        for tid, did, value in setEngValues:
            d(tid).eng.setValue(did, value)

    def fixInt(self, int):
        cache: dict[str, dialog] = dict()

        def d(tid):
            if not tid in cache:
                cache[tid] = dialog(int, tid)
            return cache[tid]

        d(58).eng.adjmerges([13, 17])
        d(60).eng.adjmerges([14])
        d(61).eng.adjmerges([20, 20, 20])
        fixes = ["Once upon a time, there lived a poor but kind old man and his wife. ",
                 "On one New Year's Eve something happened.",
                 "The both of them, the old man and woman, made bamboo hats.", " They intended to buy New Year’s sticky rice cakes by bringing them to town and selling them.",
                 "“As there are 5 bamboo hats, we should be able to buy sticky rice cakes.”",
                 "“Please do so. After that, please be careful, as it will snow tonight.”",
                 "The old man left with 5 hats", " and as soon as the old man left the house it started to snow.",
                 " As the snow fall gradually became stronger, the old man hurried along the street.",
                 "As he came to the end of the village, there were 6 Jizousama lined up.", "Snow had accumulated on the head and shoulders of the Jizousama.",
                 "Upon seeing this, the old man could not continue on like this.",
                 "“Jizousama. It’s cold and snow is falling. Please wear this bamboo hat. “",
                 "The old man put the bamboo hats he was going to sell on the Jizousama.",
                 "However, there were only 5 hats, and 6 Jizousama.", " The old man then took off his own hat and placed it on the last Jizousama.",
                 "When he returned home, his wife said, “she was surprised.",
                 "“Well, well. That was quite fast. And, what happened to the bamboo hats?”",
                 "The old man spoke about the Jizousama. ", "“Well, well. That was a good thing you did. We don’t need sticky rice cakes.”",
                 "The old woman smiled and said",
                 "Later that night, in the middle of the night they heard a strange noise.",
                 "We came to pay gratitude for the bamboo hats. Where is that old man's house? We came to pay gratitude for the bamboo hats.” ",
                 "The singing voices drew closer, and when they finally came to the old man’s house, quiet! Then there was a sound of someone placing something, and just like that vanished.",
                 "When the old man opened the door, he could see the disappearing outlines of the last Jizousama he gave the bamboo hats to.",
                 "And in front of the house was a huge stack of sticky rice cakes and food."]
        for f in range(0, len(fixes)):
            d(64).eng.setValue(f + 1, fixes[f])
        d(64).clear(range(27, 33))
        d(66).eng.adjmerges([2, 5, 12, 13, 14, 15, 15])
        d(66).clear(range(17, 24))
        d(441).eng.mergesomeup(2, 121)
        d(445).eng.mergesomeup(1, 99)
        d(445).eng.splits(2, [49, 54, 87, 64, 23, 38])

        d(403).jap.remove([1])
        d(525).jap.remove([8])


def begginner():
    jta = JpodToAnki()
    #
    beg = jta.parseJodLevelDump('begsen', 'Beginner')
    # beg.to_csv(f"c:/japanese/begsen_unfixed.csv",index=False)
    beg = pd.read_csv(f"c:/japanese/begsen_unfixed.csv")
    jta.fixBeg(beg)
    # jta.download(beg)
    jta.save(beg, 'begsen')
    # parseJodLevelDump('intsen', 'Intermediate')


def intermediate():
    jta = JpodToAnki()
    intsen = 'intsen'
    #int = jta.parseJodLevelDump(intsen, 'Int')
    #int.to_csv(f"c:/japanese/{intsen}_unfixed_withdia.csv",index=False)
    # jta.save(int, f'{intsen}_unfixed')

    int = pd.read_csv(f"c:/japanese/{intsen}_unfixed_withdia.csv")


    #jta.download(int)
    jta.fixInt(int)
    int.sort_values(by='ankiid')[['japanese', 'english', 'ankiid', 'lesson']].to_csv('c:/japanese/intsen_pairs.csv', index=False)

    int.sort_values(by=['season', 'lesson', 'dialogid'])[['lesson', 'season', 'dialogid']].to_csv('c:/japanese/intsen_lessease.csv', index=False)
    # int.sort_values(by='ankiid')[['english']].to_csv('c:/japanese/intsen_engonly.csv', index=False)
    int[int['season'].str.match('.*lowerint.*', case=False, na=False)][['japanese']].to_csv('c:/japanese/intsen_lowerint.csv', index=False)
    # int = pd.read_csv(f"c:/japanese/{intsen}_unfixed_anki.csv")
    jta.save(int, intsen)
    # parseJodLevelDump('intsen', 'Intermediate')


intermediate()
