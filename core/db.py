import sqlite3
from concurrent import futures

from core.utils import finder

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS fragments (
        file_name TEXT PRIMARY KEY,
        sub_text TEXT,
        duration REAL,
        media_file TEXT
);
"""

INSERT_MANY = """
    INSERT INTO fragments VALUES(?, ?, ?, ?)
"""

GET_ALL_PHRASES = """
    SELECT sub_text FROM fragments;
"""


class Database(object):
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.prepare()

    def prepare(self):
        self.cursor.execute(CREATE_TABLE)
        self.conn.commit()

    def find_dulpicates(self, subs):
        phrases = set(s for s in self.get_all_phrases())
        counter = 0
        for media_file, values in subs.items():
            no_dupl = []
            for sub in values["subtitles"]:
                if sub["text"] not in phrases:
                    no_dupl.append(sub)
                else:
                    counter += 1

            values["subtitles"] = no_dupl

        return counter, subs

    def find_similar(self, subs, ratio=90, workers=4):
        phrases = set(s for s in self.get_all_phrases())
        counter = 0
        subtitles_dict = {}

        with futures.ProcessPoolExecutor(max_workers=workers) as executor:
            i = 0
            tasks = []
            for media_file, values in subs.items():
                f_obj = executor.submit(finder, phrases, values, i, ratio)
                subtitles_dict[i] = media_file
                tasks.append(f_obj)
                i += 1

            for task in futures.as_completed(tasks):
                values, i, count = task.result()
                media_file = subtitles_dict[i]
                subs[media_file] = values
                counter += count
        return counter, subs

    def get_all_phrases(self):
        phrases = self.cursor.execute(GET_ALL_PHRASES)
        return [ph[0] for ph in phrases.fetchall()]

    def save_subs(self, subtitles) -> int:
        inp = []
        for media_file, values in subtitles.items():
            for sub in values["subtitles"]:
                inp.append((sub["filename"], sub["text"], sub["duration"], media_file))
        self.cursor.executemany(INSERT_MANY, inp)
        self.conn.commit()
        return self.conn.total_changes
