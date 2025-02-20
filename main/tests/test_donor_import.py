# -*- coding: utf-8 -*-

from email.header import Header
from email.message import Message
from io import StringIO

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

from main.models import Donor
from main.management.commands.donor_import import Command


command = Command()


def test_parse_subject():
    assert command.parse_subject('garbage') is None

    # Valid
    valid = 'Receipt [$25.00] By: John Doe [john.doe@archlinux.org]'
    output = command.parse_subject(valid)
    assert output == 'John Doe'


def test_parse_name():
    assert command.sanitize_name('1244') == ''
    assert command.sanitize_name('John Doe') == 'John Doe'
    assert command.sanitize_name(' John Doe ') == 'John Doe'
    assert command.sanitize_name('John Doe 23') == 'John Doe'


def test_decode_subject():
    text = u'メイル'
    subject = Header(text, 'utf-8')
    assert command.decode_subject(subject) == text


def test_invalid_args(monkeypatch):
    monkeypatch.setattr('sys.stdin', StringIO(''))
    with pytest.raises(CommandError) as e:
        call_command('donor_import')
    assert 'Failed to read from STDIN' in str(e.value)


def test_invalid_path():
    with pytest.raises(CommandError) as e:
        call_command('donor_import', '/tmp/non-existant')
    assert 'argument input: can\'t open' in str(e.value)


def test_maildir(db, monkeypatch):
    msg = Message()
    msg['subject'] = 'John Doe'
    msg['to'] = 'John Doe <john@doe.com>'

    # Invalid
    monkeypatch.setattr('sys.stdin', StringIO(msg.as_string()))
    with pytest.raises(SystemExit):
        call_command('donor_import')
    assert len(Donor.objects.all()) == 0

    # # Valid
    msg = Message()
    msg['subject'] = 'Receipt [$25.00] By: David Doe [david@doe.com]'
    msg['to'] = 'John Doe <david@doe.com>'
    monkeypatch.setattr('sys.stdin', StringIO(msg.as_string()))
    call_command('donor_import')
    assert len(Donor.objects.all()) == 1

    # # Re-running should result in no new donor
    monkeypatch.setattr('sys.stdin', StringIO(msg.as_string()))
    call_command('donor_import')
    assert len(Donor.objects.all()) == 1
