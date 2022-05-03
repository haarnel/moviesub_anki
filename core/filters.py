import re
import sys

AUTHOR_STRING = [
    "synced and corrected by",
    "please rate this subtitle",
    "encoded by",
    "subtitles by",
    "opensubtitles.org",
]

MUSIC_ICONS = ["#", "♪"]
HTML_TAGS = re.compile(r"<.*?>")

_SELECTED_FILTERS = None


def remove_author_string(sub: str) -> str:
    for str in AUTHOR_STRING:
        if str in sub.lower():
            return ""
    return sub


def remove_music(sub: str) -> str:
    splitted_sub = {idx: ch for idx, ch in enumerate(sub, 0)}
    idx = 0
    for c in sub:
        if c in MUSIC_ICONS:
            del splitted_sub[idx]
        idx += 1
    joined_sub = "".join(c for c in splitted_sub.values())
    if joined_sub:
        return joined_sub.strip()
    return ""


def remove_html_tags(sub: str) -> str:
    return HTML_TAGS.sub("", sub)


def remove_dots(sub: str) -> str:
    return sub.replace("...", "").replace("-", "").strip()


def apply_filters(sub, filters):
    global _SELECTED_FILTERS
    if not _SELECTED_FILTERS:
        module = sys.modules[__name__]
        _SELECTED_FILTERS = [getattr(module, filter) for filter in filters]

    sub_text = sub.text
    for filter in _SELECTED_FILTERS:
        sub_text = filter(sub_text)

    if sub_text:
        sub.text = sub_text

    return sub
