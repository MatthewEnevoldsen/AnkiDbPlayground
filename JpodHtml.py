import re
from typing import List, Sequence, Tuple

import pandas as pd

import JpodHtmlParser as jp
from Utils.windows import downloadFile


class JpodToAnki:
    def parseJodLevelDump(self, fileNameNoExt, level):
        data = pd.read_csv(f"c:/japanese/{fileNameNoExt}.csv")

        def getseason(row):
            season = re.findall('.*/(.*?)/', row['pathways-href'])[0]
            return re.sub(r'\W+', '', season)

        def getlesson(row):
            lesson = re.findall('(.*?)\s*\n', row['lesson'])[0]
            return re.sub(r'\W+', '', lesson)

        data['japanese'] = data.apply(lambda row: jp.getsen(row['kanjisen']), axis=1)
        data['mp3Url'] = data.apply(lambda row: jp.getmp3(row['kanjisen']) or jp.getmp3(row['engsen']), axis=1)
        data['english'] = data.apply(lambda row: jp.getsen(row['engsen']), axis=1)
        data['lesson2'] = data.apply(getlesson, axis=1)
        data['season'] = data.apply(getseason, axis=1)

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

        for d in todl:
            df(d)
        # Parallel(n_jobs=8)(delayed(df)(d) for d in downloads)

    def shift(self, df, transid: int, fromto: Sequence[Tuple[int, int]], col: str):
        def getval(id):
            return df.loc[(df.transid == transid) & (df.dialogid == id), col].values[0]

        values = {m[0]: getval(m[0]) for m in fromto}
        for m in fromto:
            self.setValue(df, transid, m[1], col, values[m[0]])

    def shiftup(self, df, transid: int, dialogids: Sequence[int], col: str):
        # 1=2 so 2=>1
        self.shift(df, transid, [(i, i - 1) for i in dialogids], col)

    def shiftdown(self, df, transid: int, dialogids: Sequence[int], col: str):
        # 4=>5, 5 = 4
        self.shift(df, transid, [(i, i + 1) for i in dialogids], col)

    def deleteEntry(self, df, transid, did):
        # don't really want to delete, just want it to be clear in anki
        self.setValue(df, transid, did, 'english', 'a')
        self.setValue(df, transid, did, 'japanese', 'a')
        self.setValue(df, transid, did, 'ankiaudio', 'a')

    def setValue(self, df, transid, did, field, value):
        df.loc[(df.transid == transid) & (df.dialogid == did), field] = value

    def fixBeg(self, beg):
        # english offset for last 2
        self.shiftup(beg, 2430, set(range(10, 14)), 'english')
        self.deleteEntry(beg, 2430, 14)
        self.shiftup(beg, 2429, range(8, 13), 'japanese')
        self.deleteEntry(beg, 2429, 13)
        self.shiftup(beg, 992, range(6, 12), 'english')
        self.shiftup(beg, 992, range(1, 12), 'japanese')
        self.shiftup(beg, 992, range(1, 12), 'english')
        for a in beg.loc[(beg.english.str.contains('^\([^\(]*\)$', na=False)) & (
            beg.japanese.str.contains('^\([^\(]*\)$', na=False)), ['dialogid', 'transid']].values:
            self.deleteEntry(beg, a[1], a[0])

        beg.loc[(beg.japanese.str.contains('Listen to the full conversation.', na=False)), 'japanese'] = ''
        beg.loc[(beg.japanese.str.contains('Listen to the full conversation.', na=False)), 'ankiaudio'] = ''

        # 114003 - move half the english down, shift the rest
        self.shiftdown(beg, 114, range(4, 13), 'english')
        self.setValue(beg, 114, 3, 'english', 'Yeah? I\'m leaving now. I\'ve bought food and drinks.')
        self.setValue(beg, 114, 4, 'english', 'I also changed the batteries in the radio. Preparations are complete.')

        self.shiftdown(beg, 206, range(13, 15), 'english')
        self.setValue(beg, 206, 12, 'english', 'Just as I thought, I am a hated person.')
        self.setValue(beg, 206, 13, 'english', 'It was on purpose, right?')

        self.shiftdown(beg, 237, range(2, 11), 'english')
        self.setValue(beg, 237, 1, 'english', 'Wait! Hold that elevator!')
        self.setValue(beg, 237, 2, 'english', 'Thank you')


        self.shiftdown(beg, 1459, range(4, 12), 'english')
        self.setValue(beg, 1459, 3, 'english', 'This is Maeda.')
        self.setValue(beg, 1459, 4, 'english', 'Can you come out for a moment Shimoyama?')

        self.setValue(beg, 1459, 10, 'english', 'Alright, then let\'s go to the all you can eat Korean place.')
        self.setValue(beg, 1459, 11, 'english', 'Can you meet me in the lobby in 15 minutes?')
        self.setValue(beg, 1459, 12, 'english', 'Yes, that should be fine. Alright, I\'ll see you in 15 minutes.')

        self.shift(beg, 516, [(9, 10)], 'english')
        self.deleteEntry(beg, 516, 9)

        fulldialogs = [(333,9), (361,11), (457,18)]
        for d in fulldialogs:
            self.deleteEntry(beg, d[0], d[1])


jta = JpodToAnki()

beg = jta.parseJodLevelDump('begsen', 'Beginner')
jta.fixBeg(beg)
jta.download(beg)
jta.save(beg, 'begsen')
# parseJodLevelDump('intsen', 'Intermediate')
