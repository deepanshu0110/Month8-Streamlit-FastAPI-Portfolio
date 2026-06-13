"""
=========================================
DAY 152 – WRITTEN ANSWERS (COLLECTIVE)
=========================================

Task 1 – Trigger keyword:
    Keyword that separates schedule entries: `-` (hyphen, each cron entry is a list item under `cron:`).

Task 3 – Skipped jobs:
    Jobs skipped if `test` fails: `lint`, `build-docker`, `deploy` (all jobs that depend on `test` via `needs:`).

Task 4 – Why secrets must not be hardcoded:
    Secrets must never be hardcoded in workflow files because the files are public (in the repository).
    Anyone with repo access could read them, compromising deployment credentials and other services.

Task 5 – Cache behaviour when requirements.txt changes:
    When `requirements.txt` changes, the hash in the cache key changes, causing a cache miss.
    A new cache entry is created after the `pip install` step runs, and subsequent runs will use that new cache.

Task 6B – NRA Insight (CI/CD business value):
    Number  : 0 manual deployment steps after committing `.github/workflows/ci.yml`.
    Reason  : Failing tests block the `deploy` job via `needs: test` — broken code never reaches Render,
              and the README badge turns red immediately.
    Action  : Commit `.github/workflows/ci.yml` to the repo, add `RENDER_DEPLOY_HOOK` to GitHub Secrets,
              and add the badge URL to README.md.

Local run command for tests (Task 2 reference):
    pytest tests/ -v
"""

