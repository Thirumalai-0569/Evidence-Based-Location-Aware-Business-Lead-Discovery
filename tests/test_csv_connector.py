import pytest
from backend.connectors.csv_connector import load_approved_csv, load_approved_csv_bytes

def test_headers_are_case_and_space_insensitive():
    rows = load_approved_csv_bytes(b" Name , Latitude,LONGITUDE,Category\nABC School,12.9,79.1,Education\n")
    assert len(rows) == 1
    assert rows[0]["name"] == "ABC School" and rows[0]["category"] == "Education"

def test_utf8_bom_and_defaults():
    rows = load_approved_csv_bytes("\ufeffname,latitude,longitude\nXYZ,1,2\n".encode("utf-8"))
    assert rows[0]["category"] == "Unknown" and rows[0]["source"] == "Approved CSV Dataset"

def test_invalid_rows_are_skipped():
    data = b"name,latitude,longitude\nGood,10,20\n,10,20\nBadLat,95,20\nNotNumber,abc,20\nBadLon,10,200\n"
    assert [r["name"] for r in load_approved_csv_bytes(data)] == ["Good"]

def test_missing_required_columns_raises():
    with pytest.raises(ValueError, match="latitude"):
        load_approved_csv_bytes(b"name,longitude\nA,1\n")

def test_non_utf8_is_a_clear_error():
    with pytest.raises(ValueError, match="UTF-8"):
        load_approved_csv_bytes(b"name,latitude,longitude\n\xff\xfe,1,2\n")

def test_path_loader_matches_bytes_loader(tmp_path):
    p = tmp_path / "d.csv"
    p.write_bytes(b"Name,Latitude,Longitude\nA,1,2\n")
    assert load_approved_csv(str(p)) == load_approved_csv_bytes(p.read_bytes())
