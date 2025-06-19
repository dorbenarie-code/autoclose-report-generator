import pytest
import pandas as pd
from myapp.utils.report_utils import create_and_email_report

def test_create_and_email_report_rejects_series():
    with pytest.raises(TypeError):
        create_and_email_report(pd.Series([1,2,3]), client="X", tech="Y") 