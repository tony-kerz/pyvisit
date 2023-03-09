from astpretty import pprint

from src.visitor import *


def test_no_alias_pass():
    issues = visit(
        'from os import environ',
        {
            MODULES: {
                'os': {
                    NO_ALIAS: True
                }
            }
        }
    )

    assertPass(issues)


def test_no_alias_fail():
    src = 'from os import environ as _environ'

    issues = visit(
        src,
        {
            MODULES: {
                'os': {
                    NO_ALIAS: True
                }
            }
        }
    )

    assertFail(issues, rule=f'{MODULES}.os.{NO_ALIAS}')
    assert issues[0]['source'] == src


def test_no_alias_twice_fail():
    lines = [
        'from os import environ as _environ',
        'from os import environ as __environ',
    ]

    issues = visit(
        join(lines),
        {
            MODULES: {
                'os': {
                    NO_ALIAS: True
                }
            }
        }
    )

    assertFail(issues, 2, rule=f'{MODULES}.os.{NO_ALIAS}')
    assert issues[0]['source'] == lines[0]
    assert issues[1]['source'] == lines[1]


def test_no_assign_pass():
    lines = [
        'from os import environ',
        'a = 1'
    ]

    issues = visit(
        join(lines),
        {
            VALUES: {
                'environ': {
                    NO_ASSIGN: True
                }
            }
        }
    )

    assertPass(issues)


def test_no_assign_fail():
    lines = [
        'from os import environ',
        'a = environ'
    ]

    issues = visit(
        join(lines),
        {
            VALUES: {
                'environ': {
                    NO_ASSIGN: True
                }
            }
        }
    )

    assertFail(issues, rule=f'{VALUES}.environ.{NO_ASSIGN}')
    assert issues[0]['source'] == lines[1]


def test_call_required_pass():
    lines = [
        'from .funky import funky',
        "funky(stuff='foo')"
    ]

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {}
                    }
                }
            }
        }
    )

    assertPass(issues)


def test_call_required_fail():
    lines = [
        'from .content.funky import funky',
        "funky(beats=True)"
    ]

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {}
                    }
                }
            }
        }
    )

    assertFail(issues, rule=f'{CALLS}.funky.{KEYWORDS}.stuff.{IS_REQUIRED}')


def test_call_match_pass():
    lines = [
        'from .content.funky import funky',
        "funky(stuff='foo')"
    ]

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            MATCH: '^foo$'
                        }
                    }
                }
            }
        }
    )

    assertPass(issues)


def test_validator_pass():
    lines = [
        'from .content.funky import funky',
        "funky(stuff='foo')"
    ]

    def validate():
        return None

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            VALIDATOR: validate
                        }
                    }
                }
            }
        }
    )

    assertPass(issues)


def test_validator_fail():
    lines = [
        'from .content.funky import funky',
        "funky(stuff='foo')"
    ]

    def validate():
        return 'oh no u did not!'

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            VALIDATOR: validate
                        }
                    }
                }
            }
        }
    )

    assertFail(issues)


def test_validator_context_pass():
    lines = [
        'from .content.funky import funky',
        "funky(stuff='foo')"
    ]

    def validate(value, context):
        expected = context.get('required-value-for-funky.stuff')
        if (expected != value):
            return f'expected={expected}, actual={value}'

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            VALIDATOR: validate
                        }
                    }
                }
            }
        },
        {
            'required-value-for-funky.stuff': 'foo'
        }
    )

    assertPass(issues)


def test_validator_context_fail():
    lines = [
        'from .content.funky import funky',
        "funky(stuff='foo')"
    ]

    def validate(value, context):
        expected = context.get('required-value-for-funky.stuff')
        if (expected != value):
            return f'expected={expected}, actual={value}'

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            VALIDATOR: validate
                        }
                    }
                }
            }
        },
        {
            'required-value-for-funky.stuff': 'bar'
        }
    )

    assertFail(issues)


def test_validator_context_complex_pass():
    lines = [
        'from datetime import datetime',
        'from .content.funky import funky',
        "funky(stuff=f'foo.{datetime.now()}')"
    ]

    def validate(value, context):
        expected = context.get('required-value-for-funky.stuff')
        _re = f'^{expected}\..*$'
        if not re.match(_re, value):
            return f'expected-match={_re}, actual={value}'

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            VALIDATOR: validate
                        }
                    }
                }
            }
        },
        {
            'required-value-for-funky.stuff': 'foo'
        }
    )

    assertPass(issues)


def test_validator_context_complex_fail():
    lines = [
        'from datetime import datetime',
        'from .content.funky import funky',
        "funky(stuff=f'bar.{datetime.now()}')"
    ]

    def validate(value, context):
        expected = context.get('required-value-for-funky.stuff')
        _re = f'^{expected}\..*$'
        if not re.match(_re, value):
            return f'expected-match={_re}, actual={value}'

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            VALIDATOR: validate
                        }
                    }
                }
            }
        },
        {
            'required-value-for-funky.stuff': 'foo'
        }
    )
    assertFail(issues)


def test_validator_context_dict_pass():
    lines = [
        'from .content.funky import funky',
        "funky(stuff={key1: 'foo'})"
    ]

    def validate(value, context):
        expected = context.get('required-value-for-funky.stuff.key1')
        _value = value.get('key1')
        if (expected != _value):
            return f'expected={expected}, actual={_value}'

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            TYPE: ast.Dict,
                            VALIDATOR: validate
                        }
                    }
                }
            }
        },
        {
            'required-value-for-funky.stuff.key1': 'foo'
        }
    )
    assertPass(issues)


def test_validator_context_dict_type_fail():
    lines = [
        'from .content.funky import funky',
        "funky(stuff='foo')"
    ]

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            TYPE: ast.Dict
                        }
                    }
                }
            }
        }
    )

    assertFail(issues)


def test_validator_context_dict_key_fail():
    lines = [
        'from .content.funky import funky',
        "funky(stuff={key1: 'bar'})"
    ]

    is_called = False

    def validate(value, context):
        is_called = True
        expected = context.get('required-value-for-funky.stuff.key1')
        if (expected != value):
            return f'expected={expected}, actual={value}'

    issues = visit(
        join(lines),
        {
            CALLS: {
                'funky': {
                    KEYWORDS: {
                        'stuff': {
                            TYPE: ast.Dict,
                            KEYS: {
                                'key1': {
                                    VALIDATOR: validate
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            'required-value-for-funky.stuff.key1': 'foo'
        }
    )

    assert is_called
    assertPass(issues)


# helpers
#

def join(lines):
    return '\n'.join(lines)


def visit(source, rules, context={}):
    visitor = Visitor(rules, context=context)
    visitor.visit(ast.parse(source))
    return visitor.issues


def _print(issue, pretty=False):
    indent(f'rule={issue.rule}')
    indent(f'source=[{issue.source}]')
    extra = issue.extra
    if extra:
        indent(f'extra=[{extra}]')
    if pretty:
        pprint(issue.node, show_offsets=False)
    else:
        indent(f'node={ast.dump(issue.node)}')


def indent(s):
    print(f'  {s}')


def report(issues, pretty=False):
    for i, issue in enumerate(issues):
        print(f'issues[{i}]: ')
        _print(issue, pretty)


def assertFail(issues, count=1, rule=None):
    assert len(issues) == count
    if rule:
        assert issues[0].rule == rule
    report(issues)


def assertPass(issues):
    assert len(issues) == 0
