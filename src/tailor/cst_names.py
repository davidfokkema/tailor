import libcst as cst


class FindVariables(cst.CSTVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.names = set()

    def visit_Name(self, node: cst.Name) -> None:
        self.names.add(node.value)


class RenameVariables(cst.CSTTransformer):
    def __init__(self, mapping: dict[str, str]):
        super().__init__()
        self.mapping = mapping

    def leave_Name(self, node: cst.Name, updated_node: cst.Name) -> cst.Name:
        if node.value in self.mapping.keys():
            return updated_node.with_changes(value=self.mapping[node.value])
        else:
            return updated_node


def rename_variables(expression: str, mapping: dict[str, str]) -> str:
    try:
        # first parse as expression to see if it is valid code
        cst.parse_expression(expression)
        # then, parse code while preserving whitespace etc.
        tree = cst.parse_module(expression)
    except cst.ParserSyntaxError:
        raise SyntaxError("SyntaxError while parsing expression")

    transformer = RenameVariables(mapping)
    modified_tree = tree.visit(transformer)
    return modified_tree.code


def get_variable_names(expression: str) -> list[str]:
    try:
        tree = cst.parse_expression(expression)
    except cst.ParserSyntaxError:
        raise SyntaxError("SyntaxError while parsing expression")

    visitor = FindVariables()
    tree.visit(visitor)
    return visitor.names
