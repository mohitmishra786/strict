import csv
import io
from typing import Any

from defusedxml.ElementTree import parse as parse_xml


class InputValidator:
    """Validator for various input formats."""

    @staticmethod
    def parse_csv(data: str) -> list[dict[str, str]]:
        """Parse CSV string safely."""
        f = io.StringIO(data)
        reader = csv.DictReader(f)
        return list(reader)

    @staticmethod
    def parse_xml(data: str) -> dict[str, Any]:
        """Parse XML string safely."""
        # This is a simplified XML to Dict parser
        tree = parse_xml(io.StringIO(data))
        root = tree.getroot()
        if root is None:
            return {}
        return {root.tag: InputValidator._xml_element_to_dict(root)}

    @staticmethod
    def _xml_element_to_dict(elem) -> dict[str, Any] | str:
        """Recursive helper for XML parsing."""
        if len(elem) == 0:
            return elem.text or ""

        result = {}
        for child in elem:
            child_data = InputValidator._xml_element_to_dict(child)
            if child.tag in result:
                if isinstance(result[child.tag], list):
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = [result[child.tag], child_data]
            else:
                result[child.tag] = child_data
        return result
