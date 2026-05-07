#!/usr/bin/env python3
"""
Git Storyteller - Repository Analysis Script

Analyzes a Git repository's history and produces a structured JSON report
containing commit data, contributor stats, file change heatmaps, dramatic
events, and milestone detection.

Usage:
    python3 analyze.py <repo-path> [--output <output-path>]

Output defaults to ./git-story-data.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta


# Limit analysis to recent 2 years for performance on large repos
MAX_HISTORY_DAYS = 730
FIELD_SEP = "<<GS_SEP>>"
RECORD_SEP = "<<GS_REC>>"


def run_git(args, cwd, timeout=120):
    """Run a git command and return stdout as string."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"Warning: git {' '.join(args[:3])}... returned code {result.returncode}",
                  file=sys.stderr)
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Warning: git {' '.join(args[:3])}... timed out", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("Error: git is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)


def parse_commits(repo_path, since_date):
    """Parse git log into structured commit records."""
    fmt = FIELD_SEP.join(["%H", "%an", "%ae", "%aI", "%s", "%P"])
    raw = run_git(
        ["log", f"--since={since_date}", f"--format={fmt}{RECORD_SEP}", "--no-merges"],
        cwd=repo_path,
        timeout=180,
    )
    commits = []
    for record in raw.split(RECORD_SEP):
        record = record.strip()
        if not record:
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) < 6:
            continue
        hash_, author, email, date_iso, subject, parents = parts
        commits.append({
            "hash": hash_[:12],
            "author": author.strip(),
            "email": email.strip(),
            "date": date_iso.strip(),
            "subject": subject.strip(),
            "parents": parents.strip().split(),
        })
    return commits


def parse_merge_commits(repo_path, since_date):
    """Parse merge commits separately for milestone detection."""
    fmt = FIELD_SEP.join(["%H", "%an", "%aI", "%s"])
    raw = run_git(
        ["log", f"--since={since_date}", f"--format={fmt}{RECORD_SEP}", "--merges"],
        cwd=repo_path,
        timeout=60,
    )
    merges = []
    for record in raw.split(RECORD_SEP):
        record = record.strip()
        if not record:
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) < 4:
            continue
        hash_, author, date_iso, subject = parts
        merges.append({
            "hash": hash_[:12],
            "author": author.strip(),
            "date": date_iso.strip(),
            "subject": subject.strip(),
            "type": "merge",
        })
    return merges


def get_tags(repo_path, since_date):
    """Get tags with dates."""
    raw = run_git(
        ["tag", "--sort=-creatordate",
         "--format=%(refname:short)%(if)%(creatordate:iso)%(then)" + FIELD_SEP + "%(creatordate:iso-strict)%(end)"],
        cwd=repo_path,
    )
    tags = []
    for line in raw.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split(FIELD_SEP)
        tag_name = parts[0].strip()
        tag_date = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
        tags.append({"name": tag_name, "date": tag_date})
    return tags


def get_numstat(repo_path, since_date):
    """Get file-level change stats using --numstat."""
    raw = run_git(
        ["log", f"--since={since_date}", "--numstat", "--format=" + RECORD_SEP + "%H" + FIELD_SEP + "%aI"],
        cwd=repo_path,
        timeout=300,
    )
    file_stats = defaultdict(lambda: {"additions": 0, "deletions": 0, "commits": 0})
    commit_sizes = []

    current_hash = None
    current_date = None
    current_add = 0
    current_del = 0

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if RECORD_SEP in line:
            # Save previous commit size
            if current_hash:
                commit_sizes.append({
                    "hash": current_hash,
                    "date": current_date,
                    "additions": current_add,
                    "deletions": current_del,
                })
            rest = line.replace(RECORD_SEP, "").strip()
            if FIELD_SEP in rest:
                parts = rest.split(FIELD_SEP)
                current_hash = parts[0][:12]
                current_date = parts[1].strip() if len(parts) > 1 else None
            else:
                current_hash = rest[:12] if rest else None
                current_date = None
            current_add = 0
            current_del = 0
            continue
        # numstat line: additions\tdeletions\tfilename
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                add = int(parts[0]) if parts[0] != "-" else 0
                delete = int(parts[1]) if parts[1] != "-" else 0
            except ValueError:
                continue
            filename = parts[2]
            file_stats[filename]["additions"] += add
            file_stats[filename]["deletions"] += delete
            file_stats[filename]["commits"] += 1
            current_add += add
            current_del += delete

    # Don't forget the last commit
    if current_hash:
        commit_sizes.append({
            "hash": current_hash,
            "date": current_date,
            "additions": current_add,
            "deletions": current_del,
        })

    return dict(file_stats), commit_sizes


def compute_contributor_stats(commits):
    """Compute contributor rankings and statistics."""
    author_commits = Counter()
    author_first = {}
    author_last = {}

    for c in commits:
        author = c["author"]
        author_commits[author] += 1
        date = c["date"]
        if author not in author_first or date < author_first[author]:
            author_first[author] = date
        if author not in author_last or date > author_last[author]:
            author_last[author] = date

    contributors = []
    for author, count in author_commits.most_common():
        contributors.append({
            "name": author,
            "commits": count,
            "first_commit": author_first.get(author, ""),
            "last_commit": author_last.get(author, ""),
        })
    return contributors


def compute_commit_frequency(commits):
    """Compute daily and weekly commit counts."""
    daily = Counter()
    for c in commits:
        try:
            dt = datetime.fromisoformat(c["date"])
            day = dt.strftime("%Y-%m-%d")
            daily[day] += 1
        except (ValueError, TypeError):
            continue

    # Sort by date
    sorted_daily = sorted(daily.items())

    # Aggregate to weekly
    weekly = defaultdict(int)
    for day_str, count in sorted_daily:
        dt = datetime.strptime(day_str, "%Y-%m-%d")
        week_start = dt - timedelta(days=dt.weekday())
        weekly[week_start.strftime("%Y-%m-%d")] += count

    return {
        "daily": sorted_daily,
        "weekly": sorted(weekly.items()),
    }


def detect_dramatic_events(commits):
    """Detect interesting/dramatic events in commit history."""
    events = []

    for c in commits:
        subject_lower = c["subject"].lower()

        # Late-night commits (22:00 - 06:00)
        try:
            dt = datetime.fromisoformat(c["date"])
            hour = dt.hour
            if hour >= 22 or hour < 6:
                events.append({
                    "type": "late_night",
                    "hash": c["hash"],
                    "author": c["author"],
                    "date": c["date"],
                    "subject": c["subject"],
                    "detail": f"Committed at {dt.strftime('%H:%M')} local time",
                })
        except (ValueError, TypeError):
            pass

        # Reverts
        if subject_lower.startswith("revert"):
            events.append({
                "type": "revert",
                "hash": c["hash"],
                "author": c["author"],
                "date": c["date"],
                "subject": c["subject"],
                "detail": "A change was reverted",
            })

        # Hotfix commits
        if "hotfix" in subject_lower or "hot-fix" in subject_lower:
            events.append({
                "type": "hotfix",
                "hash": c["hash"],
                "author": c["author"],
                "date": c["date"],
                "subject": c["subject"],
                "detail": "Emergency hotfix deployed",
            })

        # Fix/bug patterns with urgency
        if re.search(r"\burgent\b|\bcritical\b|\bemergency\b", subject_lower):
            events.append({
                "type": "urgent",
                "hash": c["hash"],
                "author": c["author"],
                "date": c["date"],
                "subject": c["subject"],
                "detail": "Urgent fix applied",
            })

    return events


def detect_milestones(commits, merge_commits, tags, commit_sizes):
    """Detect milestones: tags, large refactors, significant merges."""
    milestones = []

    # Tags as milestones
    for tag in tags:
        milestones.append({
            "type": "tag",
            "name": tag["name"],
            "date": tag.get("date", ""),
            "detail": f"Version {tag['name']} released",
        })

    # Merge commits as milestones (limit to avoid noise)
    for mc in merge_commits[:50]:
        milestones.append({
            "type": "merge",
            "name": mc["subject"][:80],
            "date": mc["date"],
            "detail": f"Merge by {mc['author']}",
        })

    # Large refactors: commits with >500 line changes
    for cs in commit_sizes:
        total = cs["additions"] + cs["deletions"]
        if total > 500:
            milestones.append({
                "type": "large_change",
                "name": f"Large change ({cs['additions']}+ / {cs['deletions']}-)",
                "date": cs.get("date", ""),
                "detail": f"Commit {cs['hash']} changed {total} lines",
            })

    return milestones


def build_file_heatmap(file_stats, top_n=30):
    """Build a heatmap of the most-changed files."""
    ranked = sorted(
        file_stats.items(),
        key=lambda x: x[1]["additions"] + x[1]["deletions"],
        reverse=True,
    )
    return [
        {
            "file": fname,
            "additions": stats["additions"],
            "deletions": stats["deletions"],
            "commits": stats["commits"],
            "total_changes": stats["additions"] + stats["deletions"],
        }
        for fname, stats in ranked[:top_n]
    ]


def main():
    parser = argparse.ArgumentParser(description="Analyze git repository history")
    parser.add_argument("repo", help="Path to the git repository")
    parser.add_argument("--output", "-o", default="git-story-data.json",
                        help="Output JSON file path (default: git-story-data.json)")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo)

    # Validate it's a git repo
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        # Maybe it's a bare repo or subdirectory
        check = run_git(["rev-parse", "--git-dir"], cwd=repo_path)
        if not check.strip():
            print(f"Error: {repo_path} is not a git repository", file=sys.stderr)
            sys.exit(1)

    since_date = (datetime.now() - timedelta(days=MAX_HISTORY_DAYS)).strftime("%Y-%m-%d")
    print(f"Analyzing repository: {repo_path}")
    print(f"History window: {since_date} to present")

    # Get repo name
    repo_name = os.path.basename(repo_path)
    remote_url = run_git(["remote", "get-url", "origin"], cwd=repo_path).strip()

    # Collect data
    print("  Parsing commit log...")
    commits = parse_commits(repo_path, since_date)
    print(f"  Found {len(commits)} commits (excluding merges)")

    print("  Parsing merge commits...")
    merge_commits = parse_merge_commits(repo_path, since_date)
    print(f"  Found {len(merge_commits)} merge commits")

    print("  Collecting tags...")
    tags = get_tags(repo_path, since_date)
    print(f"  Found {len(tags)} tags")

    print("  Analyzing file changes (this may take a moment)...")
    file_stats, commit_sizes = get_numstat(repo_path, since_date)
    print(f"  Analyzed changes across {len(file_stats)} files")

    # Process data
    print("  Computing contributor stats...")
    contributors = compute_contributor_stats(commits)
    print(f"  Found {len(contributors)} contributors")

    print("  Computing commit frequency...")
    frequency = compute_commit_frequency(commits)

    print("  Detecting dramatic events...")
    dramatic_events = detect_dramatic_events(commits)
    print(f"  Found {len(dramatic_events)} dramatic events")

    print("  Detecting milestones...")
    milestones = detect_milestones(commits, merge_commits, tags, commit_sizes)
    print(f"  Found {len(milestones)} milestones")

    print("  Building file heatmap...")
    heatmap = build_file_heatmap(file_stats)

    # Compute summary
    total_additions = sum(cs["additions"] for cs in commit_sizes)
    total_deletions = sum(cs["deletions"] for cs in commit_sizes)

    dates = [c["date"] for c in commits if c.get("date")]
    first_date = min(dates) if dates else ""
    last_date = max(dates) if dates else ""

    report = {
        "meta": {
            "repo_name": repo_name,
            "repo_path": repo_path,
            "remote_url": remote_url,
            "analysis_date": datetime.now().isoformat(),
            "history_since": since_date,
        },
        "summary": {
            "total_commits": len(commits) + len(merge_commits),
            "total_non_merge_commits": len(commits),
            "total_merge_commits": len(merge_commits),
            "total_contributors": len(contributors),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_files_changed": len(file_stats),
            "first_commit_date": first_date,
            "last_commit_date": last_date,
        },
        "contributors": contributors,
        "frequency": frequency,
        "dramatic_events": dramatic_events,
        "milestones": milestones,
        "file_heatmap": heatmap,
        "commit_sizes": commit_sizes[-200:],  # Keep last 200 for the chart
    }

    # Write output
    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nAnalysis complete! Output written to: {output_path}")
    print(f"  Commits: {report['summary']['total_commits']}")
    print(f"  Contributors: {report['summary']['total_contributors']}")
    print(f"  Dramatic events: {len(dramatic_events)}")
    print(f"  Milestones: {len(milestones)}")


if __name__ == "__main__":
    main()
