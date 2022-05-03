import configparser
import multiprocessing
import os
import random
from concurrent import futures
from datetime import datetime
from subprocess import run
from uuid import uuid4

import genanki
from fuzzywuzzy import fuzz

from core.filters import apply_filters

FFMPEG_CUT = '{ffmpeg} -ss {start} -i {video} -c:a aac -b:a {bitrate}k -t {duration} -vf "scale=max({width}\,a*{height}):max({height}\,{width}/a),crop={width}:{height}" {output} -loglevel quiet '
FFMPEG_AUDIO = '{ffmpeg} -ss {start} -i {video} -t {duration} -q:a 0 -map a {output} -loglevel quiet '

def load_config(deck_name, config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    s = config["SETTINGS"]
    f = config["FILTERS"]
    filters = [
        opt for opt, _ in f.items() if opt.startswith("remove") and f.getboolean(opt)
    ]
    data_dir = s.get("DATA_DIR", "")
    include_media = s.getboolean("INCLUDE_MEDIA", False)
    if not include_media:
        date_string = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        folder_name = deck_name.replace(" ", "-") + "-" + date_string
        data_dir = os.path.join(data_dir, folder_name)
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
    else:
        data_dir = ""

    settins_dict = {
        "DATA_DIR": data_dir,
        "DB_DIR": s.get("DB_DIR", os.path.join(data_dir, "database.db")),
        "INCLUDE_MEDIA": include_media,
        "FFMPEG_BINARY": s.get("FFMPEG_BINARY", "ffmpeg"),
        "VIDEO_WIDTH": s.getint("VIDEO_WIDTH", 480),
        "VIDEO_HEIGHT": s.getint("VIDEO_HEIGHT", 320),
        "BITRATE": s.getint("BITRATE", 320),
        "MAX_WORKER_COUNT": s.getint("MAX_WORKER_COUNT", multiprocessing.cpu_count()),
        "SHOW_LOG": s.getboolean("SHOW_LOG", True),
        "EXTRACT_ONLY_AUDIO": s.getboolean("EXTRACT_ONLY_AUDIO", False),
        "FIND_DUPLICATES": f.getboolean("FIND_DUPLICATES", False),
        "ONLY_MARKED_SUBS": f.get("ONLY_MARKED_SUBS", ""),
        "MAX_SUB_DURATION": f.getint("MAX_SUBTITLE_DURATION", 10),
        "MIN_SUB_DURATION": f.getint("MIN_SUBTITLE_DURATION", 20),
        "MAX_SUB_LENGTH": f.getint("MAX_SUBTITLE_LENGTH", 120),
        "MIN_SUB_LENGTH": f.getint("MIN_SUBTITLE_LENGTH", 30),
        "PAD_TIME_START": f.getfloat("PAD_TIME_START", 0.0),
        "PAD_TIME_END": f.getfloat("PAD_TIME_END", 0.0),
        "FILTERS": filters,
        "FIND_SIMILAR": f.getboolean("FIND_SIMILAR", False),
        "FIND_SIMILAR_RATIO": f.getint("FIND_SIMILAR_RATIO", 100),
    }
    return settins_dict


def prepare_subtitles(subtitles, settings):
    marked = settings["ONLY_MARKED_SUBS"]
    counter = 0
    seen = set()
    for media_file, values in subtitles.items():
        subs = values["subtitles"]
        parsed_subs = []
        for sub in subs:
            if marked:
                if marked in sub.text:
                    parsed_subs.append(sub)
                continue

            s_len = len(sub.text)
            dt = sub.duration.to_time()
            dt_seconds = (dt.hour * 60 + dt.minute) * 60 + dt.second
            if (
                s_len >= settings["MIN_SUB_LENGTH"]
                and s_len <= settings["MAX_SUB_LENGTH"]
                and dt_seconds >= settings["MIN_SUB_DURATION"]
                and dt_seconds <= settings["MAX_SUB_DURATION"]
            ):

                if settings["FILTERS"]:
                    sub = apply_filters(sub=sub, filters=settings["FILTERS"])
                if sub.text not in seen:
                    parsed_subs.append(sub)
                    seen.add(sub.text)

        formated_subs = []
        pad_start = int(settings["PAD_TIME_START"] * 1000)
        pad_end = int(settings["PAD_TIME_END"] * 1000)
        for sub in parsed_subs:
            start = (sub.start - pad_start).to_time().isoformat()
            duration = (sub.duration + pad_end).to_time().isoformat()
            counter += 1
            formated_subs.append(
                {
                    "text": sub.text.replace(marked, "").strip(),
                    "start": start,
                    "end": sub.end.to_time().isoformat(),
                    "duration": duration,
                }
            )
        values["subtitles"] = formated_subs

    return subtitles, counter


def create_anki_deck(subtitles, deck_name, settings):
    model_id = 1123282242
    deck_id = random.randrange(1 << 30, 1 << 31)
    fields = [{"name": "Phrase"}, {"name": "Media"}]
    template = [
        {
            "name": "Card",
            "qfmt": "{{type:Phrase}}<br>{{Media}}",
            "afmt": "{{FrontSide}}{{Phrase}}",
        },
    ]
    css = open("data/style.css").read()
    model = genanki.Model(
        model_id=model_id,
        name="Movie Model",
        fields=fields,
        templates=template,
        css=css,
    )
    deck = genanki.Deck(deck_id, deck_name)
    media_files = []
    for media_file, values in subtitles.items():
        for sub in values["subtitles"]:
            note = genanki.Note(
                model=model, fields=[sub["text"], f"[sound:{sub['filename']}]"]
            )
            deck.add_note(note)
            media_files.append(sub["filename"])

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(f"{deck_name}.apkg")
    if settings["INCLUDE_MEDIA"]:
        for file in media_files:
            os.remove(file)
    return deck


def cut_video(sub, settings, video):
    command = FFMPEG_CUT.format(
        ffmpeg=settings["FFMPEG_BINARY"],
        start=sub["start"],
        video=video,
        duration=sub["duration"],
        width=settings["VIDEO_WIDTH"],
        height=settings["VIDEO_HEIGHT"],
        output=sub["filename"],
        bitrate=settings["BITRATE"],
    )
    run(command, shell=True, universal_newlines=True)


def cut_audio(sub, settings, video):
    command = FFMPEG_AUDIO.format(
        ffmpeg=settings["FFMPEG_BINARY"],
        start=sub["start"],
        video=video,
        duration=sub["duration"],
        output=sub["filename"],
    )
    run(command, shell=True, universal_newlines=True)

def video_cutter(subtitles, settings):

    with futures.ProcessPoolExecutor(settings['MAX_WORKER_COUNT']) as executor:
        save = {}
        tasks = []
        idx = 1
        for media_file, values in subtitles.items():
            for sub in values["subtitles"]:
                if settings["EXTRACT_ONLY_AUDIO"]:
                    id = str(uuid4()) + ".mp3"
                    sub["filename"] = os.path.join(settings["DATA_DIR"], id)
                    f_obj = executor.submit(cut_audio, sub, settings, media_file)
                else:
                    # Case: Audio + srt file
                    _, ext = os.path.splitext(media_file)
                    if ext == ".mp3":
                        id = str(uuid4()) + ".mp3"
                    else:
                        id = str(uuid4()) + ".mp4"
                    sub["filename"] = os.path.join(settings["DATA_DIR"], id)
                    f_obj = executor.submit(cut_video, sub, settings, media_file)
                
                save[f_obj] = (idx, sub)
                tasks.append(f_obj)
                idx += 1
        for res in futures.as_completed(tasks):
            result = res.result()
            opt = save[res]
            if settings["SHOW_LOG"]:
                print(opt[0], opt[1]["text"])


def finder(phrases, values, i, ratio):
    no_dulp = []
    counter = 0
    for sub in values["subtitles"]:
        found = False
        for phrase in phrases:
            r = fuzz.token_sort_ratio(sub["text"], phrase)
            if r >= ratio:
                found = True
                counter += 1
                break
        if not found:
            no_dulp.append(sub)
    values["subtitles"] = no_dulp
    return values, i, counter
