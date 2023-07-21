import ast


class RenameVariables(ast.NodeTransformer):
    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if isinstance(node.ctx, ast.Load) and node.id in self.mapping.keys():
            return ast.Name(id=self.mapping[node.id], ctx=ast.Load())
        else:
            return node


def rename_variables(expression: str, mapping: dict[str, str]) -> str:
    node = ast.parse(expression)
    transformed = RenameVariables(mapping).visit(node)
    return ast.unparse(transformed)


def get_variable_names(expression: str) -> set[str]:
    node = ast.parse(expression)
    return set(n.id for n in ast.walk(node) if isinstance(n, ast.Name))
