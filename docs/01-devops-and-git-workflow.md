# DevOps Culture and the Git/GitHub Workflow

## What is DevOps?
DevOps joins **Dev**elopment and **Op**erations so teams can ship small changes quickly, safely and repeatedly. Instead of "developers throw code over the wall to operations", one team owns a feature from idea to running in production.

Core ideas:
- **Automation:** anything repeated (testing, building, deploying) is done by a pipeline, not by hand.
- **Small, frequent changes:** easier to review, test and roll back than big releases.
- **Fast feedback:** a failing test tells you within minutes, not weeks.
- **Shared ownership:** the people who write the code also care how it runs.
- **Measure everything:** logs, metrics and alerts show whether a release is healthy.

## The DevOps loop
Plan -> Code -> Build -> Test -> Release -> Deploy -> Operate -> Monitor -> (back to Plan)

## Git and GitHub workflow used here
1. **Branch:** never work directly on `main`.
   ```bash
   git checkout -b feature/add-greeting
   ```
2. **Commit** small, clear changes:
   ```bash
   git add .
   git commit -m "Add greeting to home page"
   ```
3. **Push** and open a **pull request (PR)** on GitHub.
4. **CI runs automatically** on the PR: lint, tests, build, smoke test. A red check blocks the merge.
5. **Review:** a teammate reads the diff and comments (the PR template has a checklist).
6. **Merge to `main`:** this triggers the full pipeline: publish the image, deploy to staging, then production.

| Term | Meaning |
|---|---|
| Repository | The project and its full history |
| Branch | An isolated line of work |
| Commit | A saved snapshot with a message |
| Pull request | A request to merge a branch, with review and checks |
| Merge | Combining a branch into `main` |
| Branch protection | Settings that require checks/reviews before merging |

## CI vs CD
- **Continuous Integration (CI):** every change is merged often and automatically built and tested.
- **Continuous Delivery:** every passing change is *ready* to deploy, with a human approving the release.
- **Continuous Deployment:** every passing change is deployed automatically, with no approval.

This pipeline is **continuous delivery with an approval gate**: the `production` environment can require a reviewer before the last job runs.

## Useful Git commands
```bash
git status                  # what changed
git log --oneline -10       # recent history
git diff                    # unstaged changes
git pull                    # fetch and merge the latest main
git branch -d feature/x     # delete a merged branch
git revert <commit>         # undo a commit safely (new commit)
```
