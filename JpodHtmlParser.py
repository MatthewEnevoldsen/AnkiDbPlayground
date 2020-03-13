from Utils.windows import *


class JpodHtmlParser:
    def toxml(self, weirdhtmloutput):
        html = weirdhtmloutput.replace('"<', '"').replace('>"', '"')
        return ET.fromstring(f'<a>{html}</a>')

    def getsen(self, html):
        if pd.isnull(html):
            return None
        def datatext(s):
            xml = toxml(s)
            return xml[0][0].attrib['data-text']
        def singleline(s):
            xml = toxml(s)
            return xml[0].text
        def fromfinal(s):
            return re.match('<td class[^<]*?lang=\".*?\">.*</td>', s)
        for f in [datatext, singleline, fromfinal]:
            try:
                return f(html)
            except:
                pass
        return None

    def getmp3(self, html):
        if pd.isnull(html):
            return None
        try:
            xml = self.toxml(html)
            return xml[0][0].attrib['data-url']
        except:
            return None

