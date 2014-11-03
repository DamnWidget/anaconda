"""Imports new symbols.
"""

import tokenize
from collections import defaultdict

from compat import StringIO


class Iterator(object):

    def __init__(self, tokens, start=None, end=None):
        self._tokens = tokens
        self._cursor = start or 0
        self._end = end or len(self._tokens)

    def rewind(self):
        self._cursor -= 1

    def next(self):
        if not self:
            return None, None
        token = self._tokens[self._cursor]
        index = self._cursor
        self._cursor += 1
        return index, token

    def peek(self):
        return self._tokens[self._cursor] if self else None

    def until(self, type):
        tokens = []
        while self:
            index, token = self.next()
            tokens.append((index, token))
            if type == token[0]:
                break
        return tokens

    def __nonzero__(self):
        return self._cursor < self._end
    __bool__ = __nonzero__


class Import(object):

    def __init__(self, location, name, alias):
        self.location = location
        self.name = name
        self.alias = alias

    def __repr__(self):
        return 'Import(location=%r, name=%r, alias=%r)' % \
            (self.location, self.name, self.alias)

    def __hash__(self):
        return hash((self.location, self.name, self.alias))

    def __eq__(self, other):
        return (self.location == other.location
                and self.name == other.name and self.alias == other.alias)

    def __ne__(self, other):
        return (self.location != other.location
                or self.name != other.name or self.alias != other.alias)

    def __lt__(self, other):
        return self.location < other.location \
            or self.name < other.name \
            or (self.alias is not None
                and other.alias is not None and self.alias < other.alias)


# See SymbolIndex.LOCATIONS for details.
LOCATION_ORDER = 'FS3L'


class Imports(object):

    def __init__(self, index, source):
        self._imports = set()
        self._imports_from = defaultdict(set)
        self._import_begin = self._imports_end = None
        self._source = source
        self._index = index
        self._parse(source)

    def add_import(self, name, alias=None):
        location = LOCATION_ORDER.index(self._index.location_for(name))
        self._imports.add(Import(location, name, alias))

    def add_import_from(self, module, name, alias=None):
        location = LOCATION_ORDER.index(self._index.location_for(module))
        self._imports_from[module].add(Import(location, name, alias))

    def remove(self, references):
        for imp in list(self._imports):
            if imp.name in references:
                self._imports.remove(imp)
        for name, imports in self._imports_from.items():
            for imp in list(imports):
                if imp.name in references:
                    imports.remove(imp)

    def get_update(self):
        groups = []
        for expected_location in range(len(LOCATION_ORDER)):
            out = StringIO()
            for imp in sorted(self._imports):
                if expected_location != imp.location:
                    continue
                out.write('import {module}{alias}\n'.format(
                    module=imp.name,
                    alias='as {alias}'.format(
                        alias=imp.alias) if imp.alias else '',
                ))

            for module, imports in sorted(self._imports_from.items()):
                imports = sorted(imports)
                if not imports or expected_location != imports[0].location:
                    continue
                line = 'from {module} import '.format(module=module)
                clauses = ['{name}{alias}'.format(
                           name=i.name,
                           alias=' as {alias}'.format(
                               alias=i.alias) if i.alias else ''
                           ) for i in imports]
                clauses.reverse()
                while clauses:
                    clause = clauses.pop()
                    if len(line) + len(clause) + 1 > 80:
                        line += '\\\n'
                        out.write(line)
                        line = '    '
                    line += clause + (', ' if clauses else '')
                if line.strip():
                    out.write(line + '\n')

            text = out.getvalue()
            if text:
                groups.append(out.getvalue())

        start = self._tokens[self._import_begin][2][0] - 1
        end = self._tokens[
            min(len(self._tokens) - 1, self._imports_end)][2][0] - 1
        if groups:
            text = '\n'.join(groups) + '\n\n'
        else:
            text = ''
        return start, end, text

    def update_source(self):
        start, end, text = self.get_update()
        lines = self._source.splitlines()
        lines[start:end] = text.splitlines()
        return '\n'.join(lines)

    def _parse(self, source):
        reader = StringIO(source)
        self._tokens = list(tokenize.generate_tokens(reader.readline))
        it = Iterator(self._tokens)
        self._import_begin, self._imports_end = self._find_import_range(it)
        it = Iterator(
            self._tokens, start=self._import_begin, end=self._imports_end)
        self._parse_imports(it)

    def _find_import_range(self, it):
        ranges = self._find_import_ranges(it)
        start, end = ranges[0][1:]
        return start, end

    def _find_import_ranges(self, it):
        ranges = []
        indentation = 0
        explicit = False
        size = 0
        start = None

        while it:
            index, token = it.next()

            if token[0] == tokenize.INDENT:
                indentation += 1
                continue
            elif token[0] == tokenize.DEDENT:
                indentation += 1
                continue

            if indentation:
                continue

            # Explicitly tell importmagic to manage a particular block of
            # imports.
            if token[1] == '# importmagic: manage':
                explicit = True
            elif token[0] in (
                tokenize.STRING, tokenize.NEWLINE,
                tokenize.NL, tokenize.COMMENT
            ):
                continue

            if not ranges:
                ranges.append((0, index, index))

            # Accumulate imports
            if token[1] in ('import', 'from'):
                if start is None:
                    start = index
                size += 1
                while it:
                    token = it.peek()
                    if token[0] == tokenize.NEWLINE or token[1] == ';':
                        break
                    index, _ = it.next()

            # Terminate this import range
            elif start is not None and token[1].strip():
                ranges.append((size, start, index))
                start = None
                size = 0
                if explicit:
                    ranges = ranges[-1:]
                    break

        if start is not None:
            ranges.append((size, start, index))
        ranges.sort(reverse=True)
        return ranges

    def _parse_imports(self, it):
        while it:
            index, token = it.next()

            if token[1] not in ('import', 'from') and token[1].strip():
                break

            type = token[1]
            if type in ('import', 'from'):
                tokens = it.until(tokenize.NEWLINE)
                tokens = [t[1] for i, t in tokens
                          if t[0] == tokenize.NAME or t[1] in ',.']
                tokens.reverse()
                self._parse_import(type, tokens)

    def _parse_import(self, type, tokens):
        module = None
        if type == 'from':
            module = ''
            while tokens and tokens[-1] != 'import':
                module += tokens.pop()
            assert tokens.pop() == 'import'
        while tokens:
            name = ''
            while True:
                name += tokens.pop()
                next = tokens.pop() if tokens else None
                if next == '.':
                    name += next
                else:
                    break

            alias = None
            if next == 'as':
                alias = tokens.pop()
                if alias == name:
                    alias = None
                next = tokens.pop() if tokens else None
            if next == ',':
                pass
            if type == 'import':
                self.add_import(name, alias=alias)
            else:
                self.add_import_from(module, name, alias=alias)

    def __repr__(self):
        return 'Imports(imports={!r}, impots_from={!r}'.format(
            self._imports, self._imports_from
        )


def _process_imports(src, index, unresolved, unreferenced):
    imports = Imports(index, src)
    imports.remove(unreferenced)
    for symbol in unresolved:
        scores = index.symbol_scores(symbol)
        if not scores:
            continue
        _, module, variable = scores[0]
        # Direct module import: eg. os.path
        if variable is None:
            # sys.path         sys path          -> import sys
            # os.path.basename os.path basename  -> import os.path
            imports.add_import(module)
        else:
            # basename      os.path basename -> from os.path import basename
            # path.basename os.path basename -> from os import path
            imports.add_import_from(module, variable)
    return imports


def get_update(src, index, unresolved, unreferenced):
    imports = _process_imports(src, index, unresolved, unreferenced)
    return imports.get_update()


def update_imports(src, index, unresolved, unreferenced):
    imports = _process_imports(src, index, unresolved, unreferenced)
    return imports.update_source()
