import libcst as cst


class FindVariables(cst.CSTVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.names = []

    def visit_Name(self, node: cst.Name) -> None:
        if node.value not in self.names:
            self.names.append(node.value)


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
    tree = cst.parse_module(expression)
    transformer = RenameVariables(mapping)
    modified_tree = tree.visit(transformer)
    print(f"{id(tree)=}, {id(modified_tree)=}")
    return modified_tree.code


def get_variable_names(expression: str) -> list[str]:
    tree = cst.parse_module(expression)
    visitor = FindVariables()
    tree.visit(visitor)
    return visitor.names


if __name__ == "__main__":
    print(f"{get_variable_names('a + b * x')=}")

    mapping = {"x": "col1", "b": "col2"}
    print(f"{mapping=}")
    print(f"{rename_variables('a + b * x', mapping)=}")
