from unittest import TestCase
import JpodHtmlParser as jp

class TestJpodHtmlParser(TestCase):
    def test_true2(self):
        pass
    def test_getsenwierdquote(self):
        str = '''<td class="lsn3-lesson-dialogue__td--recorder">
            <button aria-label="Voice Recorder" type="button" tabindex="0" title="Voice Recorder" data-url="https://cdn.innovativelanguage.com/japanesepod101/learningcenter/audio/transcript_2423/6.mp3" data-text="" the="" rules"??　もりさんのですか。"="" class="js-lsn3-record-voice js-lsn3-tabindex r101-recorder-a__icon"></button>
        </td><td class="lsn3-lesson-dialogue__td--play">
            <button type="button" class="js-lsn3-play-dialogue" title="Play" aria-label="Play" data-src="https://cdn.innovativelanguage.com/japanesepod101/learningcenter/audio/transcript_2423/6.mp3" data-type="audio/mp3"></button>
        </td><td class="lsn3-lesson-dialogue__td--name">B:</td><td class="lsn3-lesson-dialogue__td--text" lang="ja">"The Rules"??　もりさんのですか。</td>'''
        exp = '"The Rules"??　もりさんのですか。'
        res = jp.getsen(str)
        self.assertEqual(exp, res)

    def test_getmpr(self):
        str = '<td class="lsn3-lesson-dialogue__td--text" lang="ja" colspan="4">（木ノ下、帽子をかぶる）</td>'
        pass
