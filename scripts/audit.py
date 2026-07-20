"""Data-Core 代码审计脚本"""
import os
import ast

BASE = r"d:\Programs\data-core\datacore"
issues = []

for root, dirs, files in os.walk(BASE):
    for fn in sorted(files):
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        rel = os.path.relpath(path, BASE)
        content = open(path, "r", encoding="utf-8").read()

        # Syntax check
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError as e:
            issues.append(("SYNTAX", rel, str(e)))
            continue

        lines = content.split("\n")
        n = len(lines)

        # File length
        if n > 300:
            issues.append(("LONG", rel, f"{n} lines (>300)"))

        # Missing docstring
        first_stmt = next(
            (node for node in ast.iter_child_nodes(tree)
             if isinstance(node, (ast.Expr, ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom))),
            None
        )
        has_doc = (
            isinstance(first_stmt, ast.Expr)
            and isinstance(first_stmt.value, ast.Constant)
            and isinstance(first_stmt.value.value, str)
        )
        if not has_doc:
            issues.append(("NODOC", rel, "missing module docstring"))

        # Bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(("BARE_EXCEPT", rel, f"line {node.lineno}"))

        # Unused imports check
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imported_names.add(alias.asname or alias.name)

        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                pass
        unused = imported_names - used_names - {"__future__", "__all__", "ABC", "abstractmethod"}
        stdlib_core = {"os", "sys", "time", "json", "hashlib", "pickle", "pathlib", "abc", "typing", "ast", "re"}
        unused = {u for u in unused if u not in stdlib_core}
        if unused:
            issues.append(("UNUSED_IMPORT", rel, str(unused)))

        # Check Optional vs None default pattern
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, ast.Constant) and default.value is None:
                        pass  # None defaults are fine

print(f"Audited {sum(1 for _, _, files in os.walk(BASE) for f in files if f.endswith('.py'))} files")
if issues:
    print(f"\nFound {len(issues)} issues:")
    for cat, rel, msg in issues:
        print(f"  [{cat:12s}] {rel:40s} {msg}")
else:
    print("No issues found")
