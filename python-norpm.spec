Name:           python-norpm
Version:        1.2
Release:        1%?dist
Summary:        RPM Macro Expansion in Python

License:        LGPL-2.1-or-later
URL:            hhttps://github.com/praiskup/norpm
Source:         %pypi_source norpm

BuildArch:      noarch
BuildRequires:  python3-devel
# Test dependencies:
BuildRequires:  python3dist(pytest)


%global _description %{expand:
Parse RPM macro and spec files, expanding macros safely—without any potential
Turing-complete side effects.

This is a standalone library and set of tools that depend only on the standard
Python library and PLY (used for expression parsing).
}

%description %_description


%package -n     python3-norpm
Summary:        %summary

%description -n python3-norpm %_description


%prep
%autosetup -p1 -n norpm-%version


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l norpm


%check
%pyproject_check_import
%pytest


%files -n python3-norpm -f %pyproject_files
%license COPYING
%doc README.md
%_bindir/norpm-expand-specfile


%changelog
* Mon Aug 11 2025 Pavel Raiskup <praiskup@redhat.com> - 1.2-1
- Initial packaging
