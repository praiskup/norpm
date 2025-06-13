# Use forge macros for getting source tarball from GitHub
%global forgeurl https://github.com/nest/nest-simulator

# We build the python bit separately - their build system doesn't let me build
# and install separately - everything is done at install time

# We do not build the developer documentation with doxygen. Advanced developers
# that develop based on the source git tree can build it themselves

# Switch them off if you want
%bcond mpich 1
%bcond openmpi 1

# Tests include source linters and so on, and require a specific older version
# of vera and clang and so forth, so we simply rely on upstream CI here
%bcond tests 0

# Default for numthreads
%global numthreads %{?_smp_build_ncpus}

# build fails on ppc with lto enabled in rawhide
# https://bugzilla.redhat.com/show_bug.cgi?id=2056459
# fails on F34 and F35 on aarch64
%ifarch %{power64} %{arm64}
%global _lto_cflags %{nil}
%endif

# On armv7 we get a failure with LTO.  The log has no useful information in it
# but my guess is we ran out of memory on the builder.  Disable LTO for armv7
# Also runs out of memory without lto. Seems to need about 25Gigs per thread,
# so limit the number of threads

%ifarch armv7hl
%global _lto_cflags %{nil}

%global numthreads %(awk '/MemTotal:/ {print int($2/25e6)}' /proc/meminfo)

%if 0%{numthreads} > 0%{?_smp_build_ncpus}
%global numthreads %{?_smp_build_ncpus}
%endif

# ensure that it's > 0
%if 0%{numthreads} == 0
%global numthreads 1
%endif

# also reduce debuginfo level
%global optflags %(echo "%optflags" | sed  -e 's/-g /-g1 /')
%endif

Name:           nest
Version:        3.8
Release:        %autorelease
Summary:        The neural simulation tool
%forgemeta

# thirdparty/compose is LGPLv2.1+
# thirdparty/randutils.hpp is MIT
# SPDX
License:        GPL-2.0-or-later and MIT and LGPL-2.1-or-later
URL:            http://www.nest-simulator.org/
Source0:        %forgesource
Source1:        README-Fedora.md

# https://github.com/sanjayankur31/nest-simulator/tree/fedora-3.7
# 1. Let it build and install the cythonised shared object But we still build
# our python modules ourselves

# 2. The helpindex must be generated after the help files have been installed
# to the install location, so we do this manually because the script doesn't
# respect rpmbuildroot and so on
Patch:          0001-disable-python-setups.patch
# Tweak PYEXECDIR
Patch:          0002-tweak-PYEXECDIR.patch
# Use system Random123
Patch:          0003-use-system-Random123.patch
# Remove rpath
Patch:          0004-remove-rpath.patch
# Install in standard libdir
Patch:          0005-install-in-libdir.patch
# Use online docs for helpdesk
Patch:          0006-use-online-documentation.patch

# Remove hard coded O0
Patch:          0007-remove-hard-coded-O0.patch

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}

BuildRequires:  boost-devel
BuildRequires:  cmake
BuildRequires:  chrpath
BuildRequires:  graphviz
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  ncurses-devel
BuildRequires:  gsl-devel
BuildRequires:  libtool
BuildRequires:  libtool-ltdl-devel
BuildRequires:  libneurosim-devel
BuildRequires:  python3-devel
BuildRequires:  python3-Cython
BuildRequires:  python3-mock
BuildRequires:  python3-pytest
BuildRequires:  python3-setuptools
BuildRequires:  readline-devel
BuildRequires:  Random123-devel
Requires:       %{name}-common

%global _description %{expand:
NEST is a simulator for spiking neural network models that focuses on the
dynamics, size and structure of neural systems rather than on the exact
morphology of individual neurons. The development of NEST is coordinated by the
NEST Initiative.  NEST is ideal for networks of spiking neurons of any size,
for example: Models of information processing e.g. in the visual or auditory
cortex of mammals; Models of network activity dynamics, e.g. laminar cortical
networks or balanced random networks; Models of learning and plasticity.
Please read the README-Fedora.md file provided in each package for information
on how these NEST packages are to be used.

Please see https://nest-simulator.readthedocs.io/ for the latest documentation.
}

%description %_description

%package common
BuildArch:  noarch
Summary:    Common files for %{name}

%description common %_description

# These are also arch specific
%package devel
Summary:    Development files for %{name}
Requires:   %{name}%{?_isa} = %{version}-%{release}

# provide headers package
Provides:   %{name}-headers%{?_isa} = %{version}-%{release}

%description devel %_description

%package doc
BuildArch:  noarch
Summary:    Documentation for %{name}

%description doc %_description


%package -n python3-%{name}
Summary:    Python3 bindings for nest
Requires:   %{name} = %{version}-%{release}
Requires:   %{name}-common = %{version}-%{release}
Requires:   %{py3_dist numpy} %{py3_dist scipy}
Recommends: %{py3_dist matplotlib}
Recommends: %{py3_dist ipython}
%{?python_provide:%python_provide python3-%{name}}

%description -n python3-%{name} %_description

%if %{with openmpi}
%package openmpi
Summary:        %{name} built with openmpi
BuildRequires:  openmpi-devel
BuildRequires:  rpm-mpi-hooks
BuildRequires:  libneurosim-openmpi-devel
BuildRequires:  MUSIC-openmpi-devel
BuildRequires:  MUSIC-openmpi
Requires:       openmpi
Requires:       %{name}-openmpi-common = %{version}-%{release}

%description openmpi %_description

%package openmpi-common
Summary:    Common files for %{name} built with openmpi support

%description openmpi-common %_description

%package openmpi-devel
Summary:    Development files for %{name} built with openmpi support
Requires:   %{name}-openmpi%{?_isa} = %{version}-%{release}

# provide headers package
Provides:   %{name}-openmpi-headers%{?_isa} = %{version}-%{release}

%description openmpi-devel %_description

%package -n python3-%{name}-openmpi
Summary:    Python3 bindings for nest with openmpi support
BuildRequires:  rpm-mpi-hooks
Requires:   openmpi
Requires:   %{name}-openmpi = %{version}-%{release}
Requires:   %{name}-openmpi-common = %{version}-%{release}
Requires:   %{py3_dist numpy} %{py3_dist scipy}
Recommends: %{py3_dist matplotlib}
Recommends: %{py3_dist ipython}
%{?python_provide:%python_provide python3-%{name}-openmpi}

%description -n python3-%{name}-openmpi %_description
%endif

%if %{with mpich}
%package mpich
Summary:        %{name} built with mpich
BuildRequires:  mpich-devel
BuildRequires:  rpm-mpi-hooks
BuildRequires:  libneurosim-mpich-devel
BuildRequires:  MUSIC-mpich-devel
BuildRequires:  MUSIC-mpich
Requires:       mpich
Requires:       %{name}-mpich-common = %{version}-%{release}

%description mpich %_description

%package mpich-common
Summary:    Common files for %{name} built with mpich support

%description mpich-common %_description

%package mpich-devel
Summary:    Header files for %{name} built with mpich support
Requires:   %{name}-mpich%{?_isa} = %{version}-%{release}

# provide headers package
Provides:   %{name}-mpich-headers%{?_isa} = %{version}-%{release}

%description mpich-devel %_description


%package -n python3-%{name}-mpich
Summary:    Python3 bindings for nest with mpich support
BuildRequires:  rpm-mpi-hooks
Requires:   %{name}-mpich = %{version}-%{release}
Requires:   %{name}-mpich-common = %{version}-%{release}
Requires:   mpich
Requires:   %{py3_dist numpy} %{py3_dist scipy}
Recommends: %{py3_dist matplotlib}
Recommends: %{py3_dist ipython}
%{?python_provide:%python_provide python3-%{name}-mpich}

%description -n python3-%{name}-mpich %_description
%endif

%prep
%forgeautosetup -p1
cp %{SOURCE1} ./ -v

# Fix VERSION
# TODO: Check if needed with each release
echo %{version} > VERSION


# Tweaks
# We'll set it ourselves - easier for mpi implementations
sed -i.orig '/PYEXECDIR/ d' cmake/ProcessOptions.cmake
# These files are all in standard locations so we don't need them
# Loading an MPI module sets up PATH correctly
sed -i '/PATH=/ d' bin/nest_vars.sh.in
# correct output of --libs in nest-config
# it does not need $prefix there
sed -i 's|-L$prefix/|-L|' bin/nest-config.in
# Delete bundled Random123 copy
rm -rf thirdparty/Random123

# Correct shebangs for py3
find . -name "*.py" -exec sed -i 's|#!/usr/bin/env python.*|#!/usr/bin/python3|' '{}' \;

# builddir for serial
mkdir build-serial

%if %{with mpich}
    mkdir build-mpich
%endif

%if %{with openmpi}
    mkdir build-openmpi
%endif


%build

%global do_cmake_config \
echo  \
echo "*** BUILDING %{name}$MPI_COMPILE_TYPE ***"  \
export PYEXECDIR=$MPI_SITEARCH  \
%set_build_flags \
echo  \
pushd build$MPI_COMPILE_TYPE  && \
    cmake \\\
        -DCMAKE_C_FLAGS_RELEASE:STRING="-DNDEBUG" \\\
        -DCMAKE_CXX_FLAGS_RELEASE:STRING="-DNDEBUG" \\\
        -DCMAKE_Fortran_FLAGS_RELEASE:STRING="-DNDEBUG" \\\
        -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON \\\
        -DCMAKE_INSTALL_INCLUDEDIR:PATH=$MPI_INCLUDE \\\
        -DCMAKE_INSTALL_LIBDIR:PATH=$MPI_LIB \\\
        -DSYSCONF_INSTALL_DIR:PATH=%{_sysconfdir} \\\
        -DSHARE_INSTALL_PREFIX:PATH=%{_prefix} \\\
        -Dwith-optimize:BOOL=OFF \\\
        -DCMAKE_SKIP_RPATH:BOOL=ON \\\
        -DCMAKE_SKIP_BUILD_RPATH:BOOL=ON \\\
        -DCMAKE_SKIP_INSTALL_RPATH:BOOL=ON \\\
        -DCMAKE_BUILD_WITH_INSTALL_RPATH:BOOL=OFF \\\
        -Dwith-mpi:BOOL=$MPI_YES \\\
        -Dwith-gsl:BOOL=ON \\\
        -Dwith-boost:BOOL=ON \\\
        -Dwith-libneurosim:PATH=$MPI_HOME \\\
        -Dwith-python:BOOL=ON  \\\
        -DPYEXECDIR:PATH=$MPI_SITEARCH \\\
        -DCMAKE_INSTALL_PREFIX:PATH=$MPI_HOME \\\
        -DBUILD_SHARED_LIBS:BOOL=ON \\\
        -DPY_MPI4PY:PATH=$PY_MPI4PY \\\
        -DHAVE_RANDOM_123:BOOL=ON \\\
%if %{music} \
        -Dwith-music:BOOL=ON \\\
        -DMUSIC_INCLUDE_DIR:PATH=$MPI_INCLUDE \\\
        -DMUSIC_LIBRARY:PATH=$MPI_LIB/libmusic.so \\\
        -DMUSIC_EXECUTABLE:PATH=$MPI_BIN/music$MPI_SUFFIX \\\
%else \
        -Dwith-music:BOOL=OFF \\\
%endif \
%if "%{_lib}" == "lib64" \
        -DLIB_SUFFIX=64 .. && \
%else                      \
        -DLIB_SUFFIX="" .. && \
%endif \
popd || exit -1;

%global do_make_build \
    %make_build -j%{numthreads} -C build$MPI_COMPILE_TYPE || exit -1

%global do_pybuild \
pushd build$MPI_COMPILE_TYPE  && \
    pushd pynest && \
        # Create nest/lib dir manually or build fails \
        mkdir nest/lib \
        $PYTHON_BIN setup.py build \
    popd && \
popd || exit -1;

# Build serial version, dummy arguments
# Disable music, which requires MPI to be ON
%global music 0
export MPI_PYTHON3_SITEARCH="%{python3_sitearch}"
export MPI_COMPILER=serial
export MPI_SUFFIX=""
export MPI_HOME=%{_prefix}
export MPI_BIN=%{_bindir}
export MPI_INCLUDE=%{_includedir}
export MPI_LIB=%{_libdir}
export MPI_YES=OFF
export PY_MPI4PY=OFF
# Python 3
export MPI_COMPILE_TYPE="-serial"
export PYTHON_VERSION="3"
export PYTHON_BIN="%{python3}"
export MPI_SITEARCH=$MPI_PYTHON3_SITEARCH
%{do_cmake_config}
%{do_make_build}
%{do_pybuild}

# (1) Change configuration slightly for the MPI builds, We want the stuff
# from doc/, examples/, and testsuite/ dirs only in the serial build.
# Backup CMakeLists.txt since we need to put it back for installation
# or nest_serial and nest_indirect will not be installed.
# Don't generate docs for MPI builds
# Don't install examples and extras for MPI builds
# Don't install tests in docdir either for MPI builds
sed -i.serial \
-e '/add_subdirectory.*doc/ d' \
-e '/add_subdirectory.*examples/ d' \
-e '/add_subdirectory.*testsuite/ d' CMakeLists.txt

# Enable music support
%global music 1
# Build mpich version
%if %{with mpich}
%{_mpich_load}
export CC=mpicc
export CXX=mpicxx
export FC=mpif90
export F77=mpif77
export MPI_YES=ON
# Python 3
export MPI_COMPILE_TYPE="-mpich"
export PYTHON_VERSION="3"
export PYTHON_BIN="%{python3}"
export MPI_SITEARCH=$MPI_PYTHON3_SITEARCH
export PY_MPI4PY=$MPI_PYTHON3_SITEARCH/mpi4py
%{do_cmake_config}
%{do_make_build}
%{do_pybuild}

%{_mpich_unload}
%endif

# Build OpenMPI version
# Disable MUSIC support. OpenMPI build fails with MUSIC enabled.
%global music 0
%if %{with openmpi}
%{_openmpi_load}
export CC=mpicc
export CXX=mpicxx
export FC=mpif90
export F77=mpif77
export MPI_YES=ON
# Python 3
export MPI_COMPILE_TYPE="-openmpi"
export PYTHON_VERSION="3"
export PYTHON_BIN="%{python3}"
export MPI_SITEARCH=$MPI_PYTHON3_SITEARCH
export PY_MPI4PY=$MPI_PYTHON3_SITEARCH/mpi4py
%{do_cmake_config}
%{do_make_build}
%{do_pybuild}

%{_openmpi_unload}
%endif

%install
# Install everything
%global do_install \
echo  \
echo "*** INSTALLING %{name}$MPI_COMPILE_TYPE ***"  \
echo  \
    %make_install -C build$MPI_COMPILE_TYPE || exit -1


# Install the other python bits
%global do_pyinstall \
pushd build$MPI_COMPILE_TYPE && \
    pushd pynest && \
        $PYTHON_BIN setup.py install --skip-build --root $RPM_BUILD_ROOT --install-lib=$MPI_SITEARCH && \
    popd && \
popd || exit -1;


# (2) Put the original CMakeLists.txt back into place for installation
mv -v CMakeLists.txt CMakeLists.txt.mpi
mv -v CMakeLists.txt.serial CMakeLists.txt

# install serial version
export MPI_SUFFIX=""
export MPI_HOME=%{_prefix}
export MPI_BIN=%{_bindir}
export MPI_YES=OFF
# Python 3
export MPI_COMPILE_TYPE="-serial"
export MPI_SITEARCH="%{python3_sitearch}"
export PYTHON_BIN="%{python3}"
%{do_install}
%{do_pyinstall}

# (3) Swap again for MPI installations
mv -v CMakeLists.txt CMakeLists.txt.serial
mv -v CMakeLists.txt.mpi CMakeLists.txt

# Install MPICH version
%if %{with mpich}
%{_mpich_load}
# Python 3
export MPI_COMPILE_TYPE="-mpich"
export MPI_SITEARCH=$MPI_PYTHON3_SITEARCH
export PYTHON_BIN="%{python3}"
%{do_install}
%{do_pyinstall}

# Remove duplicated docs
rm -rf $RPM_BUILD_ROOT/%{_libdir}/mpich/share/doc/%{name}
# Remove unneeded scripts
rm -rf $RPM_BUILD_ROOT/%{_libdir}/mpich/share/%{name}/{slihelp_generator}

# Rename binaries to add MPI suffix
pushd $RPM_BUILD_ROOT/$MPI_BIN/
    mv -v %{name}{,$MPI_SUFFIX}
    mv -v %{name}-server{,$MPI_SUFFIX}
    mv -v %{name}-server-mpi{,$MPI_SUFFIX}
    mv -v %{name}_vars{,$MPI_SUFFIX}.sh
    mv -v %{name}-config{,$MPI_SUFFIX}
    mv -v sli{,$MPI_SUFFIX}
popd

# Remove rpath
chrpath --delete $RPM_BUILD_ROOT/$MPI_PYTHON3_SITEARCH/nest/pynestkernel.so
chrpath --delete $RPM_BUILD_ROOT/$MPI_BIN/sli_mpich
chrpath --delete $RPM_BUILD_ROOT/$MPI_BIN/nest_mpich
chrpath --delete $RPM_BUILD_ROOT/$MPI_LIB/libsli_readline.so
chrpath --delete $RPM_BUILD_ROOT/$MPI_LIB/libsli.so
chrpath --delete $RPM_BUILD_ROOT/$MPI_LIB/libnest.so

%{_mpich_unload}
%endif

# Install OpenMPI version
%if %{with openmpi}
%{_openmpi_load}
# Python 3
export MPI_COMPILE_TYPE="-openmpi"
export MPI_SITEARCH=$MPI_PYTHON3_SITEARCH
export PYTHON_BIN="%{python3}"
%{do_install}
%{do_pyinstall}

# Remove duplicated docs
rm -rf $RPM_BUILD_ROOT/%{_libdir}/openmpi/share/doc/%{name}
# Correct doc location
sed -i 's|NEST_DOC_DIR=$NEST_INSTALL_DIR/share/doc/nest|NEST_DOC_DIR=/usr/share/doc/nest/|' $RPM_BUILD_ROOT/$MPI_BIN/nest_vars.sh
# Remove duplicated scripts
rm -rf $RPM_BUILD_ROOT/%{_libdir}/openmpi/share/%{name}/{slihelp_generator}

# Rename binaries to add MPI suffix
pushd $RPM_BUILD_ROOT/$MPI_BIN/
    mv -v %{name}{,$MPI_SUFFIX}
    mv -v %{name}-server{,$MPI_SUFFIX}
    mv -v %{name}-server-mpi{,$MPI_SUFFIX}
    mv -v %{name}_vars{,$MPI_SUFFIX}.sh
    mv -v %{name}-config{,$MPI_SUFFIX}
    mv -v sli{,$MPI_SUFFIX}
popd

# Remove rpath
chrpath --delete $RPM_BUILD_ROOT/$MPI_PYTHON3_SITEARCH/nest/pynestkernel.so
chrpath --delete $RPM_BUILD_ROOT/$MPI_BIN/sli_openmpi
chrpath --delete $RPM_BUILD_ROOT/$MPI_BIN/nest_openmpi
chrpath --delete $RPM_BUILD_ROOT/$MPI_LIB/libsli_readline.so
chrpath --delete $RPM_BUILD_ROOT/$MPI_LIB/libsli.so
chrpath --delete $RPM_BUILD_ROOT/$MPI_LIB/libnest.so

%{_openmpi_unload}
%endif

# Remove test suite so that it isn't included in the package
rm -rf $RPM_BUILD_ROOT/%{_datadir}/nest/testsuite/
rm -rf $RPM_BUILD_ROOT/%{_bindir}/run_all_cpptests

%if %{with mpich}
%{_mpich_load}
rm -rf $RPM_BUILD_ROOT/$MPI_HOME/share/nest/testsuite/
%{_mpich_unload}
%endif
%if %{with openmpi}
%{_openmpi_load}
rm -rf $RPM_BUILD_ROOT/$MPI_HOME/share/nest/testsuite/
%{_openmpi_unload}
%endif

%check
# Cannot run py3_check_import because importing nest does not work in a chroot,
# and there's no way to tweak the location it searches (/usr/share/nest/) to
# include the buildroot before invoking it. Previously, it listened to
# environment variables, but that seems to have been removed in v3. So we'll
# need to build, then install the rpms and then test import :/
# See sli/slistartup.cc

# upstream tests
%if %{with tests}
%global do_tests_3 \
echo  \
echo "*** TESTING %{name}$MPI_COMPILE_TYPE ***"  \
echo  \
PATH=$RPM_BUILD_ROOT/$NEST_BINDIR/:$PATH $RPM_BUILD_ROOT/$NEST_DATA_DIR/testsuite/do_tests.sh --source-dir=SKIP \
%{pytest} $NEST_PYTHONDIR/nest/tests


export MPI_COMPILE_TYPE="-serial"
export NEST_BINDIR="%{_bindir}"
export PYTHON_VERSION="3"
export PYTHON_BIN="%{python3}"
export NEST_PYTHONDIR=%{python3_sitearch}
%{do_tests_3}

# Test mpich version
%if %{with mpich}
%{_mpich_load}
export MPI_COMPILE_TYPE="-mpich"
export NEST_BINDIR=$MPI_BIN
export NEST_PYTHONDIR=$MPI_PYTHON3_SITEARCH
export PYTHON_VERSION="3"
export PYTHON_BIN="%{python3}"
%{do_tests_3}

%{_mpich_unload}
%endif

# Test OpenMPI version
%if %{with openmpi}
%{_openmpi_load}
export MPI_COMPILE_TYPE="-openmpi"
export PYTHON_VERSION="3"
export PYTHON_BIN="%{python3}"
export MPI_SITEARCH=$MPI_PYTHON3_SITEARCH
%{do_tests_3}

%{_openmpi_unload}
%endif
%endif

# remove LICENSE file from docs
rm -v %{buildroot}/%{_pkgdocdir}/LICENSE


%files
%license LICENSE
%doc README-Fedora.md SECURITY.md ACKNOWLEDGMENTS.md README.md CHANGES CONTRIBUTING.md
%{_bindir}/%{name}
%{_bindir}/%{name}-server
%{_bindir}/%{name}-server-mpi
%{_bindir}/sli
%{_bindir}/%{name}_vars.sh
%{_bindir}/%{name}-config
%{_bindir}/%{name}_serial
%{_bindir}/%{name}_indirect
%{_libdir}/*.so.3*

%files common
%license LICENSE
%{_datadir}/%{name}

%files devel
%{_includedir}/%{name}
%{_libdir}/*.so

%files doc
%license LICENSE
%doc %{_pkgdocdir}/EditorSupport
%doc %{_pkgdocdir}/examples
%doc %{_pkgdocdir}/run_examples.sh

%files -n python3-%{name}
%{python3_sitearch}/%{name}
%{python3_sitearch}/nest_simulator-%{version}-py%{python3_version}.egg-info

%if %{with mpich}
%files mpich
%license LICENSE
%doc README-Fedora.md SECURITY.md ACKNOWLEDGMENTS.md README.md CHANGES CONTRIBUTING.md
%{_libdir}/mpich/bin/%{name}_mpich
%{_libdir}/mpich/bin/%{name}-server_mpich
%{_libdir}/mpich/bin/%{name}-server-mpi_mpich
%{_libdir}/mpich/bin/%{name}_vars_mpich.sh
%{_libdir}/mpich/bin/%{name}-config_mpich
%{_libdir}/mpich/bin/sli_mpich
%{_libdir}/mpich/lib/*.so.3*

%files mpich-common
%license LICENSE
%{_libdir}/mpich/share/%{name}

%files mpich-devel
%{_includedir}/mpich-%{_arch}/%{name}
%{_libdir}/mpich/lib/*.so

%files -n python3-%{name}-mpich
%license LICENSE
%{python3_sitearch}/mpich/%{name}
%{python3_sitearch}/mpich/nest_simulator-%{version}-py%{python3_version}.egg-info
%endif

%if %{with openmpi}
%files openmpi
%license LICENSE
%doc README-Fedora.md SECURITY.md ACKNOWLEDGMENTS.md README.md CHANGES CONTRIBUTING.md
%{_libdir}/openmpi/bin/%{name}_openmpi
%{_libdir}/openmpi/bin/%{name}-server_openmpi
%{_libdir}/openmpi/bin/%{name}-server-mpi_openmpi
%{_libdir}/openmpi/bin/%{name}_vars_openmpi.sh
%{_libdir}/openmpi/bin/%{name}-config_openmpi
%{_libdir}/openmpi/bin/sli_openmpi
%{_libdir}/openmpi/lib/*.so.3*

%files openmpi-common
%license LICENSE
%{_libdir}/openmpi/share/%{name}

%files openmpi-devel
%{_includedir}/openmpi-%{_arch}/%{name}
%{_libdir}/openmpi/lib/*.so

%files -n python3-%{name}-openmpi
%license LICENSE
%{python3_sitearch}/openmpi/%{name}
%{python3_sitearch}/openmpi/nest_simulator-%{version}-py%{python3_version}.egg-info
%endif

%changelog
%autochangelog
