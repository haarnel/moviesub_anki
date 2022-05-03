import pysrt

from core.db import Database
from core.utils import *

ALLOWED_EXTENSIONS = [".mkv", ".mp4", ".avi", ".mp3"]


def main(deck_name, multi=None, video=None, srt_file=None):
    settings = load_config(deck_name, config_file="config.ini")
    subtitles = {}
    counter = 0
    if not multi:
        parsed = pysrt.open(srt_file)
        subtitles[video] = {"srt_file": srt_file, "subtitles": parsed}
        counter += len(parsed)
    else:
        subtitles = {}
        media_files = []
        sub_files = []
        for root, _, files in os.walk(multi):
            for file in files:
                _, ext = os.path.splitext(file)
                path = os.path.join(root, file)
                if ext in ALLOWED_EXTENSIONS:
                    subtitles[path] = {"srt_file": None}
                    media_files.append(path)
                elif ext == ".srt":
                    sub_files.append(path)
                else:
                    raise ValueError(
                        f"Not Supported file extension {ext} {path}\nmedia formats: {ALLOWED_EXTENSIONS}\nSub formats: .srt (SubRip)"
                    )

        for sub in sub_files:
            filename, _ = os.path.splitext(sub)
            names = [filename + ext for ext in ALLOWED_EXTENSIONS]
            for name in names:
                if name in subtitles:
                    subtitles[name]["srt_file"] = sub
                    parsed = pysrt.open(sub)
                    subtitles[name]["subtitles"] = parsed
                    counter += len(parsed)
    x, i, j = 0, 0, 0
    for key, value in subtitles.items():
        if value.get("subtitles"):
            print(f"Found: {key} -> {value['srt_file']}")
            i += 1
        else:
            j += 1
            print(f"Not Found: {key} -> ???")
        x += 1

    print(f"Collected: {i}/{j}/{x}")
    print("Loaded: ", counter)
    subtitles, counter = prepare_subtitles(subtitles, settings)
    print("Filtered: ", counter)
    db = Database(db_path=settings["DB_DIR"])
    counter_post = 0
    if not settings["ONLY_MARKED_SUBS"]:
        if settings["FIND_DUPLICATES"]:
            dupl_count, subtitles = db.find_dulpicates(subtitles)
            print("Duplicates: ", dupl_count)
            counter_post += dupl_count

        if settings["FIND_SIMILAR"]:
            siml_count, subtitles = db.find_similar(
                subtitles, 
                ratio=settings["FIND_SIMILAR_RATIO"],
                workers=settings["MAX_WORKER_COUNT"],
            )
            print("Similar: ", siml_count)
            counter_post += siml_count

    if counter - counter_post > 0:
        video_cutter(subtitles, settings)
        counter = db.save_subs(subtitles)
        print("Saved to db: ", counter)
        deck = create_anki_deck(subtitles, deck_name, settings)
        print(f"Anki deck was created: {deck.name}.apkg")

    print("#" * 40)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Anki movie 0.1")
    parser.add_argument("-v", "--video", type=str, required=False)
    parser.add_argument("-s", "--subtitles", type=str, required=False)
    parser.add_argument("-m", "--multi", type=str, required=False, default="")
    parser.add_argument("-d", "--deck", type=str, required=True, help="Deck name")
    args = parser.parse_args()

    main(args.deck, args.multi, args.video, args.subtitles)
