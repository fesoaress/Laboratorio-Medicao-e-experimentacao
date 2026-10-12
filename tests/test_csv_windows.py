"""Regressão portável do C long de 32 bits ao ler release notes extensas."""

import csv

import pytest

from src.gold_sample import read_csv
from src.pipeline import write_csv
from src.s02_audit import read_rows


@pytest.mark.parametrize("reader", [read_csv, read_rows])
def test_large_fields_do_not_overflow_windows_c_long(tmp_path, monkeypatch, reader):
    path = tmp_path / "large.csv"
    body = 'Release: correção, "aspas"\n' * 10_000
    write_csv(path, ("release_body",), [{"release_body": body}])
    original = csv.field_size_limit
    def windows_limit(value):
        if value > 2**31 - 1:
            raise OverflowError("Python int too large to convert to C long")
        return original(value)
    monkeypatch.setattr(csv, "field_size_limit", windows_limit)
    assert reader(path) == [{"release_body": body}]
