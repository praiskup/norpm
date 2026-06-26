# norpm NEWS

## v1.10
- Support RPM 6.1+ macro modifiers (`<l>` and `<o>`)
- Tests for ExcludeArch/ExclusiveArch parsing
- Updated Rawhide tests

## v1.9
- Accept %define & %global with curly brackets
- Fix aliasing with %{**} syntax
- Mark built-ins "defined"
- Switch expression parser from PLY to Lark
- Enable EPEL 9 builds

## v1.8
- New helper override_macro_registry()

## v1.7
- Define hierarchy of norpm exceptions
- Tests: use hooks for reading tags (rawhide tests)
- Builtins: rep, shrink, suffix
- Implement expr
- Builtin reverse

## v1.6
- Initial release with macro expansion support
