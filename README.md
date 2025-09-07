RPM Macro Expansion in Python
=============================

Parse RPM macro files and spec files, and expand macros safely—without the
potential Turing-Complete side effects.

This is a standalone library that depends only on the standard Python library
and [PLY](https://github.com/dabeaz/ply) (for expression parsing).

How to Use It
-------------

```bash
$ norpm-expand-specfile --specfile SPEC --expand-string '%{?epoch}%{!?epoch:(none)}:%version'
(none):1.1.1
```

Directly from Python, you can use:

```python
from norpm.macrofile import system_macro_registry
from norpm.specfile import specfile_expand
registry = system_macro_registry()
with open("SPEC", "r", encoding="utf8") as fd:
    expanded_specfile = specfile_expand(fd.read(), registry)
    print("Name:", registry["name"].value)
    print("Version:", registry["version"].value)
```

State of the implementation
-----

There still are a [few features][rfes] to be implemented.  Your contributions
are welcome and greatly encouraged!

[rfes]: https://github.com/praiskup/norpm/issues?q=is%3Aissue%20state%3Aopen%20label%3Aenhancement
