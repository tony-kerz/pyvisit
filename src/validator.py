import ast

from src._logging import logging

# from astpretty import pprint

log = logging.getLogger(__name__)

rules = {
    'noAliasModules': [
        'airflow'
    ]
}


def validate(content, rules={}):
    visitor = Visitor(rules)
    visitor.visit(ast.parse(content))
    return visitor.items


class Visitor(ast.NodeVisitor):
    items = []

    def __init__(self, rules):
        self.rules = rules
        print(rules)
        self.items.append('flo')

    def visit_Call(self, node):
        func = node.func
        print(f'func-type={type(func)}: {ast.dump(func)}')
        # name = func.id if isinstance(func, ast.Name) else func.value.id
        # print(f'call={name}')
        # if name == 'DAG':
        #    _pprint(node)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if (node.module == 'airflow'):
            for name in node.names:
                if (name.name == 'DAG') and name.asname:
                    print(f'trying to alias DAG are we? {ast.dump(node)}')

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Name):
            if node.value.id == 'DAG':
                print(f'trying to assign DAG are we? {ast.dump(node)}')
