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

- Work on `main`. Never commit to the `drafts` branch from here; it belongs to Pages CMS editors.
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
| Publications               | `_data/sources.yaml`, one DOI per line                               |
| Gallery                    | `_data/gallery.yaml`                                                 |
| Pages                      | `research/`, `teaching/`, `outreach/`, `media/`, `photos/`, `join-us/`, `team/`, `publications/`, `index.md` |
| Site title, header image   | `_config.yaml`                                                       |
| Images                     | `images/` (`team/`, `blog/`, `research/`, `photos/`...)              |
| Pages CMS forms            | `.pages.yml`                                                         |

In member files, keep `description` to a title and years; the bio goes below the second `---`.

## Drafts and approvals

Lab members without GitHub accounts edit in Pages CMS on the `drafts` branch. `main` is protected: only owners and
repository admins can change it directly. When `drafts` has changes, a workflow opens a pull request titled
"Drafts waiting for approval", and a bot comments a preview link.

When asked whether there are drafts waiting:

1. `gh pr list --head drafts --base main`
2. For an open one, summarize who changed what in plain language (`gh pr view <n>`, `gh pr diff <n>`), and give the
   preview link from the bot's comment (`gh pr view <n> --comments`).
3. Merge only when the user clearly approves: `gh pr merge <n> --merge`. Always use `--merge`; squash or rebase
   breaks the automatic reset of `drafts` afterwards.
4. If the user wants something fixed first, explain that the editor can fix it in Pages CMS (still on `drafts`), or
   Molly can fix it. Don't edit `drafts` yourself unless the user insists.

Approvers get one reminder email per weekday morning while drafts are waiting, from `.github/workflows/drafts-reminder.yaml`.
Add new admins to `APPROVERS` there (GitHub usernames).
