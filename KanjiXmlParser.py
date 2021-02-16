import xml.etree.ElementTree as ET
import pandas as pd

def getKanji():
    xmlFile = 'c:\japanese\kanjidic2.xml'
    jlptkanji = {c for c in open('c:\japanese\\rawkanji.txt', "r", encoding='utf-8').read()}

    xml = ET.parse(xmlFile)
    root = xml.getroot()
    records = dict()
    for c in root.findall('character'):
        char = c.find('literal').text
        if char in jlptkanji:
            strokecount = '0'
            misc = c.find('misc')
            if misc is not None:
                strokecountfield = misc.find('stroke_count')
                if strokecountfield is not None:
                    strokecount = strokecountfield.text
            rm = c.find('reading_meaning')
            if rm is None:
                continue
            rmg = rm.find('rmgroup')
            if rmg is None:
                continue
            kunreadings = [r.text for r in rmg.findall('reading') if r.attrib['r_type'] == 'ja_kun']
            onreadings = [r.text for r in rmg.findall('reading') if r.attrib['r_type'] == 'ja_on']
            meanings = [r.text for r in rmg.findall('meaning') if 'm_lang' not in r.attrib]
            records[char] = [' '.join(kunreadings), ' '.join(onreadings), ' '.join(meanings), strokecount]
    return records

