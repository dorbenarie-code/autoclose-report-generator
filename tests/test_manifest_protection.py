import pytest
import pandas as pd
from myapp.utils.manifest import add_report_to_manifest

def test_add_report_to_manifest_rejects_series(tmp_path):
    with pytest.raises(TypeError):
        add_report_to_manifest(
            df=pd.Series([1, 2, 3]),
            report_path=tmp_path / "dummy.json",
            report_type="draft",
            client_id="client123",
            tech_name="David"
        ) 