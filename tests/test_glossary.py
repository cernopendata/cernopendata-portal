import pytest

from cernopendata.modules.fixtures.cli import glossary


def test_glossary(app, database):
    print("Inserting all the glossary terms")
    try:
        glossary([], "insert-or-replace")
    except SystemExit:
        print("It is normal to raise a system exit exception")
