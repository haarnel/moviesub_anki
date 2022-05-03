

Convert video (movie, youtube video and etc) files with subtitles into [Anki](https://apps.ankiweb.net/) deck. For now, it only works with subtitles in SubRip format.

Demo: [Watch](https://player.vimeo.com/video/559606758)

### Requirements

- Python3
- FFmpeg

### Installation

```shell
# Установка
git clone https://github.com/haarnel/moviesub_anki
cd moviesub_anki
pip install -r requirements.txt
```

### Usage

```shell
python app.py -v <video.mkv> -s <subtitles.srt> -d <deck_name>
# щк when you have a folder with video files (tv show and so on). Folder structure: (video1.mkv -> video1.srt, video2.mkv -> video2.srt)
python app.py -m <path_to_directory> -d <deck_name>
```
