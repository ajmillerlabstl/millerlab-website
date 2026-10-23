# Miller Lab website

The Miller Lab website, built with the [Lab Website Template](https://greene-lab.gitbook.io/lab-website-template-docs)
(Jekyll). Repository: `ajmillerlabstl/millerlab-website`. Live site: https://ajmillerlabstl.github.io/millerlab-website/

## Who you're working with

The people using Claude here are lab owners (Molly Hanlon, Allison Miller), and some are new to Git and GitHub.
Explain in plain language what you're doing and what changed. Avoid jargon; when a Git term is unavoidable, say what
it means in a few words.

## Every session

1. Check that you're in the `millerlab-website` folder on the `main` branch, with no unsaved local changes. If not,
   explain what you found before doing anything else.
2. Get the latest changes: `git pull --ff-only`. Other people edit the site through Pages CMS, so this is never
   optional. If it fails, stop and explain; don't force anything.

## Making edits

- Work on `main`.
- After editing, summarize what changed in plain language (which pages, what text, which images) before publishing.
- **Only commit and push when the user clearly asks** ("publish it", "push it", "go ahead"). Pushing to `main`
  publishes the live site within 2 to 5 minutes.
- Write descriptive commit messages, and commit only the files you changed.
- Never force-push, rewrite history, or delete branches.
- If you hit a merge conflict or an error you can't explain, stop and tell the user to contact Molly.

## Where things live

| To change                  | Edit                                                                 |
| -------------------------- | -------------------------------------------------------------------- |
| News, announcements, blog  | `_posts/`, one file per post, named `YYYY-MM-DD-title.md`            |
| Lab members                | `_members/`, one file per person (`group: alum` moves someone to alumni) |
| Team page sections         | `_data/team-sections.yaml`; a person's `role` picks their section    |
| Publications               | `_papers/`, one file per paper (its DOI); `_data/citations.yaml` is generated |
| Gallery                    | `_data/gallery.yaml`                                                 |
| Pages                      | `research/`, `teaching/`, `outreach/`, `media/`, `photos/`, `join-us/`, `team/`, `publications/`, `index.md` |
| Site title, header image   | `_config.yaml`                                                       |
| Images                     | `images/` (`team/`, `blog/`, `research/`, `photos/`...)              |
| Pages CMS forms            | `.pages.yml`                                                         |

In member files, keep `description` to a title and years; the bio goes below the second `---`.

## History and undoing changes

Lab members edit through Pages CMS and save straight to `main`. Every save is a commit, so any change can be seen and
undone.

- **What changed recently:** `git log --since="2 weeks ago" --format="%h %ad %an | %s" --date=short`, then
  `git show <hash>` for the details. Summarize in plain language.
- **Who:** saves by people invited to Pages CMS by email show as `pages-cms[bot]`, not by name. People who sign in to
  Pages CMS with GitHub show under their own name.
- **Undo a change:** `git revert <hash>`, then publish as usual once the user agrees. Never use `git reset` or
  force-push to undo published changes.
