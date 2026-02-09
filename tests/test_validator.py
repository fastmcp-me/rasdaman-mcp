#!/usr/bin/env python3
"""Test script for WCPS query validator"""

import pytest
from src.rasdaman_actions import RasdamanActions


@pytest.mark.parametrize(
    "query, expected",
    [
        # Valid queries
        ("for $c in (test) return $c[Lat(0:10), Lon(0:10)]", "VALID"),
        ("for $c in (test) return encode($c, \"image/png\")", "VALID"),
        ("for $c in (test) let $x := 5 return $c[Lat(0:10)]", "VALID"),
        ("for $c in (test) where $c > 0 return $c + 4", "VALID"),
        # Invalid queries
        ("for $c in (test where $c", "INVALID SYNTAX"),
        ("for $c in (test) return encode($c, 'image/png')", "INVALID SYNTAX"),
        ("for $c in (test return", "INVALID SYNTAX"),
        ("invalid wcps query", "INVALID SYNTAX"),
    ],
)
def test_wcps_validator(query: str, expected: str):
    ras_actions = RasdamanActions("", "", "")
    result = ras_actions.validate_wcps_query_action(query)

    assert result.startswith(expected), (
        f"Query: {query}\n"
        f"Expected: {expected}*\n"
        f"Got:      {result}"
    )
