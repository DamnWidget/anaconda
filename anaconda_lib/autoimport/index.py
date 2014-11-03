"""Build an index of top-level symbols from Python modules and packages."""

import os
import ast
import sys
import json
import logging
from distutils import sysconfig
from contextlib import contextmanager


LIB_LOCATIONS = sorted(set((
    (sysconfig.get_python_lib(standard_lib=True), 'S'),
    (sysconfig.get_python_lib(plat_specific=True), '3'),
    (sysconfig.get_python_lib(standard_lib=True, prefix=sys.prefix), 'S'),
    (sysconfig.get_python_lib(plat_specific=True, prefix=sys.prefix), '3'),
)), key=lambda l: -len(l[0]))

# Modules to treat as built-in.
#
# "os" is here mostly because it imports a whole bunch of aliases from other
# modules. The simplest way of dealing with that is just to import it and use
# vars() on it.
BUILTIN_MODULES = sys.builtin_module_names + ('os',)

LOCATION_BOOSTS = {
    '3': 1.2,
    'L': 1.5,
}


# TODO: Update scores based on import reference frequency.
# eg. if "sys.path" is referenced more than os.path, prefer it.


logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, SymbolIndex):
            d = o._tree.copy()
            d.update(('.' + name, getattr(o, name))
                     for name in SymbolIndex._SERIALIZED_ATTRIBUTES)
            return d
        return super(JSONEncoder, self).default(o)


class SymbolIndex(object):
    tmp_aliases = {
        # Give 'os.path' a score boost over posixpath and ntpath.
        'os.path': (os.path.__name__, 1.2),
        # Same with 'os', due to the heavy aliasing of other packages.
        'os': ('os', 1.2),
    }
    LOCATIONS = {
        'F': 'Future',
        '3': 'Third party',
        'S': 'System',
        'L': 'Local',
    }
    _PCKAGE_ALIASES = dict(
        (v[0], (k, v[1])) for k, v in tmp_aliases.items())
    _SERIALIZED_ATTRIBUTES = {'score': 1.0, 'location': '3'}

    def __init__(self, name=None, parent=None, score=1.0, location='3'):
        self._name = name
        self._tree = {}
        self._exports = {}
        self._parent = parent
        self.score = score
        self.location = location
        if parent is None:
            self._merge_aliases()
            with self.enter('__future__', location='F'):
                pass
            with self.enter('__builtin__', location='S'):
                pass

    def __repr__(self):
        return repr(self._tree)

    def __len__(self):
        return len(self._tree)

    @classmethod
    def deserialize(self, file):
        def load(tree, data, parent_location):
            for key, value in data.items():
                if isinstance(value, dict):
                    score = value.pop('.score', 1.0)
                    location = value.pop('.location', parent_location)
                    with tree.enter(
                            key, score=score, location=location) as subtree:
                        load(subtree, value, location)
                else:
                    msg = '%s expected to be float was %r' % (key, value)
                    assert isinstance(value, float), msg
                    tree.add(key, value)

        data = json.load(file)
        data.pop('.location', None)
        data.pop('.score', None)
        tree = SymbolIndex()
        load(tree, data, 'L')
        return tree

    @contextmanager
    def enter(self, name, location='L', score=1.0):
        if name is None:
            tree = self
        else:
            tree = self._tree.get(name)
            if not isinstance(tree, SymbolIndex):
                tree = self._tree[name] = SymbolIndex(
                    name, self, score=score, location=location)
                if tree.path() in SymbolIndex._PCKAGE_ALIASES:
                    alias_path, _ = SymbolIndex._PCKAGE_ALIASES[tree.path()]
                    alias = self.find(alias_path)
                    alias._tree = tree._tree
        yield tree
        if tree._exports:
            # Delete unexported variables
            for key in set(tree._tree) - set(tree._exports):
                del tree._tree[key]

    def index_source(self, filename, source):
        try:
            st = ast.parse(source, filename)
        except Exception as e:
            print('Failed to parse %s: %s' % (filename, e))
            return
        visitor = SymbolVisitor(self)
        visitor.visit(st)

    def index_file(self, module, filename):
        # test modules that we never attempt to index.
        if 'test' in filename:
            return
        loc = self._determine_location_for(filename)
        with self.enter(module, location=loc) as subtree:
            with open(filename) as fd:
                subtree.index_source(filename, fd.read())

    def index_path(self, root):
        """Index a path.

        :param root: Either a package directory, a .so or a .py module.
        """

        if os.path.basename(root).startswith('_'):
            return
        location = self._determine_location_for(root)
        if os.path.isfile(root):
            self._index_module(root, location)
        elif (os.path.isdir(root)
                and os.path.exists(os.path.join(root, '__init__.py'))):
            self._index_package(root, location)

    def index_builtin(self, name, location):
        if name.startswith('_'):
            return
        try:
            module = __import__(name, fromlist=['.'])
        except ImportError:
            logger.debug('failed to index builtin module %s', name)
            return

        with self.enter(name, location=location) as subtree:
            for key, value in vars(module).iteritems():
                if not key.startswith('_'):
                    subtree.add(key, 1.1)

    def build_index(self, paths):
        if len(self._tree) == 3:
            for builtin in BUILTIN_MODULES:
                self.index_builtin(builtin, location='S')

        for path in paths:
            if os.path.isdir(path):
                for filename in os.listdir(path):
                    filename = os.path.join(path, filename)
                    self.index_path(filename)

    def symbol_scores(self, symbol):
        """Find matches for symbol.

        :param symbol: A . separated symbol. eg. 'os.path.basename'
        :returns: A list of tuples of (score, package, reference|None),
            ordered by score from highest to lowest.
        """
        scores = []
        path = []

        # sys.path          sys path          ->   import sys
        # os.path.basename  os.path basename  ->   import os.path
        # basename          os.path basename  ->   from os.path import basename
        # path.basename     os.path basename  ->   from os import path
        def fixup(module, variable):
            prefix = module.split('.')
            if variable is not None:
                prefix.append(variable)
            seeking = symbol.split('.')
            module = []
            while prefix and seeking[0] != prefix[0]:
                module.append(prefix.pop(0))
            module, variable = '.'.join(module), prefix[0]
            # os -> '', 'os'
            if not module:
                module, variable = variable, None
            return module, variable

        def score_walk(scope, scale):
            sub_path, score = self._score_key(scope, full_key)
            if score > 0.1:
                try:
                    i = sub_path.index(None)
                    sub_path, from_symbol = (
                        sub_path[:i], '.'.join(sub_path[i + 1:]))
                except ValueError:
                    from_symbol = None
                package_path = '.'.join(path + sub_path)
                package_path, from_symbol = fixup(package_path, from_symbol)
                scores.append((score * scale, package_path, from_symbol))

            for key, subscope in scope._tree.items():
                if type(subscope) is not float:
                    path.append(key)
                    score_walk(subscope, subscope.score * scale - 0.1)
                    path.pop()

        full_key = symbol.split('.')
        score_walk(self, 1.0)
        scores.sort(reverse=True)
        return scores

    def depth(self):
        depth = 0
        node = self
        while node._parent:
            depth += 1
            node = node._parent
        return depth

    def path(self):
        path = []
        node = self
        while node and node._name:
            path.append(node._name)
            node = node._parent
        return '.'.join(reversed(path))

    def add_explicit_export(self, name, score):
        self._exports[name] = score

    def find(self, path):
        """Return the node for a path, or None."""
        path = path.split('.')
        node = self
        while node._parent:
            node = node._parent
        for name in path:
            node = node._tree.get(name, None)
            if node is None or type(node) is float:
                return None
        return node

    def location_for(self, path):
        """Return the location code for a path."""
        path = path.split('.')
        node = self
        while node._parent:
            node = node._parent
        location = node.location
        for name in path:
            tree = node._tree.get(name, None)
            if tree is None or type(tree) is float:
                return location
            location = tree.location
        return location

    def add(self, name, score):
        current_score = self._tree.get(name, 0.0)
        if score > current_score:
            self._tree[name] = score

    def serialize(self, fd=None):
        if fd is None:
            return json.dumps(self, cls=JSONEncoder)
        return json.dump(self, fd, cls=JSONEncoder)

    def boost(self):
        return LOCATION_BOOSTS.get(self.location, 1.0)

    def _index_package(self, root, location):
        basename = os.path.basename(root)
        with self.enter(basename, location=location) as subtree:
            for filename in os.listdir(root):
                subtree.index_path(os.path.join(root, filename))

    def _index_module(self, root, location):
        basename, ext = os.path.splitext(os.path.basename(root))
        if basename == '__init__':
            basename = None
        ext = ext.lower()
        import_path = '.'.join(filter(None, [self.path(), basename]))
        if import_path in BUILTIN_MODULES:
            return
        if ext == '.py':
            self.index_file(basename, root)
        elif ext in ('.dll', '.so'):
            self.index_builtin(import_path, location=location)

    def _merge_aliases(self):
        def create(node, alias, score):
            if not alias:
                return
            name = alias.pop(0)
            rscore = 1.0 if alias else score
            with node.enter(name, location='S', score=rscore) as index:
                create(index, alias, score)

        for alias, (package, score) in SymbolIndex._PCKAGE_ALIASES.items():
            create(self, package.split('.'), score)

    def _score_key(self, scope, key):
        if not key:
            return [], 0.0
        key_score = value = scope._tree.get(key[0], None)
        if value is None:
            return [], 0.0
        if type(value) is float:
            return [None, key[0]], key_score * scope.boost()
        else:
            path, score = self._score_key(value, key[1:])
            return [key[0]] + path, (score + value.score) * scope.boost()

    def _determine_location_for(self, path):
        for dir, location in LIB_LOCATIONS:
            if path.startswith(dir):
                return location
        return 'L'


class SymbolVisitor(ast.NodeVisitor):
    """Visit each node in the abstract syntax tree
    """

    def __init__(self, tree):
        self._tree = tree

    def visit_ImportFrom(self, node):

        for name in node.names:
            if name.name != '*' and not name.name.startswith('_'):
                if name.name not in self._tree._tree:
                    self._tree.add(name.name, 0.25)

    def visit_Import(self, node):

        for name in node.names:
            if (not name.name.startswith('_')
                    and name.name not in self._tree._tree):
                self._tree.add(name.name, 0.25)

    def visit_ClassDef(self, node):
        self._common_operation(node, 1.1)

    def visit_FunctionDef(self, node):
        self._common_operation(node, 1.1)

    def visit_Assign(self, node):
        # TODO: Handle __all__
        names = [n for n in node.targets if isinstance(n, ast.Name)]
        for name in names:
            if name.id == '__all__' and isinstance(node.value, ast.List):
                for subnode in node.value.elts:
                    if isinstance(subnode, ast.Str):
                        self._tree.add_explicit_export(subnode.s, 1.2)
            elif not name.id.startswith('_'):
                self._tree.add(name.id, 1.1)

    def visit_If(self, node):
        # NOTE: In lieu of actually parsing if/else blocks at the top-level,
        # we'll just ignore them.
        pass

    def _common_operation(self, node, score):
        if not node.name.startswith('_') and node.name not in self._tree._tree:
            self._tree.add(node.name, score)


if __name__ == '__main__':
    # print ast.dump(ast.parse(open('pyautoimp.py').read(), 'pyautoimp.py'))
    tree = SymbolIndex()
    tree.build_index(sys.path)
    tree.serialize(sys.stdout)
    print(defaultdict)
