"""
Test conditions_for_arch_statements.py script
"""

import os
import tempfile

from norpm.macro import MacroRegistry
from norpm.cli.conditions_for_arch_statements import macro_names_needed


def test_arch_detector():
    """
    Normal way of working.
    """
    db = MacroRegistry()
    with tempfile.TemporaryDirectory() as temp_dir:
        spec_file_path = os.path.join(temp_dir, 'foo.spec')

        # Create and write some content to the file
        with open(spec_file_path, 'w') as f:
            f.write("""\
%global foo 1
%global blah %foo
%if 0%{?blah}
ExcludeArch: %java_arches
%else
%ifarch %{myarch}
ExclusiveArch: %go_arches
%endif
# this one is not detected
%if 0%{?a_foo}
BuildArch: noarch
%endif
%if 0%{?barbar}
Name: bar
%endif
""")
        assert macro_names_needed(spec_file_path, db) == \
                {'a_foo', 'blah', 'go_arches', 'java_arches', 'myarch'}
