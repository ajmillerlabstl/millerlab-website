"""
cite process to convert sources and metasources into full citations
"""

import traceback
from importlib import import_module
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from util import *


# load environment variables
load_dotenv()


# save errors/warnings for reporting at end
errors = []
warnings = []

# output citations file
output_file = "_data/citations.yaml"


log()

log("Compiling sources")

# compiled list of sources
sources = []

# in-order list of plugins to run
plugins = ["google-scholar", "pubmed", "orcid", "sources"]

# loop through plugins
for plugin in plugins:
    # convert into path object
    plugin = Path(f"plugins/{plugin}.py")

    log(f"Running {plugin.stem} plugin")

    # get all data files to process with current plugin
    files = Path.cwd().glob(f"_data/{plugin.stem}*.*")
    files = list(filter(lambda p: p.suffix in [".yaml", ".yml", ".json"], files))

    log(f"Found {len(files)} {plugin.stem}* data file(s)", indent=1)

    # loop through data files
    for file in files:
        log(f"Processing data file {file.name}", indent=1)

        # load data from file
        try:
            data = load_data(file)
            # check if file in correct format
            if not list_of_dicts(data):
                raise Exception(f"{file.name} data file not a list of dicts")
        except Exception as e:
            log(e, indent=2, level="ERROR")
            errors.append(e)
            continue

        # loop through data entries
        for index, entry in enumerate(data):
            log(f"Processing entry {index + 1} of {len(data)}, {label(entry)}", level=2)

            # run plugin on data entry to expand into multiple sources
            try:
                expanded = import_module(f"plugins.{plugin.stem}").main(entry)
                # check that plugin returned correct format
                if not list_of_dicts(expanded):
                    raise Exception(f"{plugin.stem} plugin didn't return list of dicts")
            # catch any plugin error
            except Exception as e:
                # log detailed pre-formatted/colored trace
                print(traceback.format_exc())
                # log high-level error
                log(e, indent=3, level="ERROR")
                errors.append(e)
                continue

            # loop through sources
            for source in expanded:
                if plugin.stem != "sources":
                    log(label(source), level=3)

                # include meta info about source
                source["plugin"] = plugin.name
                source["file"] = file.name

                # add source to compiled list
                sources.append(source)

            if plugin.stem != "sources":
                log(f"{len(expanded)} source(s)", indent=3)


log("Merging sources by id")

# merge sources with matching (non-blank) ids
for a in range(0, len(sources)):
    a_id = get_safe(sources, f"{a}.id", "")
    if not a_id:
        continue
    for b in range(a + 1, len(sources)):
        b_id = get_safe(sources, f"{b}.id", "")
        if b_id == a_id:
            log(f"Found duplicate {b_id}", indent=2)
            sources[a].update(sources[b])
            sources[b] = {}
sources = [entry for entry in sources if entry]


log(f"{len(sources)} total source(s) to cite")


log()

log("Generating citations")

# list of new citations
citations = []

# load existing citations to preserve manual enrichments (abstracts, tags, images, etc.)
existing_citations = {}
try:
    if Path(output_file).exists():
        for c in load_data(output_file) or []:
            cid = get_safe(c, "id", "").strip()
            if cid:
                existing_citations[cid.lower()] = c
except Exception as e:
    log(f"Note: Could not preload existing citations: {e}", level="WARNING")


# loop through compiled sources
for index, source in enumerate(sources):
    log(f"Processing source {index + 1} of {len(sources)}, {label(source)}")

    # if explicitly flagged, remove/ignore entry
    if get_safe(source, "remove", False) == True:
        continue

    # new citation data for source
    citation = {}

    # source id
    _id = get_safe(source, "id", "").strip()

    # papers already on the site are kept exactly as they are; only new ids are looked up
    # (fields people edit in sources.yaml always come fresh from there, so removing a tag or link works)
    existing = existing_citations.get(_id.lower())
    if existing:
        citation = {
            key: value
            for key, value in existing.items()
            if key not in ["tags", "buttons", "description", "image", "repo", "note"]
        }

        # fill in an abstract the publisher has sent to crossref since the paper was added
        # (recent papers only: older ones won't gain one, and each lookup slows the build)
        recent = str(get_safe(citation, "date", "")) >= str(date.today().replace(year=date.today().year - 1))
        if recent and not get_safe(citation, "abstract", "") and not get_safe(source, "abstract", ""):
            try:
                abstract = get_safe(cite_with_manubot(_id), "abstract", "")
                if abstract:
                    citation["abstract"] = abstract
            except Exception:
                pass

    # manubot doesn't work without an id
    elif _id:
        log("Using Manubot to generate citation", indent=1)

        try:
            # run manubot and set citation
            citation = cite_with_manubot(_id)

        # if manubot cannot cite source
        except Exception as e:
            plugin = get_safe(source, "plugin", "")
            file = get_safe(source, "file", "")
            # if regular source (id entered by user), throw error
            if plugin == "sources.py":
                log(e, indent=3, level="ERROR")
                errors.append(f"Manubot could not generate citation for source {_id}")
            # otherwise, if from metasource (id retrieved from some third-party api), just warn
            else:
                log(e, indent=3, level="WARNING")
                warnings.append(
                    f"Manubot could not generate citation for source {_id} (from {file} with {plugin})"
                )
                # discard source from citations
                continue

    # bioRxiv preprints now list the nonprofit that runs bioRxiv as their publisher
    if get_safe(citation, "publisher", "") == "openRxiv":
        citation["publisher"] = "bioRxiv"

    # preserve fields from input source, overriding existing fields
    # (blank fields saved by the Pages CMS form, like an empty abstract, don't wipe real ones)
    citation.update({key: value for key, value in source.items() if value not in ["", None]})

    # ensure date in proper format for correct date sorting
    if get_safe(citation, "date", ""):
        citation["date"] = format_date(get_safe(citation, "date", ""))

    # add new citation to list
    citations.append(citation)


log()

log("Removing blank and duplicate citations")

citations, dropped = clean_citations(citations)
for citation in dropped:
    log(f"Hid {get_safe(citation, 'id', '')} {get_safe(citation, 'title', '(no title)')[:60]}", indent=1)

log()

log("Saving updated citations")


# save new citations
try:
    save_data(output_file, citations)
except Exception as e:
    log(e, level="ERROR")
    errors.append(e)

# label hand-entered sources so the list is readable
try:
    label_sources("_data/sources.yaml", citations)
except Exception as e:
    log(e, level="WARNING")
    warnings.append(e)


log()


# exit at end, so user can see all errors/warnings in one run
if len(warnings):
    log(f"{len(warnings)} warning(s) occurred above", level="WARNING")
    for warning in warnings:
        log(warning, indent=1, level="WARNING")

if len(errors):
    log(f"{len(errors)} error(s) occurred above", level="ERROR")
    for error in errors:
        log(error, indent=1, level="ERROR")
    log()
    exit(1)

else:
    log("All done!", level="SUCCESS")

log()
