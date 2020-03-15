import re
import pandas as pd
import os
import requests
import csv
from Utils.windows import *
from joblib import Parallel, delayed
import JpodHtmlParser as jhp

class JpodParser:
    def parseJodLevelDump(self, fileNameNoExt, level):
        data = pd.read_csv(f"c:/japanese/{fileNameNoExt}.csv")

        def getseason(row):
            season = re.findall('.*/(.*?)/', row['pathways-href'])[0]
            return re.sub(r'\W+', '', season)

        def getlesson(row):
            lesson = re.findall('(.*?)\s*\n', row['lesson'])[0]
            return re.sub(r'\W+', '', lesson)
        parser = jhp.JpodHtmlParser()
        data['japanese'] = data.apply(lambda row: parser.getsen(row['kanjisen']), axis=1)
        data['mp3Url'] = data.apply(lambda row: parser.getmp3(row['kanjisen']) or parser.getmp3(row['engsen']), axis=1)
        data['english'] = data.apply(lambda row: parser.getsen(row['engsen']), axis=1)
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
        m['tags'] = m.apply(lambda r: f"JPod {level} {r['season']} {r['lesson']}", axis=1)
        m['ankiaudio'] = m.apply(lambda r: f"[sound:{r['filename']}]", axis=1)
        m['ankiid'] = m.apply(lambda row: int(row['transid']) * 1000 + int(row['dialogid']), axis=1)
        m.sort_values(['season', 'lesson','transid', 'dialogid'], inplace=True)
        return m
    def save(self, df, fileNameNoExt):
        df[['ankiid', 'japanese', 'english', 'ankiaudio', 'tags']].to_csv(f"c:/japanese/{fileNameNoExt}_anki.csv", index=False)
    def download(self, df):
        todl = set()
        df[['mp3Url', 'filename']].apply(lambda r: todl.add((r['mp3Url'], f"C:\\Users\\matte\\AppData\\Roaming\\Anki2\\Tirinst\\collection.media\\{r['filename']}")), axis=1)
        def df(d):
            downloadFile(d[0], d[1])
        for d in todl:
            df(d)
        #Parallel(n_jobs=8)(delayed(df)(d) for d in downloads)

    def shiftup(self, df, transid, dialogids, col):
        for did in dialogids:
            nextdid = did + 1
            df.loc[(df.transid == transid) & (df.dialogid == did), col] = df.loc[(df.transid == transid) & (df.dialogid == nextdid), col].values[0]
    def shiftdown(self, df, transid, dialogids, col):
        #4=>5, 5 = 4
        #5=>6, 6 = 5
        #4 = ''?

        for did in sorted(dialogids, reverse=True):
            nextdid = did - 1
            df.loc[(df.transid == transid) & (df.dialogid == did), col] = df.loc[(df.transid == transid) & (df.dialogid == nextdid), col].values[0]
    def deleteEntry(self, df, transid, did):
        #don't really want to delete, just want it to be clear in anki
        self.setValue(df, transid, did, 'english', '')
        self.setValue(df, transid, did, 'japanese', '')
        self.setValue(df, transid, did, 'ankiaudio', '')
    def setValue(self, df, transid, did, field, value):
        df.loc[(df.transid == transid) & (df.dialogid == did), field] = value

    def fixBeg(self, beg):
        #english offset for last 2
        self.shiftup(beg, 2430, range(10, 14), 'english')
        self.deleteEntry(beg, 2430, 14)
        self.shiftup(beg, 2429, range(8, 13), 'japanese')
        self.deleteEntry(beg, 2429, 13)
        self.shiftup(beg, 992, range(6, 12), 'english')
        self.shiftup(beg, 992, range(1, 12), 'japanese')
        self.shiftup(beg, 992, range(1, 12), 'english')
        bothNoise = (beg.english.str.contains('^\([^\(]*\)$', na=False)) & (beg.japanese.str.contains('^\([^\(]*\)$', na=False))
        beg.loc[bothNoise, 'english'] = ''
        beg.loc[bothNoise, 'japanese'] = ''
        beg.loc[bothNoise, 'ankiaudio'] = ''

        beg.loc[(beg.japanese.str.contains('Listen to the full conversation.', na=False)), 'japanese'] = ''
        beg.loc[(beg.japanese.str.contains('Listen to the full conversation.', na=False)), 'ankiaudio'] = ''

        #114003 - move half the english down, shift the rest
        self.shiftdown(beg, 992, range(5, 13), 'english')
        self.setValue(beg, 114, 3, 'english', 'Yeah? I\'m leaving now. I\'ve bought food and drinks.')
        self.setValue(beg, 114, 4, 'english', 'I also changed the batteries in the radio. Preparations are complete.')

        self.shiftdown(beg, 206, range(14,15), 'english')
        self.setValue(beg, 206, 12, 'english', 'Just as I thought, I am a hated person.')
        self.setValue(beg, 206, 13, 'english', 'It was on purpose, right?')

        self.shiftdown(beg, 237, range(3,11), 'english')
        self.setValue(beg, 237, 1, 'english', 'Wait! Hold that elevator!')
        self.setValue(beg, 237, 2, 'english', 'Thank you')




jp = JpodParser()

beg = jp.parseJodLevelDump('begsen', 'Beginner')
jp.fixBeg(beg)
jp.download(beg)
jp.save(beg, 'begsen')
#parseJodLevelDump('intsen', 'Intermediate')
