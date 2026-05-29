# =============================================================================
# AUTO GITHUB SYNC -- Month 8 (Streamlit + FastAPI Portfolio)
# Watches: C:\Users\Deepanshu\OneDrive\Desktop\Month8
# Repo   : deepanshu0110/Month8-Streamlit-FastAPI-Portfolio
# Run    : python auto_sync.py
# Stop   : Ctrl+C
# =============================================================================

import os
import re
import sys
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
WATCH_FOLDER = os.path.join(
    os.path.expanduser("~"),
    "OneDrive", "Desktop", "Month8"
)
REPO_NAME    = "Month8-Streamlit-FastAPI-Portfolio"
GITHUB_USER  = "deepanshu0110"

EXTENSIONS = {
    ".py",      # Streamlit apps, FastAPI apps
    ".ipynb",   # teaching notebooks
    ".csv",     # datasets
    ".png",     # app screenshots
    ".jpg",
    ".jpeg",
    ".pdf",
    ".md",      # README, notes
    ".txt",     # requirements.txt, notes
    ".json",    # config, API payloads
    ".env",     # (gitignored, but listed for awareness)
}

# Files to always ignore
IGNORE_NAMES = {
    "auto_sync.py",
    ".gitignore",
    "desktop.ini",
    "thumbs.db",
}

DEBOUNCE_SECONDS = 3  # wait 3s after last change before committing

# -----------------------------------------------------------------------------
# DAY-NUMBER + TOPIC PARSER
# -----------------------------------------------------------------------------
DAY_TOPICS = {
    141: "Streamlit Fundamentals",
    142: "File Upload + Dynamic Filters",
    143: "Streamlit EDA Dashboard",
    144: "ML Model Integration",
    145: "Session State + Caching",
    146: "Multi-Page Streamlit Apps",
    147: "FastAPI Basics",
    148: "FastAPI + ML Model Serving",
    149: "Deployment - Streamlit Cloud",
    150: "Deployment - Render + Docker Basics",
    151: "Week 1 Mini-Project (EDA App)",
    152: "Week 2 Mini-Project (ML Prediction App)",
    153: "Advanced Streamlit - Plotly + Custom CSS",
    154: "Streamlit + Database Integration",
    155: "FastAPI Advanced - Auth + CORS",
    156: "Full-Stack App - Streamlit + FastAPI",
    157: "Week 3 Mini-Project (Full-Stack App)",
    158: "Gap Day - IELTS Prep Integration",
    159: "Month 8 Capstone Part 1",
    160: "Month 8 Capstone Part 2",
}

def parse_day(filename):
    """Extract day number from filename like Day141_app.py or day141_something.csv"""
    match = re.search(r'[Dd]ay[_\s]?(\d{1,3})', filename)
    if match:
        return int(match.group(1))
    return None

def file_type_label(ext):
    labels = {
        ".py":    "Python",
        ".ipynb": "Notebook",
        ".csv":   "Dataset",
        ".png":   "Screenshot",
        ".jpg":   "Screenshot",
        ".jpeg":  "Screenshot",
        ".pdf":   "PDF",
        ".md":    "Markdown",
        ".txt":   "Text",
        ".json":  "JSON",
    }
    return labels.get(ext.lower(), ext.upper().lstrip("."))

def build_commit_message(filename):
    day = parse_day(filename)
    ext = Path(filename).suffix.lower()
    ftype = file_type_label(ext)
    if day and day in DAY_TOPICS:
        topic = DAY_TOPICS[day]
        return f"add: Day {day} -- {topic} [{ftype}]"
    elif day:
        return f"add: Day {day} [{ftype}] -- {filename}"
    else:
        return f"add: {filename} [{ftype}]"

# -----------------------------------------------------------------------------
# README GENERATOR
# -----------------------------------------------------------------------------
def build_readme(watch_path):
    """Scan folder and regenerate README.md with a full scorecard table."""

    tracked_files = []
    for f in sorted(os.listdir(watch_path)):
        ext = Path(f).suffix.lower()
        if ext in EXTENSIONS and f not in IGNORE_NAMES and not f.startswith("."):
            day = parse_day(f)
            tracked_files.append((day or 9999, f, ext))

    tracked_files.sort(key=lambda x: (x[0], x[1]))

    # Build table rows
    rows = []
    for day, fname, ext in tracked_files:
        topic = DAY_TOPICS.get(day, "—") if day != 9999 else "—"
        day_str = str(day) if day != 9999 else "—"
        ftype = file_type_label(ext)
        rows.append(f"| {day_str} | {topic} | `{fname}` | {ftype} |")

    table = "\n".join(rows) if rows else "| — | No files tracked yet | — | — |"

    readme = f"""# Month 8 -- Streamlit + FastAPI Deployment Portfolio
**Deepanshu Garg | [@deepanshu0110](https://github.com/{GITHUB_USER})**

> 20-day structured programme: Streamlit dashboards, FastAPI model serving,
> full-stack app architecture, and live deployment on Streamlit Cloud + Render.

---

## Month 8 Roadmap

| Week | Days | Focus |
|------|------|-------|
| W1   | 141-145 | Streamlit basics -- layout, widgets, filters, caching |
| W2   | 146-150 | ML model integration + multi-page apps |
| W3   | 151-155 | FastAPI basics -- REST endpoints, model serving |
| W4   | 156-158 | Full-stack app (Streamlit + FastAPI) + deployment |
| Capstone | 159-160 | Deployed live app on Streamlit Cloud |

---

## File Index

| Day | Topic | File | Type |
|-----|-------|------|------|
{table}

---

## Previous Months

| Month | Repo | Score |
|-------|------|-------|
| Month 1 -- Excel | [excel-data-analytics](https://github.com/{GITHUB_USER}/excel-data-analytics) | 88/80 |
| Month 2 -- SQL | [Month2-SQL-Portfolio](https://github.com/{GITHUB_USER}/Month2-SQL-Portfolio) | 119/120 |
| Month 3 -- Python/Pandas | [Month3-Python-Portfolio](https://github.com/{GITHUB_USER}/Month3-Python-Portfolio) | 100/100 |
| Month 4 -- Power BI + Tableau | [Month4-PowerBI-Tableau-Portfolio](https://github.com/{GITHUB_USER}/Month4-PowerBI-Tableau-Portfolio) | 110/100 |
| Month 5 -- BI + Upwork | [Month5-BI-Upwork-Portfolio](https://github.com/{GITHUB_USER}/Month5-BI-Upwork-Portfolio) | 120/120 |
| Month 7 -- Advanced ML | [Month7-AdvancedML-Portfolio](https://github.com/{GITHUB_USER}/Month7-AdvancedML-Portfolio) | 1440/1440 (PERFECT) |

---

*Auto-synced via watchdog -- Last updated: {datetime.now().strftime("%d %b %Y %H:%M")}*
"""
    readme_path = os.path.join(watch_path, "README.md")
    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(readme)
    print(f"  README.md updated ({len(rows)} files tracked)")

# -----------------------------------------------------------------------------
# GIT HELPERS
# -----------------------------------------------------------------------------
def git_run(args, cwd):
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def commit_and_push(watch_path, changed_files):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Changes detected: {changed_files}")

    # Regenerate README first
    build_readme(watch_path)

    # Stage everything
    code, out, err = git_run(["add", "."], watch_path)
    if code != 0:
        print(f"  git add failed: {err}")
        return

    # Check if there's anything to commit
    code, out, err = git_run(["status", "--porcelain"], watch_path)
    if not out.strip():
        print("  Nothing new to commit.")
        return

    # Build commit message from the first real changed file
    real_files = [f for f in changed_files if f not in ("README.md", "auto_sync.py")]
    msg_file = real_files[0] if real_files else changed_files[0]
    commit_msg = build_commit_message(msg_file)

    if len(changed_files) > 1:
        commit_msg += f" (+{len(changed_files) - 1} more)"

    code, out, err = git_run(["commit", "-m", commit_msg], watch_path)
    if code != 0:
        print(f"  git commit failed: {err}")
        return
    print(f"  Committed: {commit_msg}")

    code, out, err = git_run(["push", "origin", "main"], watch_path)
    if code != 0:
        print(f"  git push failed: {err}")
        print(f"  Try: git push -u origin main")
    else:
        print(f"  Pushed to GitHub. URL: https://github.com/{GITHUB_USER}/{REPO_NAME}")

# -----------------------------------------------------------------------------
# WATCHDOG HANDLER
# -----------------------------------------------------------------------------
class SyncHandler(FileSystemEventHandler):
    def __init__(self, watch_path):
        self.watch_path = watch_path
        self._pending = set()
        self._timer = None
        self._lock = threading.Lock()

    def _schedule(self, filename):
        ext = Path(filename).suffix.lower()
        if ext not in EXTENSIONS:
            return
        if filename in IGNORE_NAMES:
            return
        if filename.startswith("."):
            return

        with self._lock:
            self._pending.add(filename)
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self._flush
            )
            self._timer.start()

    def _flush(self):
        with self._lock:
            files = list(self._pending)
            self._pending.clear()
        if files:
            commit_and_push(self.watch_path, files)

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(os.path.basename(event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            self._schedule(os.path.basename(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self._schedule(os.path.basename(event.dest_path))

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    watch_path = WATCH_FOLDER

    # Verify folder exists
    if not os.path.isdir(watch_path):
        print(f"ERROR: Watch folder not found: {watch_path}")
        print("Create it first:")
        print(f"  mkdir \"{watch_path}\"")
        sys.exit(1)

    # Verify it's a git repo
    git_dir = os.path.join(watch_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"ERROR: Not a git repo: {watch_path}")
        print("Run the setup script first: setup_month8_repo.ps1")
        sys.exit(1)

    print("=" * 60)
    print("AUTO GITHUB SYNC -- Month 8 (Streamlit + FastAPI)")
    print(f"Watching : {watch_path}")
    print(f"Repo     : {GITHUB_USER}/{REPO_NAME}")
    print(f"Triggers : {', '.join(sorted(EXTENSIONS))}")
    print(f"Debounce : {DEBOUNCE_SECONDS}s")
    print("Drop any file -> auto-push to GitHub")
    print("Stop: Ctrl+C")
    print("=" * 60)

    # Initial README build
    build_readme(watch_path)

    handler  = SyncHandler(watch_path)
    observer = Observer()
    observer.schedule(handler, watch_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
