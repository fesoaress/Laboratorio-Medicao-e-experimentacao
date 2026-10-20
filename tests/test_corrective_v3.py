import pytest

from src.corrective import change_entries, functional_notes, functional_signals, predict


@pytest.mark.parametrize("body,expected", [
    ("- Fixed crash\n- Added support\n- Updated theme", "no"),
    ("- Fixed crash\n- Fix leak\n- Added support", "yes"),
    ("- Fixed crash\n- Other change", "no"),
    ("## Bugfixes\n- Crash\n- Leak\n## Features\n- Widget", "yes"),
    ("## Fixes\n- docs: fix typo\n- fix(ci): pipeline", "no"),
    ("## Changes\n1. Fixed crash\n2. Fixed leak", "yes"),
    ("Fixed a crash", "yes"),
    ("## New Contributors\n- fix: username", "no"),
])
def test_v3_predominance_uses_all_changes(body, expected):
    assert predict(tag="v1.2.3", previous_tag="v1.2.2", body=body, version="v3").corrective_release == expected


def test_v3_ignores_code_and_footer_without_ignoring_real_changes():
    text = "<!-- generated -->\n```\n- fix fake\n```\n- Fixed crash\n**Full Changelog**: https://example.org/fix\nhttps://example.org/fix"
    assert change_entries(text) == [True]
    assert predict(tag="x", body=text, version="v3").note_change_entries == 1


def test_v3_notes_with_real_noncorrective_changes_override_commits_and_patch():
    p = predict(tag="v1.0.2", previous_tag="v1.0.1", body="- Added a widget", messages=["fix: crash"], version="v3")
    assert p.corrective_release == "no" and p.reason == "notes_majority_all_changes"
    assert p.note_change_entries == p.commit_change_entries == 1


def test_v3_commit_denominator_and_no_semver_only_fallback():
    assert predict(tag="v1.0.2", previous_tag="v1.0.1", version="v3").corrective_release == "no"
    assert predict(tag="x", messages=["fix: crash", "Add widget", "Update theme"], version="v3").corrective_release == "no"
    p = predict(tag="x", messages=["Merge branch main", "docs: fix typo", "fix: crash", "fix: leak", "Add widget", ""], version="v3")
    assert p.corrective_release == "yes" and p.commit_change_entries == 3


def test_v4_maintenance_and_release_administration_are_not_functional_changes():
    text = "## Changes\n- abc1234 fix: crash\n- def5678 docs: example\n- 123abcd refactor: cleanup\n- Released 3.0.2\n## Dependency Updates\n- Bump tool\n## Bug Fixes\n- Leak"
    assert change_entries(text, ignore_maintenance=True) == [True, True]
    assert predict(tag="x", body=text, version="v4").corrective_release == "yes"
    assert predict(tag="x", messages=["fix: crash", "refactor: cleanup"], version="v4").corrective_release == "yes"
    assert predict(tag="x", body="- Fix crash\n- New widget\n- Unknown functional change", version="v4").corrective_release == "no"


def test_v5_general_feature_verbs_compete_with_fixes():
    for text in ("Added support for widget", "Introduce API", "New command", "Improvements"):
        assert functional_signals(text) == (False, True)
    assert functional_signals("fix: added handling for crash") == (True, False)
    assert functional_signals("abc1234 docs: fix typo") == (False, False)
    assert functional_notes("## Fixes\n- Crash\n## New Features\n- Widget\n## New Contributors\n- fix bogus") == (1, 1)
    assert functional_notes("```\n- Fix fake\n```\n<!-- generated -->\n- Fixed crash\n**Full Changelog**: URL") == (1, 0)
    assert predict(tag="v1.2.3", previous_tag="v1.2.2", version="v5").corrective_release == "no"
    assert predict(tag="x", body="- Fix crash\n- Added API\n- Support format", version="v5").corrective_release == "no"
    assert predict(tag="x", body="## Fixes\n- docs: fix typo\n- Fix crash", version="v5").corrective_release == "yes"
