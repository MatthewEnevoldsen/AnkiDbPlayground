import xml.etree.ElementTree as ET
from Utils.windows import *
import pandas as pd


def __init__():
    pass

class JpodHtmlParser:

    def toxml(self, weirdhtmloutput):
        html = weirdhtmloutput.replace('"<', '"').replace('>"', '"')
        return ET.fromstring(f'<a>{html}</a>')

    def getsen(self, html):
        if pd.isnull(html):
            return None
        def datatext(s):
            xml = self.toxml(s)
            return xml[0][0].attrib['data-text']
        def singleline(s):
            xml = self.toxml(s)
            return xml[0].text
        def fromfinal(s):
            return re.findall('<td class[^<]*?lang=\".*?\">(.*)</td>', s)[0]
        for f in [datatext, singleline, fromfinal]:
            try:
                return f(html)
            except:
                pass
        return None

    def getmp3(self, html):
        if pd.isnull(html):
            return None
        def byregex(s):
            re.findall('(https.*?mp3)', s)[0]
        def byxml(s):
            xml = self.toxml(s)
            return xml[0][0].attrib['data-url']
        for f in [byxml, byregex]:
            try:
                return f(html)
            except:
                pass
        return None