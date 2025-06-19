from myapp.utils.parsing_utils import process_uploaded_file
from myapp.dashboard.data_loader import load_kpi_data


def test_process_uploaded_file_returns_list_of_dicts() -> None:
    results = process_uploaded_file("fake_path.xlsx", "2024-12-01", "2024-12-31")
    assert isinstance(results, list)
    assert all(isinstance(item, dict) for item in results)


def test_process_uploaded_file_contains_expected_keys() -> None:
    results = process_uploaded_file("fake_path.xlsx", "2024-12-01", "2024-12-31")
    for row in results:
        assert "date" in row
        assert "job" in row
        assert "technician" in row


def test_process_uploaded_file_with_empty_file() -> None:
    results = process_uploaded_file("empty.xlsx", "2024-12-01", "2024-12-31")
    # simulate empty: you can later make the function actually return [] for real empty file
    assert isinstance(results, list)


def test_load_kpi_data() -> None:
    total_reports, active_techs, total_amount = load_kpi_data()
    assert total_reports >= 0
    assert active_techs >= 0
    assert total_amount >= 0.0
