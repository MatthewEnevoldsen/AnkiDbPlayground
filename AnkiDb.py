from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


class AnkiDb:
    def __init__(self):
        #dbPath = f"C:/Users/matte/AppData/Roaming/Anki2/Tirinst/collection.anki2"
        dbPath = f"C:/Users/matte/AppData/Roaming/Anki2/Tirinst/collection.anki2.pycharm"
        Base = automap_base()
        engine = create_engine(f"sqlite:///{dbPath}")
        Base.prepare(engine, reflect=True)

        self.notes = Base.classes.notes
        self.cards = Base.classes.cards
        self.col = Base.classes.col
        self.revlog = Base.classes.revlog
        self.session = Session(engine)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()