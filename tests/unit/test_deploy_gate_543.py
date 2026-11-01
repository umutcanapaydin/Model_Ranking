"""#543 (the release delta security review's R11): `deploy_gate.policy_root` had no caller since #517, and returned the
brief at the merge-base alone, so a future caller would quietly undo D-232 clause 1 (the policy is read at every
protected base, the merge-base and the default branch's tip) with every test green.

The rule, derived over every Python file under `scripts/` and `.claude/hooks/` (never a hand-kept list): no file but
`brief_fields` calls `protected_base` (one base), and no file reads one of the policy roots `_policy` returns alone
(a subscript of them), where the gate takes the union of all of them.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import deploy_gate

ROOT = Path(__file__).resolve().parents[2]


def _sources() -> dict[str, str]:
    files = sorted([*(ROOT / "scripts").rglob("*.py"), *(ROOT / ".claude" / "hooks").glob("*.py")])
    return {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8") for p in files}


def _called(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        func = node.func
        return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
    return None


def single_base_reads(source: str) -> list[str]:
    """Each place `source` reads one protected base for policy: a call to `protected_base`, or a subscript of the
    policy roots `_policy` returns (bound by unpacking its first element, or indexed straight off the call)."""
    tree = ast.parse(source)
    found: list[str] = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module))]:
        roots: set[str] = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and _called(node.value) == "_policy":
                for target in node.targets:
                    first = target.elts[0] if isinstance(target, ast.Tuple) and target.elts else None
                    if isinstance(first, ast.Name):
                        roots.add(first.id)
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and _called(node) == "protected_base":
                found.append(f"line {node.lineno}: protected_base(...)")
            if isinstance(node, ast.Subscript):
                value = node.value
                if isinstance(value, ast.Name) and value.id in roots:
                    found.append(f"line {node.lineno}: {value.id}[...] of _policy(...)")
                if isinstance(value, ast.Subscript) and _called(value.value) == "_policy":
                    found.append(f"line {node.lineno}: _policy(...)[...][...]")
    return sorted(set(found))


def test_the_rule_fires_on_a_single_base_read_and_stays_quiet_on_the_union() -> None:
    """Watched to fail (writing-a-control §2): the shape `policy_root` had is found; reading every root is not."""
    planted = ("def policy_root(root):\n    policies, where, _ = _policy(root)\n"
               "    return (policies[0] if policies else None), where\n"
               "def other(root):\n    return _policy(root)[0][0]\n"
               "def third(root):\n    return brief_fields.protected_base(root)\n")
    assert len(single_base_reads(planted)) == 3
    union = ("def declared(root):\n    policies, _, _ = _policy(root)\n"
             "    return [p for p in policies or []]\n")
    assert single_base_reads(union) == []


def test_no_script_reads_a_single_protected_base_for_policy() -> None:
    sources = _sources()
    assert "scripts/deploy_gate.py" in sources and "scripts/brief_fields.py" in sources, \
        f"the derived file set is not the tree it should be ({len(sources)} files): fail closed"
    assert any("_policy(" in text for text in sources.values()), "no reader of `_policy` found: fail closed"
    offenders = {rel: reads for rel, text in sources.items() if rel != "scripts/brief_fields.py"
                 if (reads := single_base_reads(text))}
    assert offenders == {}, f"a script reads one protected base where the gate reads them all (D-232): {offenders}"


def test_policy_root_is_gone() -> None:
    assert not hasattr(deploy_gate, "policy_root"), "#543: the dead single-base reader is back"
