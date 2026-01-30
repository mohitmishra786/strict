import pytest
from strict.integrity.io import InputValidator


def test_parse_csv():
    csv_data = "name,value\ntest,10\nother,20"
    result = InputValidator.parse_csv(csv_data)
    assert len(result) == 2
    assert result[0]["name"] == "test"
    assert result[0]["value"] == "10"


def test_parse_xml():
    xml_data = "<root><item>test</item><value>10</value></root>"
    result = InputValidator.parse_xml(xml_data)
    assert result["root"]["item"] == "test"
    assert result["root"]["value"] == "10"


def test_parse_xml_nested():
    xml_data = "<root><item><a>1</a><b>2</b></item></root>"
    result = InputValidator.parse_xml(xml_data)
    assert result["root"]["item"]["a"] == "1"
    assert result["root"]["item"]["b"] == "2"
