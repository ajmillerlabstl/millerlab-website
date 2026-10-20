Visit **[ajmillerlabstl.github.io/millerlab-website](https://ajmillerlabstl.github.io/millerlab-website)** 🚀

# Miller Lab website

The website of the Miller Lab, which studies perennial plant diversity and evolution at the
[Donald Danforth Plant Science Center](https://www.danforthcenter.org/) and the
[Department of Biology at Saint Louis University](https://www.slu.edu/arts-and-sciences/biology/).
It replaces the lab's old Weebly site, perennialplantdiversity.org.

The site is built with [Jekyll](https://jekyllrb.com/) on the
[Lab Website Template](https://github.com/greenelab/lab-website-template). Every change pushed to `main` is
rebuilt and published automatically by GitHub Actions.

- [Editing the site](#editing-the-site)
- [Where things live](#where-things-live)
- [Common tasks](#common-tasks)
- [Previewing changes on your computer](#previewing-changes-on-your-computer)
- [How publishing works](#how-publishing-works)
- [Changes from the template](#changes-from-the-template)
- [Credits and license](#credits-and-license)

## Editing the site

Most edits don't need any code. Use **[Pages CMS](https://app.pagescms.org)**:

1. Ask the repository owner to add you as a collaborator on this repository.
2. Sign in at [app.pagescms.org](https://app.pagescms.org) with your GitHub account and open `millerlab-website`.
3. Pick what to edit: **Lab Members**, **News & Blog**, **Publications**, or **Site Pages**. Upload photos right in the form.
4. Save. The live site updates in about two minutes.

For quick text fixes you can also edit a file on github.com (open it and click the pencil icon). For layout or
bulk changes, see [Previewing changes on your computer](#previewing-changes-on-your-computer).

## Where things live

| To change…              | Edit…                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------- |
| Lab members             | `_members/` — one file per person                                                      |
| Team page sections      | `_data/team-sections.yaml` — section names and order                                   |
| News and blog posts     | `_posts/` — one file per post, named `YYYY-MM-DD-short-title.md`                        |
| Publications            | `_data/sources.yaml` (DOIs) and `_data/orcid.yaml` (ORCID iDs)                         |
| Page text               | `index.md` (home), `research/`, `team/`, `publications/`, `teaching/`, `outreach/`, `media/`, `photos/`, `join-us/` |
| Site title, footer, links | `_config.yaml`                                                                       |
| Images                  | `images/` — `team/` for portraits, `site/` for page banners, `blog/`, `research/`, `photos/`… |

Never edit `_site/`. It's the built site and is overwritten on every build.

## Common tasks

### Add a lab member

Create `_members/firstname-lastname.md` (or use **Lab Members → Add** in Pages CMS):

```yaml
---
name: "Jane Smith"
image: images/team/jane-smith.jpg
role: technician
description: "Lab Technician (2025 - present)"
links:
  email: jsmith@danforthcenter.org
  orcid: 0000-0002-1825-0097
  google-scholar: AbCdEfGhIjK        # the part after user= in the profile link
  linkedin: jane-smith               # the part after linkedin.com/in/
  bluesky: janesmith.bsky.social
  home-page: https://example.com
---

Jane's bio goes here, as one or more paragraphs.
```

- **`role`** puts the person in a section of the Team page. One of: `principal-investigator`, `staff`,
  `technician`, `research-scientist`, `postdoc`, `phd`, `masters`, `undergrad`, `high-school`, `honorary`.
- **`description`** is the short line under their photo: role and years only. The bio goes below the second `---`.
- **`links`** are all optional.
- **Photos:** roughly square, at least 400 px wide, under about 500 KB, named after the person. They're shown as
  circles, so keep the face centered.
- **Don't rename a member file** once it exists. The file name is the address of the person's page.

Current members appear on the Team page with their full bio (long bios collapse behind "Read more"). Former
members appear as small photos in the Hall of Fame, linking to their own page.

### Move someone to alumni

Add `group: alum` to their file and update the years, e.g. `description: "Lab Technician (2023 - 2025)"`. In Pages
CMS, set **Current member or alum?** to **alum**. Their `role` stays the same and picks their alumni section.
Optionally add an update line to the bio, e.g. *Update: Jane is now a PhD student at …*

### Post news

Add `_posts/2026-10-19-short-title.md` (or use **News & Blog** in Pages CMS):

```yaml
---
title: "Jane Smith wins poster award"
author: jane-smith
image: images/blog/jane-poster.jpg
tags: news
---

The text of the post.
```

The date in the file name is the date shown on the site.

### Add a paper

Papers are listed automatically from DOIs and ORCID iDs. Citations refresh every Monday, and whenever `main`
changes.

- **One paper:** add a line to `_data/sources.yaml`: `- id: doi:10.1234/abcd.5678`
- **Everything on someone's ORCID record:** replace the `[]` in `_data/orcid.yaml` with `- orcid: 0000-0000-0000-0000`

### Change a page banner

Each page sets its banner photo with a `header:` line at the top of its file, e.g.
`header: images/site/research.jpg`. Pages without one use the defaults in `_config.yaml`.

### Change the Team page sections

Edit `_data/team-sections.yaml` to rename, reorder, or regroup sections. Each section lists the `role`s it shows.
Sections with nobody in them are hidden automatically.

## Previewing changes on your computer

You need [Ruby](https://www.ruby-lang.org/) (on Windows, [RubyInstaller](https://rubyinstaller.org/) with the
DevKit), [Python 3](https://www.python.org/), and [Git](https://git-scm.com/).

```bash
git clone https://github.com/ajmillerlabstl/millerlab-website.git
cd millerlab-website

# one time
bundle install
python -m venv ~/.venvs/millerlab
# Windows: ~/.venvs/millerlab/Scripts/activate    macOS/Linux: source ~/.venvs/millerlab/bin/activate
pip install -r _cite/requirements.txt

# each time (activate the venv first)
python _cite/cite.py          # only needed after changing publications
bundle exec jekyll serve      # then open http://127.0.0.1:4000
```

The preview rebuilds when you save a file, except `_config.yaml`: stop the server (Ctrl+C) and start it again
after changing that.

Then publish:

```bash
git pull                      # GitHub's automations commit too, so always pull first
git add -A
git commit -m "Describe the change"
git push
```

## How publishing works

- **On push to `main`:** citations are updated (`_cite/cite.py`), the site is built, and the result is pushed to
  the `gh-pages` branch, which GitHub Pages serves.
- **Every Monday:** citations are refreshed, so new papers appear on their own.
- **Pull requests** get a preview build, so a change can be checked before it goes live.
- If a build fails, the live site stays as it was. See the **Actions** tab for the error.

## Changes from the template

Things specific to this site, for whoever maintains it next:

- **Team page:** grouped into the old site's sections by `role` (`_data/team-sections.yaml`,
  `_includes/team-sections.html`). Current members show their full bio inline (`_includes/member-bio.html`,
  `_styles/member-bio.scss`), with long bios collapsed by `_scripts/read-more.js`. Role icons are removed from
  portraits.
- **Pages CMS** forms are configured in `.pages.yml`.
- **Windows support:** the link checker in `_plugins/misc.rb` is skipped when `libcurl` isn't available, and the
  `ostruct` gem is added for Ruby 4.
- **GitHub builds** use Ruby 3.4 (`.github/workflows/build-site.yaml`, `build-preview.yaml`).
- **Branding:** the template logo, favicon, and share image are replaced, and the footer credit is changed.
- **Content** was converted from the Weebly export with `_scripts/convert_from_weebly.py`.

## Credits and license

Built on the [Lab Website Template](https://github.com/greenelab/lab-website-template) by the
[Greene Lab](https://greenelab.com/), used under the BSD 3-Clause License (see `LICENSE.md`).
[Documentation for the template](https://greene-lab.gitbook.io/lab-website-template-docs) covers components and
options not described here.

Site content and photos © the Miller Lab.
