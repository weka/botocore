# Copyright 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import datetime
from tests import mock
import pytest
import itertools

from botocore.exceptions import MD5UnavailableError
from botocore.compat import (
    total_seconds, unquote_str, six, ensure_bytes, get_md5,
    compat_shell_split, get_tzinfo_options
)
from tests import BaseEnvVar, unittest


class TotalSecondsTest(BaseEnvVar):
    def test_total_seconds(self):
        delta = datetime.timedelta(days=1, seconds=45)
        remaining = total_seconds(delta)
        assert remaining == 86445.0

        delta = datetime.timedelta(seconds=33, microseconds=772)
        remaining = total_seconds(delta)
        assert remaining == 33.000772


class TestUnquoteStr(unittest.TestCase):
    def test_unquote_str(self):
        value = u'%E2%9C%93'
        # Note: decoded to unicode and utf-8 decoded as well.
        # This would work in python2 and python3.
        assert unquote_str(value) == u'\u2713'

    def test_unquote_normal(self):
        value = u'foo'
        # Note: decoded to unicode and utf-8 decoded as well.
        # This would work in python2 and python3.
        assert unquote_str(value) == u'foo'

    def test_unquote_with_spaces(self):
        value = u'foo+bar'
        # Note: decoded to unicode and utf-8 decoded as well.
        # This would work in python2 and python3.
        assert unquote_str(value) == 'foo bar'


class TestEnsureBytes(unittest.TestCase):
    def test_string(self):
        value = 'foo'
        response = ensure_bytes(value)
        assert isinstance(response, six.binary_type)
        assert response == b'foo'

    def test_binary(self):
        value = b'bar'
        response = ensure_bytes(value)
        assert isinstance(response, six.binary_type)
        assert response == b'bar'

    def test_unicode(self):
        value = u'baz'
        response = ensure_bytes(value)
        assert isinstance(response, six.binary_type)
        assert response == b'baz'

    def test_non_ascii(self):
        value = u'\u2713'
        response = ensure_bytes(value)
        assert isinstance(response, six.binary_type)
        assert response == b'\xe2\x9c\x93'

    def test_non_string_or_bytes_raises_error(self):
        value = 500
        with pytest.raises(ValueError):
            ensure_bytes(value)


class TestGetMD5(unittest.TestCase):
    def test_available(self):
        md5 = mock.Mock()
        with mock.patch('botocore.compat.MD5_AVAILABLE', True):
            with mock.patch('hashlib.md5', mock.Mock(return_value=md5)):
                assert get_md5() == md5

    def test_unavailable_raises_error(self):
        with mock.patch('botocore.compat.MD5_AVAILABLE', False):
            with pytest.raises(MD5UnavailableError):
                get_md5()


WINDOWS_SHELL_SPLIT_CASES = {
    r'': [],
    r'spam \\': [r'spam', '\\\\'],
    r'spam ': [r'spam'],
    r' spam': [r'spam'],
    'spam eggs': [r'spam', r'eggs'],
    'spam\teggs': [r'spam', r'eggs'],
    'spam\neggs': ['spam\neggs'],
    '""': [''],
    '" "': [' '],
    '"\t"': ['\t'],
    '\\\\': ['\\\\'],
    '\\\\ ': ['\\\\'],
    '\\\\\t': ['\\\\'],
    r'\"': ['"'],
    # The following four test cases are official test cases given in
    # Microsoft's documentation.
    r'"abc" d e': [r'abc', r'd', r'e'],
    r'a\\b d"e f"g h': [r'a\\b', r'de fg', r'h'],
    r'a\\\"b c d': [r'a\"b', r'c', r'd'],
    r'a\\\\"b c" d e': [r'a\\b c', r'd', r'e']
}


@pytest.mark.parametrize(
    "input_string, expected_output",
    WINDOWS_SHELL_SPLIT_CASES.items(),
)
def test_compat_shell_split_windows(input_string, expected_output):
    assert compat_shell_split(input_string, "win32") == expected_output


UNIX_SHELL_SPLIT_CASES = {
    r'': [],
    r'spam \\': [r'spam', '\\'],
    r'spam ': [r'spam'],
    r' spam': [r'spam'],
    'spam eggs': [r'spam', r'eggs'],
    'spam\teggs': [r'spam', r'eggs'],
    'spam\neggs': ['spam', 'eggs'],
    '""': [''],
    '" "': [' '],
    '"\t"': ['\t'],
    '\\\\': ['\\'],
    '\\\\ ': ['\\'],
    '\\\\\t': ['\\'],
    r'\"': ['"'],
    # The following four test cases are official test cases given in
    # Microsoft's documentation, but adapted to unix shell splitting.
    r'"abc" d e': [r'abc', r'd', r'e'],
    r'a\\b d"e f"g h': [r'a\b', r'de fg', r'h'],
    r'a\\\"b c d': [r'a\"b', r'c', r'd'],
    r'a\\\\"b c" d e': [r'a\\b c', r'd', r'e']
}


@pytest.mark.parametrize(
    "platform, test_case",
    itertools.product(["linux2", "darwin"], UNIX_SHELL_SPLIT_CASES.items()),
)
def test_compat_shell_split_unix(platform, test_case):
    input_string, expected_output = test_case
    assert compat_shell_split(input_string, platform) == expected_output


@pytest.mark.parametrize("platform", ["linux2", "darwin", "win32"])
def test_compat_shell_split_error(platform):
    with pytest.raises(ValueError):
        compat_shell_split(r'"', platform)


class TestTimezoneOperations(unittest.TestCase):
    def test_get_tzinfo_options(self):
        options = get_tzinfo_options()
        assert len(options) > 0

        for tzinfo in options:
            assert isinstance(tzinfo(), datetime.tzinfo)
