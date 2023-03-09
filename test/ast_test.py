import ast
from astpretty import pprint


def test_import_star():
    lines = [
        'from os import *'
    ]

    pprint(ast.parse(join(lines)), show_offsets=False)


# helpers

def join(lines):
    return '\n'.join(lines)
