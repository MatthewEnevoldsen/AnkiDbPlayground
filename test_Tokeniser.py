from unittest import TestCase
import JapDictParser as jdp
import Tokeniser

class Test(TestCase):
    def test_splittowords(self):
        basetoentry, conjugtobase = jdp.getmergedentries()
        sen = '彼は飲酒にふけって健康を害した'
        allwords = Tokeniser.splittowords(sen, conjugtobase)

        self.fail()
    def test_reccyboy(self):
        basetoentry, conjugtobase = jdp.getmergedentries()
        sen = '彼は飲酒にふけって健康を害した'
        allwords = Tokeniser.maxlensqtokens(sen, conjugtobase)
        self.assertTrue(len(allwords) == 5)

    def test_reccyboysimp(self):
        basetoentry, conjugtobase = jdp.getmergedentries()
        sen = '彼は飲酒'
        allwords = Tokeniser.maxlensqtokens(sen, conjugtobase)
        self.assertTrue(len(allwords) == 3)


