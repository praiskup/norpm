RPM macro expansion written in Python
=====================================

Parse RPM macro files and spec files, and expand macros in a safe manner—without
the possible Turing Complete side-effects.

This is a self standing library that depends only on the standard Python
library.

How to use it
-------------

$ norpm-expand-specfile --specfile SPEC --expand-string '%version %{!?epoch:(none)}'
1.1.1 (none)

Directly from Python, one may use:

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

TODO
====

There are many things waiting to be implemented.  Contributions are welcome!

- [ ] Parametric macro definitions + calls, like `%macro arg1 arg2\eol`
- [ ] %if/%ifarch, %else statements
- [ ] rpmrc files (these e.g. define %optflags)
- [ ] %include
- [ ] %dnl
- [ ] %{lua:} (not safe, must be an opt-in)
- [ ] %(shell) (not safe, must be an opt-in)
- [ ] %undefine
- [ ] %[expressions]
- [ ] %SOURCEN
- [ ] Requires/BuildRequires parsing
- [ ] built-ins, like %{sub:}, %{expand:}, etc.
