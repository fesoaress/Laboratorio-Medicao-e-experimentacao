"""Exemplos construídos à mão: nunca avaliações da amostra real."""

import pytest

from src.corrective import message_signals, note_signals, patch_only, predict, semver
from src.corrective_validation import scores


@pytest.mark.parametrize("tag,expected", [("v2.3.1", (2, 3, 1)), ("2.3.1+build.9", (2, 3, 1)),
    ("2.3.1-beta.1", None), ("2.03.1", None), ("v2.3", None), ("release/2.3.1", None), ("", None)])
def test_semver_stable_only(tag, expected):
    assert semver(tag) == expected


@pytest.mark.parametrize("before,after,expected", [("v2.3.0", "v2.3.1", True),
    ("2.3.0", "2.3.9", True), ("2.3.1", "2.3.1+meta", False), ("2.3.1", "2.4.0", False),
    ("2.3.1", "3.3.2", False), ("2.3.1", "2.3.0", False), ("", "2.3.1", False)])
def test_patch_requires_actual_previous_version(before, after, expected):
    assert patch_only(before, after) == expected


@pytest.mark.parametrize("message,expected", [("FIX(parser): avoid crash", (True, False)),
    ("Revert broken change", (True, False)), ("hotfix regression", (True, False)),
    ("feat: add a command", (False, True)), ("Update fixture and prefix", (False, False)),
    ("fixed-point arithmetic", (False, False)), ("", (False, False)),
    ("chore: update\nfix: an unrelated quoted example", (False, False))])
def test_subject_word_boundaries(message, expected):
    assert message_signals(message) == expected


@pytest.mark.parametrize("message", ["fix(docs): link", "fix(deps): bump", "ci: fix build", "test: fix expectation"])
def test_v2_excludes_typed_maintenance(message):
    assert message_signals(message, exclude_maintenance=True) == (False, False)
    assert predict(tag="unknown", messages=[message], version="v2").corrective_release == "no"


def test_notes_count_entries_not_section_titles_or_repeated_words():
    assert note_signals("## Bug fixes\n- Avoid crash\n- Fix, fix, fix memory leak\n## Features\n- New API") == (2, 1)
    assert note_signals("## Bug fixes\n\n## Features\n") == (0, 0)
    assert note_signals("Fix crash\nImprove performance") == (1, 0)


def test_baseline_patch_or_commit_and_incomplete_context_is_explicit():
    result = predict(tag="2.3.1", previous_tag="2.3.0", interval_status="error")
    assert result.corrective_release == "yes" and not result.commit_context_complete
    assert predict(tag="not-semver", messages=["fix: crash"]).corrective_release == "yes"
    assert predict(tag="not-semver", body="Fix crash").corrective_release == "no"
    assert predict(tag="not-semver").corrective_release == "no"
    assert result.to_dict()["version"] == "v1"


def test_v2_handles_mixed_releases_and_notes_precedence():
    args = {"tag": "2.3.1", "previous_tag": "2.3.0", "version": "v2"}
    assert predict(**args, body="## Features\n- New API", messages=["fix: bug"]).corrective_release == "no"
    assert predict(**args, body="## Fixes\n- Crash\n- Leak\n## Features\n- API").corrective_release == "yes"
    assert predict(**args, body="- fix: bug\n- feat: api").corrective_release == "no"
    assert predict(**args, messages=["fix: bug", "fix: leak", "feat: api"]).corrective_release == "yes"
    assert predict(**args, messages=["fix: bug", "feat: api"]).corrective_release == "no"
    assert predict(**args, messages=["docs: wording"]).corrective_release == "yes"
    assert predict(tag="unknown", version="v2").corrective_release == "no"
    with pytest.raises(ValueError):
        predict(tag="2.3.1", version="invented")


def test_assignment_example_precision_recall_f1():
    # TP=30, FP=10, FN=20, TN=40 -> P=.75 R=.60 F1=2/3.
    truth = ["yes"] * 30 + ["no"] * 10 + ["yes"] * 20 + ["no"] * 40
    predicted = ["yes"] * 40 + ["no"] * 60
    result = scores(truth, predicted)
    assert (result["tp"], result["fp"], result["fn"], result["tn"]) == (30, 10, 20, 40)
    assert result["precision"] == pytest.approx(.75)
    assert result["recall"] == pytest.approx(.6)
    assert result["f1"] == pytest.approx(2 / 3)
    assert result["status"] == "needs_refinement"


def test_threshold_exact_and_undefined_metrics():
    # 14 TP, 6 FP, 6 FN -> F1=.70; aceitação inclusiva, sem arredondar.
    assert scores(["yes"] * 14 + ["no"] * 6 + ["yes"] * 6,
                  ["yes"] * 20 + ["no"] * 6)["status"] == "accepted"
    none = scores(["no"], ["no"])
    assert none["status"] == "unassessable_no_positive_consensus"
    assert not none["precision_defined"] and not none["recall_defined"] and not none["f1_defined"]
    missed = scores(["yes"], ["no"])
    assert missed["f1"] == 0 and missed["recall_defined"] and not missed["precision_defined"]
    for truth, predicted in [([], []), (["yes"], []), (["uncertain"], ["no"])]:
        with pytest.raises(ValueError):
            scores(truth, predicted)
