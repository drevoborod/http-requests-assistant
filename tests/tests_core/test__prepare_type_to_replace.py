import pytest

from src.libs.core import _prepare_type_to_replace
from src.libs.structure import TypeNames


class TestDataFromTextAreaWithType:
    def test_string_type(self):
        data_type = TypeNames.string.value
        data = "some string"
        result = _prepare_type_to_replace(data, data_type)
        assert result == data

    def test_integer_type(self):
        data_type = TypeNames.number.value
        data = "12345"
        result = _prepare_type_to_replace(data, data_type)
        assert result == 12345

    @pytest.mark.parametrize(
        "data,expected",
        (["true", True], ["false", False],
        ["True", True], ["False", False],
        ["tRUe", True], ["fAlSe", False],
        ["tRUe", True], ["fAlSe", False])
    )
    def test_boolean_type(self, data, expected):
        data_type = TypeNames.boolean.value
        result = _prepare_type_to_replace(data, data_type)
        assert result == expected

    def test_boolean_type_wrong_data(self):
        data_type = TypeNames.boolean.value
        data = "sdfdf"      # any string that cannot be interpreted as containing boolean, e.g. not "true" or "faLse"
        with pytest.raises(ValueError) as err:
            _prepare_type_to_replace(data, data_type)
        assert str(err.value) == f"Incorrect value for boolean type: {data}"


class TestDataFromTextAreaWithoutType:
    provided_type = TypeNames.empty.value

    def test_expected_string(self):
        data = "abrakadabra"
        result = _prepare_type_to_replace(data, self.provided_type)
        assert result == data

    def test_expected_number(self):
        data = "12345"
        result = _prepare_type_to_replace(data, self.provided_type)
        assert result == 12345

    @pytest.mark.parametrize("data,expected", (
        ["true", True], ["false", False],
        ["True", True], ["False", False],
        ["trUE", True], ["fALse", False],
        ["some text", "some text"]      # just in case :)
    ))
    def test_expected_boolean(self, data, expected):
        result = _prepare_type_to_replace(data, self.provided_type)
        assert result == expected


class TestDataFromChoicesWithType:
    @pytest.mark.parametrize("data,expected", (
        ["true", "true"],
        [True, "True"],
        [False, "False"],
        ["123", "123"],
        ["букаффки", "букаффки"],
        [123, "123"],
        [None, "None"],
        ["None", "None"],
        ["null", "null"]
    ))
    def test_string_type(self, data, expected):
        data_type = TypeNames.string.value
        result = _prepare_type_to_replace(data, data_type)
        assert result == expected

    @pytest.mark.parametrize("data,expected", (
        [1234, 1234],
        ["1234", 1234],
        [False, 0]
    ))
    def test_integer_type(self, data, expected):
        data_type = TypeNames.number.value
        result = _prepare_type_to_replace(data, data_type)
        assert result == expected

    @pytest.mark.parametrize("data", (
        "aaaa", None
    ))
    def test_integer_type_data_mismatch(self, data):
        """Case when user expects integer type but provides data of another type."""
        data_type = TypeNames.number.value
        with pytest.raises(ValueError):
            _prepare_type_to_replace(data, data_type)

    @pytest.mark.parametrize(
        "data,expected",
        (
            [True, True],
            [False, False]
        )
    )
    def test_boolean_type(self, data, expected):
        data_type = TypeNames.boolean.value
        result = _prepare_type_to_replace(data, data_type)
        assert result == expected

    @pytest.mark.parametrize("data", [
        "aaa", None, 123
    ])
    def test_boolean_type_mismatch(self, data):
        data_type = TypeNames.boolean.value
        with pytest.raises(ValueError):
            _prepare_type_to_replace(data, data_type)


class TestDataFromChoicesWithoutType:
    provided_type = TypeNames.empty.value

    @pytest.mark.parametrize(
        "data,expected",
        (
            [True, True],
            [None, None],
            [123, 123]
        )
    )
    def test_non_string(self, data, expected):
        result = _prepare_type_to_replace(data, self.provided_type)
        assert result == expected