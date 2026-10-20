"""
Write a pull request comment linking each page changed on drafts to its
preview, highlighting the first changed words where possible.

usage: python preview_links.py <preview url> <pull request url>
run from a checkout of drafts with origin/main fetched
"""

import re
import subprocess
import sys
from urllib.parse import quote

preview, pr_url = sys.argv[1].rstrip("/"), sys.argv[2]

# data files shown on one page
DATA_PAGES = {
    "_data/gallery.yaml": ("Home page photo gallery", ""),
    "_data/projects.yaml": ("Research page", "research/"),
    "_data/team-sections.yaml": ("Team page", "team/"),
    "_data/sources.yaml": ("Publications page", "publications/"),
    "_data/citations.yaml": ("Publications page", "publications/"),
    "_data/orcid.yaml": ("Publications page", "publications/"),
}


def git(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def page(path):
    """Page title and preview path for a changed file, if it has one."""
    if path in DATA_PAGES:
        return DATA_PAGES[path]
    if match := re.fullmatch(r"_members/(.+)\.md", path):
        return (f"Member page: {match[1]}", f"members/{match[1]}.html")
    if match := re.fullmatch(r"_posts/(\d{4})-(\d\d)-(\d\d)-(.+)\.md", path):
        year, month, day, slug = match.groups()
        return (f"News post: {slug}", f"{year}/{month}/{day}/{slug}.html")
    if path == "index.md":
        return ("Home page", "")
    if match := re.fullmatch(r"(.+)/index\.md", path):
        return (f"{match[1].replace('-', ' ').title()} page", f"{match[1]}/")
    return None


def snippet(path):
    """First few new words in a markdown file, plus the words after them."""
    if not path.endswith(".md"):
        return None
    diff = git("diff", "-U1", "--word-diff=porcelain", "origin/main...HEAD", "--", path)
    lines = diff.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        text = line[1:]
        # add following unchanged words so short edits are still findable
        for after in lines[index + 1 : index + 3]:
            if after.startswith(" "):
                text += after
        # drop markdown and yaml syntax that doesn't show on the page
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"^\s*[\w-]+:\s*", "", text)
        text = re.sub(r"[*_`#>|\[\]]", "", text)
        words = text.split()[:6]
        if len(" ".join(words)) >= 8:
            return " ".join(words)
    return None


def fragment(text):
    # text fragment links need - , & encoded as well
    return "#:~:text=" + quote(text, safe="").replace("-", "%2D")


files = git("diff", "--name-only", "origin/main...HEAD").split()
pages, others = {}, []
for path in files:
    found = page(path)
    if not found:
        others.append(path)
        continue
    title, url = found
    link = f"{preview}/{url}"
    if words := snippet(path):
        link += fragment(words)
    pages.setdefault(title, link)

comment = ["### 📝 Pages changed in these drafts", ""]
if pages:
    comment.append(
        "Each link opens the preview of that page. The first changed words are "
        "highlighted where the browser can find them."
    )
    comment.append("")
    comment += [f"- [{title}]({link})" for title, link in pages.items()]
else:
    comment.append("No single page to point to; see the exact changes below.")
if others:
    comment += ["", "Other files changed (images, settings):", ""]
    comment += [f"- `{path}`" for path in others]
comment += ["", f"Exact before/after of every change: [Files changed]({pr_url}/files)"]

print("\n".join(comment))
