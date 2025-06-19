import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytest

import myapp.utils.manifest as manifest_module
from myapp.utils.manifest import add_report_to_manifest, get_total


def make_sample_df(with_totals: bool = True) -> pd.DataFrame:
    # Create DataFrame with or without Totals row
    if with_totals:
        # First row is Totals
        return pd.DataFrame([
            {"job_id": "Totals:2", "total": 300.0},
            {"job_id": "A1", "total": 100.0},
            {"job_id": "B2", "total": 200.0},
        ])
    else:
        return pd.DataFrame([
            {"job_id": "A1", "total": 100.0},
            {"job_id": "B2", "total": 200.0},
        ])


def test_add_report_creates_manifest(tmp_path):
    # Prepare
    manifest_path = tmp_path / "manifest.json"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("DUMMY", "unused")
    monkeypatch.setattr(manifest_module, 'MANIFEST_PATH', manifest_path)

    df = make_sample_df()
    report_path = tmp_path / "report1.pdf"
    # Meta data
    meta = {"client_id": "C1", "tech_name": "T1", "report_type": "R1"}

    # Act
    add_report_to_manifest(df=df, report_path=report_path, report_type=meta["report_type"], client_id=meta["client_id"], tech_name=meta["tech_name"])

    # Assert manifest file exists
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert isinstance(data, list) and len(data) == 1
    entry = data[0]
    # Filename and path
    assert entry['filename'] == 'report1.pdf'
    assert entry['path'] == str(report_path)
    # created_at in ISO format ending with Z
    assert entry['created_at'].endswith('Z')
    # rows should exclude Totals row
    assert entry['rows'] == 2
    # total sum of 'total' column
    assert entry['total'] == pytest.approx(300.0)
    # meta fields
    assert entry['client_id'] == 'C1'
    assert entry['tech_name'] == 'T1'
    assert entry['report_type'] == 'R1'

    monkeypatch.undo()


def test_duplicate_entry_skipped(tmp_path, caplog):
    manifest_path = tmp_path / "manifest.json"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(manifest_module, 'MANIFEST_PATH', manifest_path)

    df = make_sample_df(with_totals=False)
    report_path = tmp_path / "report2.pdf"
    meta = {}

    # First addition
    add_report_to_manifest(df=df, report_path=report_path, report_type=meta.get("report_type", ""), client_id=meta.get("client_id", ""), tech_name=meta.get("tech_name", ""))
    # Second addition: duplicate
    caplog.set_level('INFO')
    add_report_to_manifest(df=df, report_path=report_path, report_type=meta.get("report_type", ""), client_id=meta.get("client_id", ""), tech_name=meta.get("tech_name", ""))

    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert len(data) == 1, "Duplicate entry should not be added"
    # Check log message
    assert any("Manifest already contains entry" in rec.message for rec in caplog.records)

    monkeypatch.undo()


def test_empty_dataframe_raises(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(manifest_module, 'MANIFEST_PATH', manifest_path)

    with pytest.raises(ValueError) as exc:
        add_report_to_manifest(df=pd.DataFrame(), report_path=tmp_path / "r.pdf", report_type="", client_id="", tech_name="")
    assert "DataFrame is empty" in str(exc.value)

    monkeypatch.undo()


def test_invalid_report_path_type(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(manifest_module, 'MANIFEST_PATH', manifest_path)

    df = make_sample_df(with_totals=False)
    with pytest.raises(ValueError) as exc:
        add_report_to_manifest(df=df, report_path="not_a_path", report_type="", client_id="", tech_name="")
    assert "report_path must be a pathlib.Path" in str(exc.value)

    monkeypatch.undo()


def test_malformed_manifest_raises(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    # Write malformed content
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"bad": "data"}), encoding='utf-8')

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(manifest_module, 'MANIFEST_PATH', manifest_path)

    df = make_sample_df()
    with pytest.raises(ValueError) as exc:
        add_report_to_manifest(df=df, report_path=tmp_path / "report3.pdf", report_type="", client_id="", tech_name="")
    assert "Malformed manifest.json" in str(exc.value)

    monkeypatch.undo()


def test_get_total_rejects_series():
    series = pd.Series([100, 200, 300], name="total")
    with pytest.raises(TypeError):
        get_total(df=series)
