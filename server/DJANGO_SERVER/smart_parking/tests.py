import ast
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent
LAYERS = ['users', 'parking', 'camera', 'detection']
SHARED = 'shared'


def source_files(module):
    for path in (ROOT / module).rglob('*.py'):
        relative = path.relative_to(ROOT / module)
        if relative.parts[0] == 'migrations' or path.name == 'tests.py':
            continue
        yield path


def imported_modules(path):
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module
            yield from (f"{node.module}.{alias.name}" for alias in node.names)


def violations():
    found = []
    for module in LAYERS + [SHARED]:
        for path in source_files(module):
            for name in imported_modules(path):
                target = name.split('.')[0]
                if target == module or target not in LAYERS + [SHARED]:
                    continue
                where = f"{path.relative_to(ROOT)} imports {name}"
                if module == SHARED:
                    found.append(f"{where}: shared must not depend on a module")
                elif target == SHARED:
                    continue
                elif LAYERS.index(target) > LAYERS.index(module):
                    found.append(f"{where}: {module} may only depend on lower modules")
                elif not (name == target or name.startswith(f"{target}.interface")):
                    found.append(f"{where}: go through {target}.interface")
    return found


class ArchitectureTests(SimpleTestCase):
    def test_modules_respect_their_boundaries(self):
        self.assertEqual(violations(), [])
