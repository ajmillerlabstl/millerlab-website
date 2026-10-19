"""
utility functions for cite process and plugins
"""

import re
import subprocess
import json
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from datetime import date, datetime
from rich import print
from diskcache import Cache


# cache for time-consuming network requests
cache = Cache("./_cite/.cache")


# clear expired items from cache
cache.expire()


def log_cache(func):
    """
    decorator to use around memoized function to log if cached or or not
    """

    def wrap(*args):
        key = func.__cache_key__(*args)
        if key in cache:
            log(" (from cache)", level="INFO", newline=False)
        return func(*args)

    return wrap


def log(message="\n--------------------\n", indent=0, level="", newline=True):
    """
    log to terminal, color determined by indent and level
    """

    colors = {
        0: "[orange1]",
        1: "[salmon1]",
        2: "[violet]",
        3: "[sky_blue1]",
        "ERROR": "[#F43F5E]",
        "WARNING": "[#EAB308]",
        "SUCCESS": "[#10B981]",
        "INFO": "[grey70]",
    }
    prefixes = {
        "ERROR": "🚫 ERROR: ",
        "WARNING": "⚠️ WARNING: ",
    }
    color = get_safe(colors, level, "") or get_safe(colors, indent, "") or "[white]"
    prefix = get_safe(prefixes, level, "")
    if newline:
        print()
    print(indent * "    " + color + prefix + str(message) + "[/]", end="", flush=True)


def label(entry):
    """
    get "label" of dict entry (for logging purposes)
    """

    return str(list(entry.keys())[0]) + ": " + str(list(entry.values())[0])


def get_safe(item, path, default=None):
    """
    safely access value in nested lists/dicts
    """

    for part in str(path).split("."):
        try:
            part = int(part)
        except ValueError:
            part = part
        try:
            item = item[part]
        except (KeyError, IndexError, AttributeError, TypeError):
            return default
    return item


def index_of(_list, value, fallback=float("inf")):
    """
    index of, with fallback
    """

    try:
        return _list.index(value)
    except ValueError:
        return fallback


def list_of_dicts(data):
    """
    check if data is list of dicts
    """

    return isinstance(data, list) and all(isinstance(entry, dict) for entry in data)


def format_date(_date):
    """
    format date as YYYY-MM-DD, or no date if malformed
    """

    if isinstance(_date, int):
        return datetime.fromtimestamp(_date // 1000.0).strftime("%Y-%m-%d")
    if isinstance(_date, (date, datetime)):
        return _date.strftime("%Y-%m-%d")
    try:
        return datetime.strptime(_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return ""


def load_data(path):
    """
    read data from yaml or json file
    """

    # convert to path object
    path = Path(path)

    # check if file exists
    if not path.is_file():
        raise Exception("Can't find file")

    # try to open file
    try:
        file = open(path, encoding="utf8")
    except Exception as e:
        raise Exception(e or "Can't open file")

    # try to parse as yaml
    try:
        with file:
            data = yaml.load(file, Loader=SafeLoader)
    except Exception:
        raise Exception("Can't parse file. Make sure it's valid YAML.")

    # if no errors, return data
    return data


def save_data(path, data):
    """
    write data to yaml file
    """

    # convert to path object
    path = Path(path)

    # try to open file
    try:
        file = open(path, mode="w")
    except Exception:
        raise Exception("Can't open file for writing")

    # prevent yaml anchors/aliases (pointers)
    yaml.Dumper.ignore_aliases = lambda *args: True

    # try to save data as yaml
    try:
        with file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)
    except Exception:
        raise Exception("Can't save YAML to file")

    # write warning note to top of file
    note = "# DO NOT EDIT, GENERATED AUTOMATICALLY"
    try:
        with open(path, "r") as file:
            data = file.read()
        with open(path, "w") as file:
            file.write(f"{note}\n\n{data}")
    except Exception:
        raise Exception("Can't write to file")


PREPRINT_PREFIXES = ("doi:10.1101/", "doi:10.64898/", "doi:10.21203/", "doi:10.31219/", "doi:10.20944/")


def clean_citations(citations):
    """
    drop citations with no title (e.g. orcid works that only point to a journal),
    and hide duplicates: the same doi in different letter case, or a preprint
    whose published version is also in the list. returns (kept, dropped).
    """

    def is_preprint(citation):
        return str(get_safe(citation, "id", "")).lower().startswith(PREPRINT_PREFIXES)

    def title_key(citation):
        title = re.sub(r"<[^>]+>", "", str(get_safe(citation, "title", ""))).lower()
        # start of title only, since journals often tweak the end of a preprint's title
        return re.sub(r"[^a-z0-9]", "", title)[:80]

    kept, dropped, seen_ids = [], [], set()
    for citation in citations:
        _id = str(get_safe(citation, "id", "")).lower()
        if not str(get_safe(citation, "title", "")).strip() or (_id and _id in seen_ids):
            dropped.append(citation)
            continue
        seen_ids.add(_id)
        kept.append(citation)

    published = {title_key(c) for c in kept if not is_preprint(c)}
    final = []
    for citation in kept:
        if is_preprint(citation) and title_key(citation) in published:
            dropped.append(citation)
        else:
            final.append(citation)

    return final, dropped


def label_sources(path, citations):
    """
    give each entry in a hand-edited sources file a readable "note" (year, first
    author, title) so people can see what each id is, sort the entries newest
    first, and strip invisible characters pasted into ids. keeps the comment
    header at the top of the file. the note is never shown on the site.
    """

    path = Path(path)
    text = path.read_text(encoding="utf8")
    header = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            header.append(line)
        else:
            break

    entries = yaml.load(text, Loader=SafeLoader) or []
    lookup = {get_safe(c, "id", ""): c for c in citations}

    for entry in entries:
        _id = str(get_safe(entry, "id", ""))
        clean = "".join(ch for ch in _id if ch.isprintable() and ch not in "​‌‍﻿").strip()
        if clean != _id:
            entry["id"] = clean
        if get_safe(entry, "note", ""):
            continue
        citation = lookup.get(_id) or lookup.get(clean) or {}
        year = str(get_safe(citation, "date", ""))[:4]
        authors = get_safe(citation, "authors", [])
        author = authors[0] + (" et al." if len(authors) > 1 else "") if authors else ""
        title = " ".join(str(get_safe(citation, "title", "")).split())
        parts = [part for part in [year, author, title] if part]
        if parts:
            entry["note"] = " · ".join(parts)

    def newest(entry):
        citation = lookup.get(get_safe(entry, "id", "")) or {}
        return str(get_safe(citation, "date", "")) or "0"

    entries.sort(key=newest, reverse=True)

    body = yaml.dump(entries, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)
    new = "\n".join(header).rstrip() + "\n\n" + body
    if new != text:
        path.write_text(new, encoding="utf8")


@log_cache
@cache.memoize(name="manubot", expire=90 * (60 * 60 * 24))
def cite_with_manubot(_id):
    """
    generate citation data for source id with Manubot
    """

    # run manubot
    try:
        commands = ["manubot", "cite", _id, "--log-level=WARNING"]
        output = subprocess.Popen(commands, stdout=subprocess.PIPE).communicate()
    except Exception as e:
        log(e, indent=3)
        raise Exception("Manubot could not generate citation")

    # parse results as json
    try:
        manubot = json.loads(output[0])[0]
    except Exception:
        raise Exception("Couldn't parse Manubot response")

    # new citation with only needed info
    citation = {}

    # original id
    citation["id"] = _id

    # title
    citation["title"] = get_safe(manubot, "title", "").strip()

    # authors
    citation["authors"] = []
    for author in get_safe(manubot, "author", {}):
        given = get_safe(author, "given", "").strip()
        family = get_safe(author, "family", "").strip()
        if given or family:
            citation["authors"].append(" ".join([given, family]))

    # publisher
    container = get_safe(manubot, "container-title", "").strip()
    collection = get_safe(manubot, "collection-title", "").strip()
    publisher = get_safe(manubot, "publisher", "").strip()
    citation["publisher"] = container or publisher or collection or ""

    # extract date part
    def date_part(citation, index):
        try:
            return citation["issued"]["date-parts"][0][index]
        except (KeyError, IndexError, TypeError):
            return ""

    # date
    year = date_part(manubot, 0)
    if year:
        # fallbacks for month and day
        month = date_part(manubot, 1) or "1"
        day = date_part(manubot, 2) or "1"
        citation["date"] = format_date(f"{year}-{month}-{day}")
    else:
        # if no year, consider date missing data
        citation["date"] = ""

    # link
    citation["link"] = get_safe(manubot, "URL", "").strip()

    # return citation data
    return citation
