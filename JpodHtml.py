import xml.etree.ElementTree as ET
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

        def downloadFile(url: str, dest: str):
            if not os.path.exists(dest):
                r = requests.get(url, allow_redirects=True)
                open(dest, 'wb').write(r.content)

        def getseason(row):
            season = re.findall('.*/(.*?)/', row['pathways-href'])[0]
            return re.sub(r'\W+', '', season)

        def getlesson(row):
            lesson = re.findall('(.*?)\s*\n', row['lesson'])[0]
            return re.sub(r'\W+', '', lesson)

        data['japanese'] = data.apply(lambda row: jhp.getsen(row['kanjisen']), axis=1)
        data['mp3Url'] = data.apply(lambda row: jhp.getmp3(row['kanjisen']) or getmp3(row['engsen']), axis=1)
        data['english'] = data.apply(lambda row: jhp.getsen(row['engsen']), axis=1)
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
        m['tags'] = m.apply(lambda r: f"JPod {level} {r['season']} {r['lesson']} {r['transid']}", axis=1)
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

    def shift(self, df, transid, dialogids, col):
        for did in dialogids:
            nextdid = did + 1
            df.loc[(df.transid == transid) & (df.dialogid == did), col] = df.loc[(df.transid == transid) & (df.dialogid == nextdid), col].values[0]
    def deleteEntry(self, df, transid, did):
        #don't really want to delete, just want it to be clear in anki
        df.loc[(df.transid == transid) & (df.dialogid == did), 'english'] = ''
        df.loc[(df.transid == transid) & (df.dialogid == did), 'japanese'] = ''
        df.loc[(df.transid == transid) & (df.dialogid == did), 'ankiaudio'] = ''


    def fixBeg(self, beg):
        #english offset for last 2
        self.shift(beg, 2430, range(10, 14), 'english')
        self.deleteEntry(beg, 2430, 14)
        self.shift(beg, 2429, range(8, 13), 'japanese')
        self.deleteEntry(beg, 2429, 13)
        self.shift(beg, 992, range(6, 12), 'english')
        self.shift(beg, 992, range(1, 12), 'japanese')
        self.shift(beg, 992, range(1, 12), 'english')
        bothNoise = (beg.english.str.contains('^\([^\(]*\)$', na=False)) & (beg.japanese.str.contains('^\([^\(]*\)$', na=False))
        beg.loc[bothNoise, 'english'] = ''
        beg.loc[bothNoise, 'japanese'] = ''
        beg.loc[bothNoise, 'ankiaudio'] = ''

jp = JpodParser()

beg = jp.parseJodLevelDump('begsen', 'Beginner')
jp.fixBeg(beg)
jp.download(beg)
jp.save(beg, 'begsen')
#parseJodLevelDump('intsen', 'Intermediate')
