import ast
import inspect
import re
import astor
import pydash as _

#from src._logging import logging
import logging

MODULES = 'modules'
NO_ALIAS = 'no-alias'
CALLS = 'calls'
KEYWORDS = 'keywords'
VALUES = 'values'
NO_ASSIGN = 'no-assign'
IS_REQUIRED = 'is-required'
TYPE = 'type'
VALIDATOR = 'validator'
MATCH = 'match'
KEYS = 'keys'

log = logging.getLogger(__name__)


class Visitor(ast.NodeVisitor):

    def __init__(self, rules, context={}):
        self.issues = []
        self.rules = rules
        self.setContext(context)

    def setContext(self, context):
        self.context = context
        log.info(f'context={context}')

    def append(self, rule, node, extra=None):
        self.issues.append(Issue(rule, astor.to_source(node).strip(), node, extra))

    def visit_Call(self, node):
        func = node.func
        print(f'func-type={type(func)}: {ast.dump(func)}')
        if isinstance(func, ast.Name):
            rule = f'{CALLS}.{func.id}.{KEYWORDS}'
            keyRules = _.get(self.rules, rule, {})
            if len(keyRules):
                for key in keyRules:
                    _rule = f'{rule}.{key}'
                    keyRule = keyRules[key]
                    keyword = _.find(node.keywords, lambda k: k.arg == key)
                    if keyword:
                        _type = keyRule.get(TYPE)
                        if _type and not isinstance(keyword.value, _type):
                            extra = f'{TYPE}: expected={self.type(_type)}, actual={self.type(keyword.value)}'
                            self.append(f'{_rule}.{TYPE}', node, extra)
                        else:
                            validator = keyRule.get(VALIDATOR)
                            if validator:
                                status = self.callValidator(validator, keyword)
                                if status:
                                    self.append(f'{_rule}.{VALIDATOR}', node, status)
                            match = keyRule.get(MATCH)
                            if match and not re.match(match, self.getValue(keyword)):
                                extra = f'{MATCH}: expected={match}, actual={self.getValue(keyword)}'
                                self.append(f'{_rule}.{MATCH}', node, extra)

                    elif keyRule.get(IS_REQUIRED, True):
                        self.append(f'{_rule}.{IS_REQUIRED}', node)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        rule = f'{MODULES}.{node.module}.{NO_ALIAS}'
        if _.get(self.rules, rule, False):
            for name in node.names:
                if name.asname:
                    self.append(rule, node)

        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Name):
            rule = f'{VALUES}.{node.value.id}.{NO_ASSIGN}'
            if _.get(self.rules, rule, default=False):
                self.append(rule, node)

        self.generic_visit(node)

    def getValue(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.JoinedStr):
            return _.reduce_(
                node.values,
                lambda res, v: f"{res}{v.value if isinstance(v, ast.Constant) else '*'}",
                ''
            )
        elif isinstance(node, ast.Dict):
            dict = {}
            keys = node.keys
            for i in range(len(keys)):
                dict[self.getValue(keys[i])] = self.getValue(node.values[i])
            return dict
        else:
            log.info(f'node={ast.dump(node)}')
            raise Exception(f'unhandled node type={type(node)}')

    def callValidator(self, validator, node):
        # fancy way of having validator not have to define args it doesn't need
        #
        args = inspect.getfullargspec(validator).args
        _args = {
            'value': self.getValue(node.value),
            'context': self.context,
            'node': node
        }
        picked = _.pick(_args, args)
        log.info(f"calling validator={validator.__name__}, value={_args.get('value')}")
        return validator(**picked)

    def type(self, thing):
        klass = thing if isinstance(thing, type) else type(thing)
        return klass.__name__

    # def report(self):
    #     for i, issue in enumerate(self.issue):
    #         print(f"[{i}]: rule={item['rule']}")
    #         print(f"source={item['source']}")
    #         extra = item['extra']
    #         if extra:
    #             print(f"extra={item['extra']}")
    #         print(f"node={ast.dump(item['node'])}")


class Issue:
    def __init__(self, rule, source, node, extra=None):
        self.rule = rule
        self.source = source
        self.node = node
        self.extra = extra
