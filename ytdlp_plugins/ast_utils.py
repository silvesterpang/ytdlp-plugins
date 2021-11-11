import ast
from contextlib import suppress
from importlib import import_module
from inspect import getsourcelines, getsourcefile
from typing import Dict, Any, List, Tuple

_CACHE: Dict[type, Tuple[str, List[Dict[str, Any]]]] = {}


def dict_info(node: ast.Dict, **defaults) -> Dict[str, Any]:
    line_info = {"_self": node.lineno}
    info = {"_lineno": line_info}
    for key, value in zip(node.keys, node.values):
        with suppress(AssertionError):
            assert isinstance(key, ast.Constant)
            if isinstance(value, ast.Constant):
                actual_value = value.value
            elif isinstance(value, ast.Dict):
                _defaults = defaults.get(key.value, {})
                actual_value = dict_info(value, **_defaults)
            elif isinstance(value, ast.List):
                actual_value = list_info(value, **defaults)
            else:
                continue
            line_info[key.value] = value.lineno
            info[key.value] = actual_value

    return info


def list_info(node: ast.List, **defaults) -> List[Dict[str, Any]]:
    data = []
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, ast.Dict):
            continue
        info = dict_info(child, **defaults)
        data.append(info)
    return data


def unlazyify(cls: type) -> type:
    with suppress(AttributeError, ImportError):
        actual_module = getattr(cls, "_module")
        module = import_module(actual_module)
        cls = getattr(module, cls.__name__)
    return cls


def find_assignment(node, name_predicate):
    for child in ast.iter_child_nodes(node):
        with suppress(AssertionError):
            assert isinstance(child, ast.Assign)
            left_expr = child.targets[0]
            assert isinstance(left_expr, ast.Name)
            name = left_expr.id
            assert name_predicate(name)
            return child.value
    return None


def get_line_infos(cls: type) -> Tuple[str, List[Dict[str, Any]]]:
    cls = unlazyify(cls)
    source_file = getsourcefile(cls)
    assert isinstance(source_file, str)
    source_lines, line_number = getsourcelines(cls)
    ast_obj = ast.parse("".join(source_lines))
    ast.increment_lineno(ast_obj, n=line_number - 1)

    test_node = find_assignment(ast_obj.body[0], lambda name: name.startswith("_TEST"))
    if not isinstance(test_node, ast.List):
        return source_file, [{"file": source_file, "lineno": line_number}]

    data = list_info(test_node, playlist=None)
    return source_file, data


def get_test_lineno(cls: type, index: int) -> Dict[str, Any]:
    if cls in _CACHE:
        source_filename, line_infos = _CACHE[cls]
    else:
        source_filename, line_infos = get_line_infos(cls)
        _CACHE[cls] = source_filename, line_infos

    if index >= len(line_infos):
        index = len(line_infos) - 1

    info = line_infos[index]
    info["_file"] = source_filename

    return info