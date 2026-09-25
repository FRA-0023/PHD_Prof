import pytest
from slice_pdf import parse_page_range

def test_parse_page_range_single_and_ranges():
    range_str = "1-3, 5, 8-10"
    pages = parse_page_range(range_str, max_pages=15)
    assert pages == [1, 2, 3, 5, 8, 9, 10]

def test_parse_page_range_bounds():
    range_str = "0, 1-2, 20"
    pages = parse_page_range(range_str, max_pages=10)
    assert pages == [1, 2]

def test_parse_page_range_inverted():
    range_str = "5-3"
    pages = parse_page_range(range_str, max_pages=10)
    assert pages == [3, 4, 5]
