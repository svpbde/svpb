"""Sphinx extension adding support for different scopes.

This allows to build documents for different target audiences by marking the
documentation with scopes. When the documentation is build, the scope is given
as tag (command line switch -t).
"""
from functools import reduce
import os
import re

from sphinx import addnodes


docs_to_remove = []


def setup(app):
    app.ignore = []
    app.connect('builder-inited', builder_inited)
    app.connect('env-get-outdated', env_get_outdated)
    app.connect('doctree-read', doctree_read)


def builder_inited(app):
    for doc in app.env.found_docs:
        first_directive = None
        # source_suffix is returned as dict, see
        # https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-source_suffix
        suffix_keys = list(app.env.config.source_suffix.keys())
        if len(suffix_keys) != 1:
            raise ValueError("Only one source_suffix is supported. If you want"
                             " to use more, please implement it yourself.")
        with open(app.env.srcdir + os.sep + doc + suffix_keys[0], 'r') as f:
            first_directive = f.readline() + f.readline()
        if first_directive:
            m = re.match(r'^\.\. meta::\s+:scope: (.*)$', first_directive)
            if m:
                tags = m.group(1).split(' ')
                include = reduce(lambda a, b: a or b,
                                 [app.tags.has(t) for t in tags])
                if not include:
                    docs_to_remove.append(doc)

    app.env.found_docs.difference_update(docs_to_remove)


def env_get_outdated(app, env, added, changed, removed):
    added.difference_update(docs_to_remove)
    changed.difference_update(docs_to_remove)
    removed.update(docs_to_remove)
    return []


def doctree_read(app, doctree):
    for toctreenode in doctree.traverse(addnodes.toctree):
        for e in toctreenode['entries']:
            ref = str(e[1])
            if ref in docs_to_remove:
                toctreenode['entries'].remove(e)
