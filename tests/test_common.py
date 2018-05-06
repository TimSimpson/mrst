import pytest

from mrst import common


def test_split_args():
    assert [] == common._split_args('')
    assert [] == common._split_args('  ')
    assert ['a'] == common._split_args('a')
    assert ['a', 'b'] == common._split_args('a b')
    assert ['blah', '=', 'hello'] == common._split_args('blah = hello')
    assert ['blah', '=', 'hello'] == common._split_args('blah=hello')
    assert ['blah', '=', 'hello'] == common._split_args('blah= hello')
    assert ['blah', '=', 'hello'] == common._split_args('blah =hello')
    assert ['blah', '=', 'hello'] == common._split_args('blah="hello"')
    assert ['blah', '=', 'hello'] == common._split_args('blah = "hello"')
    assert (['blah', '=', 'hello! I said "hello"'] ==
            common._split_args('blah = "hello! I said \\"hello\\""'))


def get_default_args():
    return {
        'input_file': 'file',
        'indent': None,
        'section': None,
        'start': None,
        'start_after': None,
        'end': None,
        'end_before': None,
    }


class TestParseIncludeFileArgs:

    def test_when_insufficient_args(self):
        with pytest.raises(ValueError):
            common.parse_include_file_args('')

    def test_with_defaults(self):
        args = common.parse_include_file_args('"file"')
        expected = get_default_args()
        assert args == expected

    def test_with_positional_args(self):
        args = common.parse_include_file_args('"file" 0 ~ 4')
        expected = get_default_args()
        expected.update({
            'indent': 4,
            'start': 0,
        })
        assert args == expected

    def test_keyword_arg(self):
        args = common.parse_include_file_args('"file" 0 ~ 8 section = "~"')
        expected = get_default_args()
        expected.update({
            'indent': 8,
            'section': '~',
            'start': 0,

        })
        assert args == expected

    def test_keyword_arg_2(self):
        args = common.parse_include_file_args(
            '"file" 0 ~ 8 section = "~" start_after = "The fine feathered '
            'friends of \\"Bird Beach\\""')
        expected = get_default_args()
        expected.update({
            'indent': 8,
            'section': '~',
            'start_after': 'The fine feathered friends of "Bird Beach"',
            'start': 0,
        })
        assert args == expected
