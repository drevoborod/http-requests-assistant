# import pytest
import pickle

from deepdiff import DeepDiff

from src.libs.core import StructureParser
from .data.parsed import PARSED_POSITIVE


def test_parse_structure():
    parser = StructureParser("tests/tests_core/data/structure.yml")
    result = parser._parse()
    diff = DeepDiff(result, PARSED_POSITIVE)
    assert not diff.to_dict()


def test_prepare_structure():
    parser = StructureParser()
    parser.parsed = PARSED_POSITIVE
    with open("tests/tests_core/data/structure.dump", "rb") as file:
        assert pickle.load(file) == parser.structure
