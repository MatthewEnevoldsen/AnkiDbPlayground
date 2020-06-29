from unittest import TestCase
import JapDictParser as jdp
import  Tokeniser as t


class Test(TestCase):
    def getwords(self, sen):
        d = jdp.getDict()
        return t.splittowords(sen,d)

    def test_get_dict(self):
        d = jdp.getDict()
        self.assertTrue('めちゃくちゃ' in d)
    def test_amose(self):
        d = jdp.getDict()
        words = t.splittowords('あ、この人、めちゃくちゃ綺麗な人だな', d)
        self.assertTrue('めちゃくちゃ' in words)
    def test_earthquake(self):
        words = self.getwords('口座にお金がないと、引き出せないので…。')
        d = jdp.getDict()
        print(words)
        for w in words:
            print(w)
            print(d[w])


