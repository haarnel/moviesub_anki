

Простой скрипт, который преобразует видео файлы с субтитрами в [Anki](https://apps.ankiweb.net/) колоду. Основное идея для применения - изучения иностранных языков. На данный момент, поддерживает только субтитры в формате SubRip.

### Требования

- Python3
- Установленный ffmpeg. Указать его через FFMPEG_BINARY, если его нет в PATH.

### Установка и запуск

```shell
# Установка
git clone https://github.com/haarnel/moviesub_anki
cd moviesub_anki
pip install -r requirements.txt

# Запуск
## 1. Вариант когда у нас один файл
python app.py -v <video.mkv> -s <subtitles.srt> -d <deck_name>

## 2. Когда есть большая папка (например, сериал) - все файлы в папке должны следовать формату: video1.mkv -> video1.srt, video2.mkv -> video2.srt.
python app.py -m <path_to_directory> -d <deck_name>
```

### Основные настройки

Стили для карточки переопределяются через data/style.css. В базе данных (data/database.db) храниться текст из субтитра и путь до файла. (если INCLUDE_MEDIA = False).

```ini
[SETTINGS]
; Путь до FFMPEG если его нету path
; FFMPEG_BINARY = /usr/bin/ffmpeg
; Где будут сохранятся видео фрагменты.
DATA_DIR = C:\Videos
; Где будет храниться файл с бд.
DB_DIR = D:\AnkiMovies\movies.db
; Сохранять видео фрагменты прямо в файл. (для экспорта)
; Создаёт много файлов во время работы в тек. директории.
; ! Удаляет их автоматически после окончания работы скрипта.
INCLUDE_MEDIA = False
; Извлекать только аудио из видео фрагмента.
EXTRACT_ONLY_AUDIO = True
; Ширина видео фрагмента
VIDEO_WIDTH = 640
; Высота видео фрагмента
VIDEO_HEIGHT = 360
; Управление битрейтом
BITRATE = 320
; Максимальное число одновременных процессов
MAX_WORKER_COUNT = 4
; Показать процесс работы
SHOW_LOG = True

[FILTERS]
; Минимальная длина субтитра в символах.
MIN_SUBTITLE_LENGTH = 45
; Максимальная длина субтитра в символах.
MAX_SUBTITLE_LENGTH = 300
; Минимальная длина субтитра в секундах.
MIN_SUBTITLE_DURATION = 2
; Максимальная длина субтитра в секундах.
MAX_SUBTITLE_DURATION = 10
; Количество добавляемое перед началом фрагмента (если отстают субтитры)
PAD_TIME_START = 0.5
; Количество добавляемое после конца фрагмента (если отстают субтитры)
PAD_TIME_END = 0.7
; Находить дубликаты в существующей бд (в data/database.db)
FIND_DUPLICATES = False
; Находить похожие фрагменты
FIND_SIMILAR = True
; Процент похожести
FIND_SIMILAR_RATIO = 70
; Если включить = то будут отбираться толко помеченные субтитры с $$$$ внутри.
; ONLY_MARKED_SUBS = $$$$

; Удаляют некоторый муср из текста (можно добавить свой в src/filters.py)
REMOVE_AUTHOR_STRING = True
REMOVE_MUSIC = True
REMOVE_HTML_TAGS = True
REMOVE_DOTS = True
```
