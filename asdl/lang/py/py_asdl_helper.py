# coding=utf-8

import sys

from asdl.asdl_ast import RealizedField, AbstractSyntaxNode, SyntaxToken


# from https://stackoverflow.com/questions/15357422/python-determine-if-a-string-should-be-converted-into-int-or-float
def isfloat(x):
    try:
        a = float(x)
    except ValueError:
        return False
    else:
        return True


def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def python_ast_to_asdl_ast(py_ast_node, grammar):

    def get_subtree(py_ast_node, next_available_id):
        # node should be composite
        py_node_name = type(py_ast_node).__name__
        # assert py_node_name.startswith('_ast.')

        node_id = next_available_id
        next_available_id += 1

        production = grammar.get_prod_by_ctr_name(py_node_name)

        fields = []
        for field in production.fields:
            field_value = getattr(py_ast_node, field.name)
            asdl_field = RealizedField(field)
            if field.cardinality == 'single' or field.cardinality == 'optional':
                if field.cardinality == 'single' and field_value is None:
                    # likely the actual value is a python None
                    field_value = 'None'

                if field_value is not None:  # sometimes it could be 0
                    if grammar.is_composite_type(field.type):
                        child_node, next_available_id = get_subtree(field_value, next_available_id)
                        asdl_field.add_value(child_node)
                    else:
                        # asdl_field.add_value(str(field_value))
                        token = SyntaxToken(field.type, str(field_value), id=next_available_id)
                        asdl_field.add_value(token)
                        next_available_id += 1
            # field with multiple cardinality
            elif field_value is not None:
                if grammar.is_composite_type(field.type):
                    for val in field_value:
                        child_node, next_available_id = get_subtree(val, next_available_id)
                        asdl_field.add_value(child_node)
                else:
                    for val in field_value:
                        # asdl_field.add_value(str(val))
                        token = SyntaxToken(field.type, str(val), id=next_available_id)
                        asdl_field.add_value(token)
                        next_available_id += 1

            fields.append(asdl_field)

        asdl_node = AbstractSyntaxNode(production, realized_fields=fields, id=node_id)

        return asdl_node, next_available_id

    asdl_node, _ = get_subtree(py_ast_node, next_available_id=0)
    return asdl_node


def asdl_ast_to_python_ast(asdl_ast_node, grammar):
    py_node_type = getattr(sys.modules['ast'], asdl_ast_node.production.constructor.name)
    py_ast_node = py_node_type()

    for field in asdl_ast_node.fields:
        # for composite node
        field_value = None
        if grammar.is_composite_type(field.type):
            if field.value and field.cardinality == 'multiple':
                field_value = []
                for val in field.value:
                    node = asdl_ast_to_python_ast(val, grammar)
                    field_value.append(node)
            elif field.value and field.cardinality in ('single', 'optional'):
                field_value = asdl_ast_to_python_ast(field.value, grammar)
        else:
            # for primitive node, note that primitive field may have `None` value
            if field.value is not None:
                if isinstance(field.value, list): # Global
                    token_value = [_value.value for _value in field.value]
                else:
                    assert isinstance(field.value, SyntaxToken)
                    token_value = field.value.value

                if field.type.name == 'object':
                    if '.' in token_value or 'e' in token_value:
                        field_value = float(token_value)
                    elif isint(token_value):
                        field_value = int(token_value)
                    else:
                        raise ValueError('cannot convert [%s] to float or int' % field.value)
                elif field.type.name == 'int':
                    field_value = int(token_value)
                else:
                    field_value = token_value

            # FIXME: hack! if int? is missing value in ImportFrom(identifier? module, alias* names, int? level), fill with 0
            elif field.name == 'level':
                field_value = 0

        # must set unused fields to default value...
        if field_value is None and field.cardinality == 'multiple':
            field_value = list()

        setattr(py_ast_node, field.name, field_value)

    return py_ast_node