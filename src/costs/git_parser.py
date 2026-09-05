"""Git commit parsing utilities."""

import re
from datetime import datetime, date
from typing import List, Optional, Tuple, Union
import git

DIFF_BATCH_SIZE = 16
_COMMIT_HEADER = re.compile(r"(?m)^\x00([0-9a-f]{40,64})\x00\n")
_DIFF_OPTIONS = [
    "--no-ext-diff",
    "--no-textconv",
    "--no-color",
    "--src-prefix=a/",
    "--dst-prefix=b/",
]


def get_commit_diff(repo: git.Repo, commit: git.Commit) -> str:
    """Return a forward patch, including root commits and file headers.

    Compare merges with their first parent. Disable external diff helpers and
    textconv so repository configuration cannot execute programs during analysis.
    A single Git call avoids materializing a Diff object for every changed file.
    """
    if commit.parents:
        return repo.git.diff(
            *_DIFF_OPTIONS,
            commit.parents[0].hexsha,
            commit.hexsha,
            "--",
            strip_newline_in_stdout=False,
        )
    return repo.git.show(
        *_DIFF_OPTIONS,
        "--format=",
        "--root",
        commit.hexsha,
        "--",
        strip_newline_in_stdout=False,
    )


def _read_commit_diffs(
    repo: git.Repo, commits: List[git.Commit]
) -> List[Tuple[git.Commit, str]]:
    """Amortize Git startup over bounded groups, preserving selection and order."""
    results = []
    for start in range(0, len(commits), DIFF_BATCH_SIZE):
        batch = commits[start : start + DIFF_BATCH_SIZE]
        output = repo.git.show(
            *_DIFF_OPTIONS,
            "--format=%x00%H%x00",
            "--first-parent",
            "--root",
            "--patch",
            *(commit.hexsha for commit in batch),
            "--",
            strip_newline_in_stdout=False,
        )
        # A patch content line always has a diff prefix, so a NUL at the start
        # of a line cannot be confused with source text (even forced text).
        parts = _COMMIT_HEADER.split(output)
        patches = {parts[i]: parts[i + 1].strip("\n") for i in range(1, len(parts), 2)}
        for commit in batch:
            if commit.hexsha not in patches:
                raise ValueError("Git output is missing a requested commit")
            patch = patches[commit.hexsha]
            results.append((commit, patch + "\n" if patch else ""))
    return results


def is_ai_commit(commit: git.Commit, tag_pattern: str = r"\[ai:") -> bool:
    """Check if commit message contains AI tag."""
    return bool(re.search(tag_pattern, commit.message))


def extract_ai_tag(commit: git.Commit) -> Optional[str]:
    """Extract AI tag from commit message."""
    match = re.search(r"\[ai:([^\]]+)\]", commit.message)
    return match.group(1) if match else None


def is_commit_in_date_range(
    commit: git.Commit,
    since: Optional[Union[date, datetime]] = None,
    until: Optional[Union[date, datetime]] = None,
    specific_date: Optional[date] = None,
) -> bool:
    """Check if commit falls within date range.

    Args:
        commit: Git commit object
        since: Start date (inclusive)
        until: End date (inclusive)
        specific_date: Exact date to match (overrides since/until)

    Returns:
        True if commit is within the specified date range
    """
    if since is None and until is None and specific_date is None:
        return True
    commit_date = commit.committed_datetime.date()
    since = _to_date(since)
    until = _to_date(until)
    specific_date = _to_date(specific_date)

    if specific_date:
        return commit_date == specific_date

    if since and commit_date < since:
        return False

    if until and commit_date > until:
        return False

    return True


def get_first_commit_date(repo: git.Repo) -> date:
    """Get the date of the first commit in the repository."""
    try:
        # Get all commits and find the oldest one
        all_commits = list(repo.iter_commits("--all"))
        if not all_commits:
            return date.today()

        # The last commit in the list is the oldest (first)
        oldest_commit = all_commits[-1]
        return oldest_commit.committed_datetime.date()
    except Exception:
        return date.today()


def _to_date(val: Optional[Union[date, datetime, str]]) -> Optional[date]:
    """Helper to convert various types to a date object."""
    if val is None:
        return None
    if isinstance(val, str):
        return datetime.strptime(val, "%Y-%m-%d").date()
    if isinstance(val, datetime):
        return val.date()
    return val


def _parse_date_args(
    repo: git.Repo,
    since: Optional[Union[date, datetime, str]] = None,
    until: Optional[Union[date, datetime, str]] = None,
    specific_date: Optional[Union[date, str]] = None,
    full_history: bool = False,
) -> Tuple[Optional[date], Optional[date], Optional[date]]:
    """Parse various date argument formats into standard date objects."""
    if specific_date:
        return None, None, _to_date(specific_date)

    parsed_since = _to_date(since)
    parsed_until = _to_date(until)

    # Full history needs no lower bound and no preliminary repository scan.

    return parsed_since, parsed_until, None


def parse_commits(
    repo_path: str,
    max_count: int = 100,
    ai_only: bool = True,
    since: Optional[Union[date, datetime, str]] = None,
    until: Optional[Union[date, datetime, str]] = None,
    specific_date: Optional[Union[date, str]] = None,
    full_history: bool = False,
) -> List[Tuple[git.Commit, str]]:
    """Parse commits from repository with date filtering."""
    repo = git.Repo(repo_path)
    commits = []

    # Parse date arguments
    parsed_since, parsed_until, parsed_specific = _parse_date_args(
        repo, since, until, specific_date, full_history
    )

    if parsed_since and parsed_until and parsed_since > parsed_until:
        raise ValueError("since must not be later than until")

    # Determine max_count for full history
    iter_count = max_count if not full_history else None

    for commit in repo.iter_commits(max_count=iter_count):
        # Check AI tag filter
        if ai_only and not is_ai_commit(commit):
            continue

        # Check date filters
        if not is_commit_in_date_range(
            commit, parsed_since, parsed_until, parsed_specific
        ):
            continue

        commits.append(commit)

    return _read_commit_diffs(repo, commits)


def get_repo_name(repo: git.Repo) -> str:
    """Get repository name from git remote or directory."""
    try:
        origin = repo.remote("origin")
        url = origin.url
        # Extract repo name from URL
        if url.endswith(".git"):
            url = url[:-4]
        return url.split("/")[-1]
    except Exception:
        return repo.working_dir.split("/")[-1]


def get_repo_stats(repo_path: str) -> dict:
    """Get repository statistics including first commit date."""
    repo = git.Repo(repo_path)

    all_commits = list(repo.iter_commits("--all"))
    first_commit = all_commits[-1] if all_commits else None
    last_commit = all_commits[0] if all_commits else None

    return {
        "total_commits": len(all_commits),
        "first_commit_date": first_commit.committed_datetime.date()
        if first_commit
        else None,
        "last_commit_date": last_commit.committed_datetime.date()
        if last_commit
        else None,
        "repo_name": get_repo_name(repo),
    }
