"""Convert the Miller Lab Weebly archive into Greene Lab Lab Website Template content."""
import re, os, shutil, csv, html as htmllib
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify
from PIL import Image

SRC = Path("/home/claude/site/5850639176ad6387f1d1df")
OUT = Path("/home/claude/millerlab-site")
REPORT = []          # lines for MIGRATION_NOTES.md
MEMBER_ROWS = []     # rows for members-review.csv

JUNK = "\u200b\ufeff"


def clean(t):
    t = t.translate({ord(c): None for c in JUNK}).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", t).strip()


def soup(name):
    return BeautifulSoup(open(SRC / name, encoding="utf-8", errors="ignore"), "html.parser")


def slugify(t, n=60):
    t = re.sub(r"\(.*?\)", "", t.lower())
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:n].strip("-") or "item"


# ---------- images ----------
_copied = {}
BLOG_SLUGS = {}   # old weebly blog slug -> new post url
OLD_PAGES = {"index.html": "/", "people.html": "team", "research.html": "research", "publications.html": "publications",
             "teaching.html": "teaching", "outreach.html": "outreach", "join-us.html": "join-us", "media.html": "media",
             "photos.html": "photos", "news.html": "blog", "lab-blog.html": "blog"}


def copy_image(src, subdir, name=None, max_px=1600):
    """Copy (and downsize) a Weebly image; return site-relative path or None."""
    if not src or src.startswith(("http", "data:", "//")):
        return src
    rel = src.split("?")[0].lstrip("/")
    # prefer the full-size _orig version when it exists
    p = SRC / rel
    orig = p.with_name(p.stem + "_orig" + p.suffix)
    if orig.exists():
        p = orig
    if not p.exists():
        root = SRC / "uploads/1/8/6/5/18659450"
        stem = Path(rel).stem
        cands = sorted(root.glob(stem + "_orig.*")) + sorted(root.glob(stem + ".*"))
        if cands:
            p = cands[0]
    if not p.exists():
        REPORT.append(f"- Missing image referenced on old site: `{rel}`")
        return None
    key = (str(p), subdir, name)
    if key in _copied:
        return _copied[key]
    stem = slugify(name) if name else slugify(p.stem.replace("_orig", ""), 50)
    dest_dir = OUT / "images" / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        im = Image.open(p)
        im.thumbnail((max_px, max_px))
        if im.mode in ("RGBA", "LA", "P") and p.suffix.lower() == ".png":
            dest = dest_dir / f"{stem}.png"
            im.save(dest, optimize=True)
        else:
            dest = dest_dir / f"{stem}.jpg"
            im.convert("RGB").save(dest, quality=85, optimize=True)
    except Exception:
        dest = dest_dir / (stem + p.suffix.lower())
        shutil.copy(p, dest)
    i = 2
    out = f"images/{subdir}/{dest.name}"
    _copied[key] = out
    return out


# ---------- html -> markdown ----------
def to_md(node, img_dir):
    node = BeautifulSoup(str(node), "html.parser")
    for tag in node.find_all(["script", "style", "noscript", "iframe"]):
        if tag.name == "iframe" and tag.get("src"):
            tag.replace_with(f"\n\n[Embedded content]({tag['src']})\n\n")
        else:
            tag.decompose()
    for img in node.find_all("img"):
        new = copy_image(img.get("src"), img_dir)
        if new:
            img["src"] = new
            img["alt"] = clean(img.get("alt", "")) if img.get("alt", "") != "Picture" else ""
        else:
            img.decompose()
    # Weebly multi-column layouts are tables; flatten them so content flows top to bottom
    for t in node.find_all(["table", "tbody", "tr", "td", "th"]):
        t.name = "div"
    for img in node.find_all("img"):
        if img.parent and img.parent.name != "p":
            wrapper = node.new_tag("p"); img.wrap(wrapper)
    for box in node.select(".wsite-image"):
        for d in box.find_all("div", recursive=False):
            if d.get_text(strip=True):
                d["class"] = d.get("class", []) + ["wsite-caption"]
    for cap in node.select(".wsite-caption"):
        txt = clean(cap.get_text(" "))
        if txt:
            new_p = node.new_tag("p"); em = node.new_tag("em"); em.string = txt; new_p.append(em)
            cap.replace_with(new_p)
        else:
            cap.decompose()
    for h in node.select(".wsite-content-title"):
        h.name = "h2"
    for a in node.find_all("a"):
        href = a.get("href", "")
        if href.startswith("http://UNSET"):
            href = href.replace("http://UNSET", "").lstrip("/")
        if href.startswith(("uploads/", "/uploads/")):
            low = href.split("?")[0].lower()
            if low.endswith((".jpg", ".jpeg", ".png", ".gif")):
                inner = a.find("img")
                if inner is not None:          # gallery thumbnail: drop the link, keep the image + caption
                    a.insert_before(node.new_tag("br")); a.unwrap(); continue
                href = copy_image(href, img_dir) or href
            else:
                fdest = OUT / "files" / Path(href.split("?")[0]).name
                src_f = SRC / href.split("?")[0].lstrip("/")
                if src_f.exists():
                    fdest.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src_f, fdest)
                    href = "files/" + fdest.name
        m = re.match(r"(?:lab-blog/)?([a-z0-9-]+?)(?:\.html)?$", href)
        if m and m.group(1) in BLOG_SLUGS:
            href = BLOG_SLUGS[m.group(1)]
        elif href.split("#")[0] in OLD_PAGES:
            href = OLD_PAGES[href.split("#")[0]]
        if href:
            a["href"] = href
        if not a.get_text(strip=True) and not a.find("img"):
            a.unwrap()
    md = markdownify(str(node), heading_style="ATX", strip=["font", "span", "div", "u"])
    md = clean_md(md)
    # site-internal links/images must go through relative_url so they work from any page depth
    internal = "|".join(["images/", "files/"] + [re.escape(v) for v in OLD_PAGES.values() if v != "/"])
    md = re.sub(rf"\]\(((?:{internal})[^)\s]*)", lambda m: "]({{ '" + m.group(1) + "' | relative_url }}", md)
    return md


def clean_md(md):
    md = md.translate({ord(c): None for c in JUNK}).replace("\xa0", " ")
    md = re.sub(r"Click to set custom HTML", "", md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\*\*\s*\*\*", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def write(path, text):
    path = OUT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def content(name):
    return soup(name).select_one("#wsite-content")


# ---------- members ----------
ROLE_RULES = [
    (r"junior research", "honorary"),
    (r"principal investigator", "principal-investigator"),
    (r"post-?doc", "postdoc"),
    (r"research scientist|research associate", "research-scientist"),
    (r"grant specialist|admin|manager(?!.*lab)", "staff"),
    (r"lab manager|technician|research assistant|lab assistant|laboratory", "technician"),
    (r"phd|ph\.d", "phd"),
    (r"\bms\b|m\.s\.|master", "masters"),
    (r"high school|stars student|collegiate", "high-school"),
    (r"undergrad|reu|intern|visiting", "undergrad"),
    (r"junior research", "honorary"),
]


def guess_role(text, section):
    t = text.lower()
    sec = section.lower()
    if "grant specialist" in t:
        return "staff"
    if "high school" in sec:
        return "high-school"
    if "graduate student" in sec and "under" not in sec and "phd" not in t:
        if re.search(r"\bms\b|m\.s\.", t):
            return "masters"
    for pat, role in ROLE_RULES:
        if re.search(pat, t):
            return role
    if "undergrad" in sec:
        return "undergrad"
    if "post" in sec:
        return "postdoc"
    return "undergrad" if "hall of fame" in sec else "staff"


def header_of(p):
    """Text before the first double line break (the bold name/role line)."""
    parts = []
    for el in p.descendants:
        if isinstance(el, Tag) and el.name == "br":
            if clean("".join(parts)):
                break
        elif isinstance(el, NavigableString):
            parts.append(str(el))
    return clean("".join(parts))


def split_header(h):
    pron = re.search(r"\((she|he|they)[^)]*\)", h)
    pronouns = pron.group(0).strip("()") if pron else ""
    h2 = h.replace(pron.group(0), "") if pron else h
    name = re.sub(r"\s*\(.*?\)", "", re.split(r",", h2)[0]).strip(" .;")
    rest = h2[len(re.split(r",", h2)[0]):].strip(" ,.;")
    rest = re.sub(r"^Ph\.?D\.\s*", "", rest)
    return name, pronouns, rest


def members():
    s = soup("people.html")
    c = s.select_one("#wsite-content")
    titles_and_ps = c.find_all(
        lambda t: (t.has_attr("class") and ("paragraph" in t["class"] or "wsite-content-title" in t["class"]))
        or (t.name == "h2" and not t.has_attr("class")))
    pending = None
    section, alum = "Current", False
    people, extra_alumni = [], []
    group_photo = None
    gp = c.find("img")
    if gp:
        group_photo = copy_image(gp.get("src"), "team", "miller-lab-group", 2000)
        cap = gp.find_parent("span").find(class_="wsite-caption") if gp.find_parent("span") else None
        group_caption = re.sub(r"\s+", " ", clean(cap.get_text(" "))) if cap else ""

    for el in titles_and_ps:
        txt = clean(el.get_text(" "))
        if el.name == "h2" and not el.has_attr("class"):
            pending = txt
            continue
        if pending and "paragraph" in el["class"]:
            st = el.find("strong")
            starts_bold = st is not None and clean(st.get_text(" "))[:10] == txt[:10]
            if not starts_bold:
                name, pron, role_txt = split_header(pending)
                pending = None
                people.append(dict(name=name, pronouns=pron, role_text=role_txt, section=section,
                                   alum=alum, bio=to_md(el, "team"), el=el, image=None))
                continue
        pending = None
        if "wsite-content-title" in el["class"]:
            if not txt:
                continue
            if "hall of fame" in txt.lower():
                alum = True
            if "," in txt and len(txt) > 60:   # a person's bio formatted as a title
                pass
            else:
                section = txt.split("Lab alums")[0].strip()
                continue
        if txt.startswith("The Miller Lab group is supported"):
            intro = to_md(el, "team")
            continue
        h = header_of(el)
        if not h:
            continue
        if re.match(r"(?i)update\s*:", h) and people:
            people[-1]["bio"] += "\n\n" + to_md(el, "team")
            continue
        if re.match(r"(?i)former|slu undergraduate researchers \(2006", h) and len(h) < 70:
            section = h
            alum = True
            rest = el.get_text(" ", strip=True)[len(h):].strip()
            if len(rest) > 40:
                extra_alumni.append(to_md(el, "team"))
            continue
        is_pi = h.lower().startswith("contact information") or txt.startswith("Allison is a Professor")
        if not is_pi and (" and " in h.split(",")[0] and "Henry" not in h or ";" in h.split(",")[0]):
            extra_alumni.append(to_md(el, "team"))
            continue
        if is_pi:
            name, pron, role_txt = "Allison Miller", "she/her", "Lab Principal Investigator (2006 - present)"
            bio_html = el
        else:
            name, pron, role_txt = split_header(h)
            bio_html = BeautifulSoup(str(el), "html.parser")
            # drop the header portion
            first = bio_html.find("strong")
            if first and clean(first.get_text(" ")) and clean(first.get_text(" "))[:15] == h[:15]:
                first.decompose()
        bio = to_md(bio_html, "team")
        bio = re.sub(r"^(\s*\n)+", "", bio)
        people.append(dict(name=name, pronouns=pron, role_text=role_txt, section=section,
                           alum=alum, bio=bio, el=el, image=None))

    # assign photos: inside a multi-column block the photo shares the block with its paragraph;
    # elsewhere the photo sits immediately before the paragraph it belongs to.
    imgs = [i for i in c.find_all("img") if i is not gp]
    pmap = {id(p["el"]): p for p in people}
    for p in people:
        mc = p["el"].find_parent(class_="wsite-multicol")
        if mc:
            im = mc.find("img")
            if im is not None:
                p["image"] = im
    for img in imgs:
        if img.find_parent(class_="wsite-multicol"):
            continue
        nxt = img.find_next(class_="paragraph")
        if nxt is not None and id(nxt) in pmap and pmap[id(nxt)]["image"] is None \
                and not nxt.find_parent(class_="wsite-multicol"):
            pmap[id(nxt)]["image"] = img

    seen = {}
    for p in people:
        slug = slugify(p["name"])
        if slug in seen:
            slug = f"{slug}-{seen[slug]}"
        seen[slug] = seen.get(slug, 1) + 1
        if "grant specialist" in p["role_text"].lower():   # listed under 'Admins' on the old site
            p["alum"] = False
        if p["alum"] and "present" in p["role_text"].lower():
            p["flag"] = "says 'present' but was listed under alumni on the old site"
        role = "principal-investigator" if p["name"] == "Allison Miller" else guess_role(p["role_text"], p["section"])
        img = copy_image(p["image"].get("src"), "team", slug, 700) if p["image"] else None
        desc = p["role_text"]
        fm = ["---", f'name: "{p["name"]}"']
        fm.append(f"image: {img}" if img else "image: images/photo.jpg")
        fm.append(f"role: {role}")
        if desc:
            fm.append(f'description: "{desc.replace(chr(34), chr(39))}"')
        if p["pronouns"]:
            fm.append(f"pronouns: {p['pronouns']}")
        if p["alum"]:
            fm.append("group: alum")
        if role == "principal-investigator":
            fm += ["aliases:", "  - A. J. Miller", "  - A. Miller", "  - Allison J. Miller",
                   "links:", "  email: amiller@danforthcenter.org",
                   "  home-page: https://www.danforthcenter.org/"]
        fm.append("---")
        bio = p["bio"]
        if p["pronouns"]:
            bio = f"*Pronouns: {p['pronouns']}*\n\n" + bio
        write(f"_members/{slug}.md", "\n".join(fm) + "\n\n" + bio)
        MEMBER_ROWS.append([slug, p["name"], role, "alum" if p["alum"] else "current",
                            p["section"], desc, "yes" if img else "NO PHOTO", p.get("flag", "")])

    # team page
    team = f"""---
title: Team
nav:
  order: 2
  tooltip: About our team
redirect_from: /people.html
---

# {{% include icon.html icon="fa-solid fa-users" %}}Team

{{% include figure.html image="{group_photo}" caption="{group_caption.replace(chr(34), chr(39))}" width="100%" %}}

{intro}
{{% include section.html %}}

## Current lab members

{{% include list.html data="members" component="portrait" filter="role == 'principal-investigator' and group != 'alum'" %}}
{{% include list.html data="members" component="portrait" filter="role != 'principal-investigator' and group != 'alum'" %}}

{{% include section.html %}}

## Miller Lab Hall of Fame

Lab alums: do you have updates to share? Please email amiller@danforthcenter.org.

{{% include list.html data="members" component="portrait" filter="group == 'alum'" style="small" %}}

### More lab alumni

{chr(10).join("- " + l.strip() for blk in extra_alumni for l in blk.splitlines() if l.strip())}
"""
    write("team/index.md", team)
    REPORT.append(f"- Converted **{len(people)} people** into `_members/` "
                  f"({sum(not p['alum'] for p in people)} current, {sum(p['alum'] for p in people)} alumni). "
                  f"Group-only entries (e.g. the 2006–2012 undergrad list) went into a 'More lab alumni' section on the Team page.")


# ---------- blog + news ----------
def posts():
    s = soup("lab-blog.html")
    n = 0
    for post in s.select(".blog-post"):
        title = clean(post.select_one(".blog-title").get_text(" "))
        m, d, y = clean(post.select_one(".date-text").get_text()).split("/")
        old_slug = post.select_one(".blog-title a")["href"].rstrip("/").split("/")[-1]
        BLOG_SLUGS[old_slug] = f"{{% post_url {y}-{int(m):02d}-{int(d):02d}-{slugify(title, 50)} %}}"
    for post in s.select(".blog-post"):
        title = clean(post.select_one(".blog-title").get_text(" "))
        m, d, y = clean(post.select_one(".date-text").get_text()).split("/")
        date = f"{y}-{int(m):02d}-{int(d):02d}"
        body = to_md(post.select_one(".blog-content"), "blog")
        img = re.search(r"\]\((images/blog/[^)]+)\)", body)
        fm = f'---\ntitle: "{title.replace(chr(34), chr(39))}"\nauthor: allison-miller\ntags: lab blog\n'
        if img:
            fm += f"image: {img.group(1)}\n"
        fm += "---\n\n"
        write(f"_posts/{date}-{slugify(title, 50)}.md", fm + body)
        n += 1
    REPORT.append(f"- Converted **{n} lab blog posts** (2017–2018). The Weebly archive only contains the first page of the blog; "
                  "older posts (2013–2016) were on paginated pages not included in the export — see 'To do' below.")

    # news page: "Month YYYY:" items
    c = content("news.html")
    text_md = to_md(c, "news")
    months = "January|February|March|April|May|June|July|August|September|October|November|December"
    text_md = re.sub(r"(?m)^\s*[*-]\s+", "", text_md)
    items = re.split(rf"\n(?=\**\s*(?:{months})\s+\d{{4}}\s*:)", "\n" + text_md)
    k = 0
    for it in items:
        mm = re.match(rf"\**\s*({months})\s+(\d{{4}})\s*:\s*\**\s*(.*)", it.strip(), re.S)
        if not mm:
            continue
        mon = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"].index(mm.group(1)) + 1
        body = mm.group(3).strip().strip("*").strip()
        if not body:
            continue
        first = re.sub(r"[*_\[\]()]|https?://\S+", "", body.split("\n")[0])
        title = first[:70].rsplit(" ", 1)[0] if len(first) > 70 else first
        k += 1
        date = f"{mm.group(2)}-{mon:02d}-{(k % 27) + 1:02d}"
        write(f"_posts/{date}-news-{slugify(title, 40)}.md",
              f'---\ntitle: "{title.strip().replace(chr(34), chr(39))}"\ntags: news\n---\n\n{body}\n')
    REPORT.append(f"- Converted **{k} items from the old News page** into short dated posts tagged `news` "
                  "(Weebly only gave month and year, so the day of the month is a placeholder).")


# ---------- publications ----------
def publications():
    c = content("publications.html")
    text = c.get_text(" ")
    dois = []
    found = re.findall(r"10\.\d{4,9}/[^\s<>\"']+", text)
    for a in c.find_all("a"):
        found += re.findall(r"10\.\d{4,9}/[^\s<>\"']+", a.get("href", ""))
    for d in found:
        d = re.split(r";jsessionid|\?", d)[0].rstrip(".,;)")
        d = re.sub(r"/(abstract|full|pdf)$", "", d)
        if d.startswith("10.1101/"):
            d = re.sub(r"v\d+$", "", d)          # bioRxiv version suffix is not part of the DOI
        if d.lower() not in [x.lower() for x in dois]:
            dois.append(d)
    yaml = ["# Publications are cited automatically from these DOIs when the site builds.",
            "# To add a paper: add a line like  - id: doi:10.1002/ajb2.70198",
            "# Tip: also add Allison's ORCID to _data/orcid.yaml so new papers appear on their own.", ""]
    yaml += [f"- id: doi:{d}" for d in dois]
    write("_data/sources.yaml", "\n".join(yaml) + "\n")
    write("_data/orcid.yaml", "# Add the PI's ORCID here to pull in her full publication record automatically, e.g.\n"
                              "# - orcid: 0000-0000-0000-0000\n")
    # entries without DOIs -> preserved as text
    html = str(c)
    parts = re.split(r"(?:<br\s*/?>\s*){2,}|</div>", html)
    nodoi = []
    for part in parts:
        t = clean(BeautifulSoup(part, "html.parser").get_text(" "))
        if len(t) > 60 and not re.search(r"10\.\d{4,9}/", t) and re.search(r"(19|20)\d\d", t) \
                and "Google Scholar" not in t:
            nodoi.append(clean_md(markdownify(part, strip=["font", "span", "div", "a"])).strip())
    page = """---
title: Publications
nav:
  order: 3
  tooltip: Published works
redirect_from: /publications.html
---

# {% include icon.html icon="fa-solid fa-book" %}Publications

\\*graduate student; \\*\\*undergraduate student. See also [Allison's Google Scholar page](https://scholar.google.com/).

{% include section.html %}

{% include search-box.html %}

{% include search-info.html %}

{% include list.html data="citations" component="citation" style="rich" %}

{% include section.html %}

## Earlier publications

"""
    page += "\n\n".join(nodoi) + "\n"
    write("publications/index.md", page)
    REPORT.append(f"- Found **{len(dois)} DOIs** on the Publications page and put them in `_data/sources.yaml`, so those citations "
                  f"are generated automatically. **{len(nodoi)} older entries had no DOI**; their text is kept as-is under "
                  "'Earlier publications'.")


# ---------- simple pages ----------
PAGES = [
    ("research.html", "research/index.md", "Research", 1, "fa-solid fa-seedling", "Our research"),
    ("teaching.html", "teaching/index.md", "Teaching", 5, "fa-solid fa-chalkboard-user", "Courses"),
    ("outreach.html", "outreach/index.md", "Outreach", 6, "fa-solid fa-people-group", "Community engagement"),
    ("media.html", "media/index.md", "Media", 7, "fa-solid fa-newspaper", "In the news"),
    ("join-us.html", "join-us/index.md", "Join Us", 9, "fa-solid fa-envelope", "Open positions and contact"),
]


def pages():
    for src, dest, title, order, icon, tip in PAGES:
        md = to_md(content(src), slugify(title))
        md = re.sub(rf"^#+\s*{re.escape(title)}\s*\n", "", md, flags=re.I)
        write(dest, f"---\ntitle: {title}\nnav:\n  order: {order}\n  tooltip: {tip}\nredirect_from: /{src}\n---\n\n"
                    f"# {{% include icon.html icon=\"{icon}\" %}}{title}\n\n{md}")
    REPORT.append("- Converted the Research, Teaching, Outreach, Media and Join Us pages to Markdown with their images.")
    REPORT.append("- Skipped `peoplenew.html` and `join-us1.html` (Weebly placeholder/draft pages) and `botany-2019.html` "
                  "(a one-off 2019 announcement).")


def photos_page():
    c = content("photos.html")
    figs = []
    for img in c.find_all("img"):
        cap = ""
        box = img.find_parent(class_="wsite-image")
        holder = img.find_parent("span")
        if box is not None and box.find("div"):
            cap = box.find("div").get_text(" ")
        elif False:
            pass
        if cap:
            pass
        elif holder is not None and holder.find(class_="wsite-caption"):
            cap = holder.find(class_="wsite-caption").get_text(" ")
        elif img.find_parent("a") is not None and img.find_parent("a").get("title"):
            cap = img.find_parent("a")["title"]
        else:
            nxt = img.find_next(class_=["wsite-caption", "paragraph"])
            if nxt is not None and nxt.find_previous("img") is img:
                cap = nxt.get_text(" ")
        cap = re.sub(r"\s+", " ", clean(cap)).replace('"', "'")
        src = img.get("src")
        a = img.find_parent("a")
        if a is not None and a.get("href", "").startswith("uploads/"):
            src = a["href"]
        path = copy_image(src, "photos")
        if path:
            figs.append(f'{{% include figure.html image="{path}" caption="{cap}" %}}')
    write("photos/index.md", "---\ntitle: Photos\nnav:\n  order: 8\n  tooltip: Lab photos\n"
          "redirect_from: /photos.html\n---\n\n# {% include icon.html icon=\"fa-solid fa-camera\" %}Photos\n\n"
          "{% capture content %}\n\n" + "\n".join(figs) + "\n\n{% endcapture %}\n\n"
          "{% include grid.html style=\"square\" content=content %}\n")
    REPORT.append(f"- Rebuilt the Photos page as a photo grid ({len(figs)} photos with their captions).")


def home():
    c = content("index.html")
    contact = to_md(c, "home")
    write("index.md", f"""---
---

# Perennial Plant Diversity and Evolution

The Miller Lab studies perennial plant biology, diversity, and evolution — from crops and their wild relatives to
the root systems that help perennials thrive and survive. The lab is a joint partnership between the
[Donald Danforth Plant Science Center](https://www.danforthcenter.org/) and the
[Department of Biology at Saint Louis University](https://www.slu.edu/).

{{%
  include button.html
  link="research"
  text="Our research"
  icon="fa-solid fa-arrow-right"
  flip=true
%}}
{{%
  include button.html
  link="team"
  text="Meet the team"
  icon="fa-solid fa-arrow-right"
  flip=true
%}}

{{% include section.html %}}

## News

Lab news, announcements, and blog posts live on the [Blog](blog) page.

{{%
  include button.html
  link="blog"
  text="Read the latest news"
  icon="fa-solid fa-arrow-right"
  flip=true
%}}

{{% include section.html %}}

## Contact

{contact}""")


# ---------- driver ----------
NEW_TYPES = """
research-scientist:
  icon: fa-solid fa-flask
  description: Research Scientist

technician:
  icon: fa-solid fa-seedling
  description: Lab Technician

staff:
  icon: fa-solid fa-briefcase
  description: Staff

masters:
  icon: fa-solid fa-book-open
  description: MS Student

high-school:
  icon: fa-solid fa-school
  description: High School Intern

honorary:
  icon: fa-solid fa-star
  description: Honorary Lab Member
"""

PAGES_YML = """# Pages CMS configuration — gives lab members simple forms for editing the site.
# Sign in at https://app.pagescms.org with GitHub and open this repository.
media:
  input: images
  output: /images

content:
  - name: posts
    label: News & Blog
    type: collection
    path: _posts
    filename: "{year}-{month}-{day}-{primary}.md"
    view:
      fields: [title, date]
      sort: [date]
    fields:
      - { name: title, label: Title, type: string, required: true }
      - { name: author, label: Author (member file name, e.g. allison-miller), type: string }
      - { name: image, label: Image, type: image }
      - { name: tags, label: "Tags (e.g. news, lab blog)", type: string }
      - { name: body, label: Text, type: rich-text }

  - name: members
    label: Lab Members
    type: collection
    path: _members
    view:
      fields: [name, role, group]
    fields:
      - { name: name, label: Name, type: string, required: true }
      - { name: image, label: Photo, type: image }
      - name: role
        label: Role
        type: select
        options:
          values: [principal-investigator, research-scientist, postdoc, phd, masters, technician, staff, undergrad, high-school, honorary]
      - { name: description, label: "Title and years, e.g. Lab Technician (2025 - present)", type: string }
      - name: group
        label: Current member or alum?
        type: select
        options:
          values: ["", alum]
      - name: links
        label: Links
        type: object
        fields:
          - { name: email, label: Email, type: string }
          - { name: orcid, label: ORCID iD, type: string }
          - { name: google-scholar, label: Google Scholar ID, type: string }
          - { name: home-page, label: Personal website, type: string }
      - { name: body, label: Bio, type: rich-text }

  - name: publications
    label: Publications (DOI list)
    type: file
    path: _data/sources.yaml
    format: yaml-frontmatter
    list: true
    fields:
      - { name: id, label: "DOI, written as doi:10.xxxx/xxxxx", type: string }

  - name: pages
    label: Site Pages
    type: collection
    path: .
    subfolders: true
    filename: "{primary}/index.md"
    exclude: [_members, _posts, _includes, _layouts, _plugins, _styles, _scripts, _cite, _data, images, .github]
    fields:
      - { name: title, label: Title, type: string }
      - { name: body, label: Content, type: rich-text }
"""

if __name__ == "__main__":
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree("/home/claude/tmpl", OUT, ignore=shutil.ignore_patterns(".git"))
    for junk in ["_members", "_posts", "projects", "research", "contact", "testbed.md", "_data/projects.yaml"]:
        p = OUT / junk
        shutil.rmtree(p) if p.is_dir() else p.unlink(missing_ok=True)
    (OUT / "_members").mkdir(); (OUT / "_posts").mkdir()

    posts(); members(); publications(); pages(); photos_page(); home()

    # header image: lab group photo background from the old theme
    hdr = copy_image("uploads/1/8/6/5/18659450/background-images/background-images/1166867864.jpg", "site", "header", 2000)
    cfg = (OUT / "_config.yaml").read_text()
    cfg = cfg.replace("title: Lab Website Template", "title: Miller Lab")
    cfg = cfg.replace("subtitle: by the Greene Lab", "subtitle: Perennial Plant Diversity")
    cfg = re.sub(r"description: .*", "description: The Miller Lab at the Donald Danforth Plant Science Center and Saint Louis University studies perennial plant diversity and evolution.", cfg, 1)
    cfg = re.sub(r"header: .*", f"header: {hdr}", cfg, 1)
    cfg = re.sub(r"footer: .*", f"footer: {hdr}", cfg, 1)
    cfg = re.sub(r"links:\n(  .*\n)+", "links:\n  email: amiller@danforthcenter.org\n", cfg, 1)
    (OUT / "_config.yaml").write_text(cfg)
    with open(OUT / "_data/types.yaml", "a") as f:
        f.write("\n# Miller Lab roles\n" + NEW_TYPES)
    (OUT / "blog/index.md").write_text((OUT / "blog/index.md").read_text().replace(
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\nUt enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        "News, announcements, and stories from the Miller Lab.").replace("title: Blog", "title: Blog").replace("order: 4", "order: 4\n  tooltip: News and announcements").replace("  tooltip: Musings and miscellany\n", ""))
    (OUT / ".pages.yml").write_text(PAGES_YML)

    with open(OUT / "members-review.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "name", "role", "status", "old-site section", "title/years", "photo", "check"])
        w.writerows(MEMBER_ROWS)
    print("\n".join(REPORT))
