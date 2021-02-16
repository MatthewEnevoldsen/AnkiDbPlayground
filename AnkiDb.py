from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


class AnkiDb:
    def __init__(self):
        #db_path = f"C:/Users/matte/AppData/Roaming/Anki2/Tirinst/collection.anki2"
        db_path = f"C:/Users/matte/AppData/Roaming/Anki2/Tirinst/collection - Copy.anki2"
        base = automap_base()
        engine = create_engine(f"sqlite:///{db_path}")
        base.prepare(engine, reflect=True)

        self.notes = base.classes.notes
        self.cards = base.classes.cards
        self.col = base.classes.col
        self.notetypes = base.classes.notetypes
        self.fields = base.classes.fields
        self.revlog = base.classes.revlog
        self.session = Session(engine)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
