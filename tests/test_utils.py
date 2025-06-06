from myapp.utils import process_uploaded_file


def test_process_uploaded_file_returns_list_of_dicts():
    results = process_uploaded_file("fake_path.xlsx", "2024-12-01", "2024-12-31")
    assert isinstance(results, list)
    assert all(isinstance(item, dict) for item in results)


def test_process_uploaded_file_contains_expected_keys():
    results = process_uploaded_file("fake_path.xlsx", "2024-12-01", "2024-12-31")
    for row in results:
        assert "date" in row
        assert "job" in row
        assert "technician" in row


def test_process_uploaded_file_with_empty_file():
    results = process_uploaded_file("empty.xlsx", "2024-12-01", "2024-12-31")
    # simulate empty: you can later make the function actually return [] for real empty file
    assert isinstance(results, list)
