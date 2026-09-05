"""Compare calculated line statistics to Git on real temporary repositories."""

from datetime import datetime, timezone

import git
import pytest

from src.costs import git_parser
from src.costs.tokenizers import GitDiffParser


@pytest.fixture
def repo(tmp_path):
    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test")
        config.set_value("user", "email", "test@example.invalid")
    return repo


def commit_file(repo, name, text, message="[ai:test] change"):
    path = repo.working_tree_dir + "/" + name
    with open(path, "w", encoding="utf-8") as stream:
        stream.write(text)
    repo.index.add([name])
    return repo.index.commit(message)


def assert_git_stats(repo, commit):
    diff = git_parser.get_commit_diff(repo, commit)
    if commit.parents:
        numstat = repo.git.diff("--numstat", commit.parents[0].hexsha, commit.hexsha)
    else:
        numstat = repo.git.show("--format=", "--numstat", commit.hexsha)
    added = deleted = 0
    for line in numstat.splitlines():
        a, d, _ = line.split("\t", 2)
        if a != "-":
            added += int(a)
            deleted += int(d)
    assert GitDiffParser.parse_diff_stats(diff) == {
        "added_lines": added,
        "deleted_lines": deleted,
        "total_changed": added + deleted,
    }
    return diff


def test_root_edit_delete_rename_binary_and_empty(repo):
    first = commit_file(repo, "code.txt", "-- decrement\n++ increment\nzażółć\n")
    assert "+-- decrement" in assert_git_stats(repo, first)
    changed = commit_file(repo, "code.txt", "++ increment\nnew\n")
    assert "--- a/code.txt" in assert_git_stats(repo, changed)
    repo.git.mv("code.txt", "renamed.txt")
    assert_git_stats(repo, repo.index.commit("rename"))
    repo.index.remove(["renamed.txt"], working_tree=True)
    assert_git_stats(repo, repo.index.commit("delete"))
    binary = commit_file(repo, "image.bin", "\x00\x01binary")
    assert "Binary files" in assert_git_stats(repo, binary)
    empty = repo.index.commit("empty")
    assert git_parser.get_commit_diff(repo, empty) == ""


def test_merge_uses_first_parent(repo):
    commit_file(repo, "main.txt", "base\n")
    main = repo.active_branch.name
    repo.git.checkout("-b", "feature")
    commit_file(repo, "feature.txt", "feature\n")
    repo.git.checkout(main)
    commit_file(repo, "main.txt", "base\nmain\n")
    repo.git.merge("feature", "--no-ff", "-m", "merge")
    diff = assert_git_stats(repo, repo.head.commit)
    assert "+feature" in diff
    assert "+main" not in diff


def test_external_diff_and_textconv_are_disabled(repo):
    first = commit_file(repo, "code.txt", "before\n")
    with repo.config_writer() as config:
        config.set_value("diff", "external", "this-command-must-not-run")
        config.set_value('diff "custom"', "textconv", "this-command-must-not-run")
    commit_file(repo, ".gitattributes", "*.txt diff=custom\n")
    last = commit_file(repo, "code.txt", "after\n")
    assert "+before" in git_parser.get_commit_diff(repo, first)
    assert "+after" in git_parser.get_commit_diff(repo, last)


def test_full_history_has_no_preliminary_scan_and_filters_remain(repo, monkeypatch):
    commit_file(repo, "a.txt", "one\n")
    commit_file(repo, "a.txt", "two\n", "manual change")

    def forbidden(*args):
        pytest.fail(
            "Full history must not scan all commits to derive a lower date bound"
        )

    monkeypatch.setattr(git_parser, "get_first_commit_date", forbidden)
    assert len(git_parser.parse_commits(repo.working_tree_dir, full_history=True)) == 1
    assert (
        len(
            git_parser.parse_commits(
                repo.working_tree_dir, full_history=True, ai_only=False
            )
        )
        == 2
    )
    assert git_parser.parse_commits(repo.working_tree_dir, max_count=1) == []
    assert git_parser.is_commit_in_date_range(
        repo.head.commit,
        since=datetime(2000, 1, 1, tzinfo=timezone.utc),
        until=datetime(2100, 1, 1),
    )
    with pytest.raises(ValueError, match="since"):
        git_parser.parse_commits(
            repo.working_tree_dir, since="2026-12-31", until="2026-01-01"
        )


def test_batched_patches_equal_individual_reads_and_keep_order(repo):
    first = commit_file(repo, "file.txt", "first\n")
    main = repo.active_branch.name
    for index in range(18):
        commit_file(repo, "file.txt", f"line {index}\n")
    repo.git.checkout("-b", "feature")
    commit_file(repo, "other.txt", "feature\n")
    repo.git.checkout(main)
    repo.git.merge("feature", "--no-ff", "-m", "merge")
    repo.index.commit("empty")
    commits = list(repo.iter_commits())
    result = git_parser.parse_commits(
        repo.working_tree_dir, full_history=True, ai_only=False
    )
    assert [c.hexsha for c, _ in result] == [c.hexsha for c in commits]
    assert result[-1][0].hexsha == first.hexsha
    for commit, patch in result:
        assert patch == git_parser.get_commit_diff(repo, commit)
