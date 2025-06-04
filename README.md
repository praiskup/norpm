RPM Macro Expansion in Python
=============================

Parse RPM macro files and spec files, and expand macros safely—without the
potential Turing Complete side effects.

This is a standalone library that depends only on the standard Python library.

How to Use It
-------------

```bash
$ norpm-expand-specfile --specfile SPEC --expand-string '%version %{!?epoch:(none)}'
1.1.1 (none)
```

Directly from Python, you can use:

```python
from norpm.macrofile import system_macro_registry
from norpm.specfile import specfile_expand
registry = system_macro_registry()
registry["dist"] = ""
with open("my.spec", "r", encoding="utf8") as fd:
    expanded_specfile = specfile_expand(fd.read(), registry)
    print("Name: ", registry["name"].value)
    print("Version: ", registry["version"].value)
```

TODOs
-----

There are many features yet to be implemented. Contributions are highly encouraged!

- [x] %undefine
- [x] Parametric macro definitions + calls
- [x] %if, %else parsing (generic)
- [ ] expression parsing (e.g., for %if)
- [ ] %if[n]arch
- [ ] rpmrc files (these e.g. define %optflags)
- [ ] %include
- [ ] %dnl
- [ ] %[expressions]
- [ ] %SOURCEN
- [ ] Requires/BuildRequires parsing
- [ ] built-ins, like %{sub:}, %{expand:}, etc.
- [ ] %{lua:} (not safe, must be an opt-in)
- [ ] %(shell) (not safe, must be an opt-in)
