from unittest import TestCase

from AnkiDb import AnkiDb
from AnkiDbReader import AnkiDbReader

class TestAnkiDbReader(TestCase):


    def test_get10kvocab(self):
        with AnkiDb() as ad:
            adr = AnkiDbReader(ad)
            cds = adr.getCardDefs('AllSentences')
            self.assertTrue('Reading' in cds)
            self.assertTrue('Audio' in cds)

    def test_gasdf(self):
        with AnkiDb() as ad:
            adr = AnkiDbReader(ad)
            nd = adr.getNoteFields()
            self.assertTrue('Japanese' in nd)
            self.assertTrue('Audio' in nd)

    def test_allVocab(self):
        with AnkiDb() as ad:
            adr = AnkiDbReader(ad)
            v = adr.allVocab()
            self.assertEqual(len(v), 12466)
    def test_allSen(self):
        with AnkiDb() as ad:
            adr = AnkiDbReader(ad)
            v = adr.getAllSentences()
            self.assertEqual(len(v), 108276)
