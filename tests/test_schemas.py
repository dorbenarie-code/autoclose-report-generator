def test_input_row_parsing() -> None:
    from myapp.utils.schemas import InputRow
    row = InputRow(date="2025-06-10", total="200.00", parts="50")
    assert row.tech_profit == 75
    assert row.date.year == 2025
