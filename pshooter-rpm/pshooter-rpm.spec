#
# RPM Spec for pSshooter RPM Macros
#

Name:		pshooter-rpm
Version:	0.1.0
Release:	%{?dist}

Summary:	Macros for use by pshooter RPM specs
BuildArch:	noarch
License:	ASL 2.0
Vendor:		Internet2
Group:		Unspecified

Provides:	%{name} = %{version}-%{release}

%description
Macros for use by pshooter RPM specs

# Where macros live
%define macro_dir %{_sysconfdir}/rpm
%define macro_prefix %{macro_dir}/macros.

# No punctuation between these is intentional.
%define macro_file %{macro_prefix}%{name}

%install
%{__mkdir_p} $RPM_BUILD_ROOT/%{macro_dir}
cat > $RPM_BUILD_ROOT/%{macro_file} <<EOF
#
# Macros used in building pshooter RPMs  (Version %{version})
#

%if %{?_rundir:0}%{!?_rundir:1}
# This didn't appear until EL7
%%_rundir %{_localstatedir}/run
%endif

# Minimum-required PostgreSQL version
%%_pshooter_postgresql_version_major 9
%%_pshooter_postgresql_version_minor 5
%%_pshooter_postgresql_version %{_pshooter_postgresql_version_major}.%{_pshooter_postgresql_version_minor}
%%_pshooter_postgresql_package postgresql%{_pshooter_postgresql_version_major}%{_pshooter_postgresql_version_minor}


%%_pshooter_libexecdir %{_libexecdir}/pshooter
%%_pshooter_sysconfdir %{_sysconfdir}/pshooter
%%_pshooter_datadir %{_datadir}/pshooter


# Where RPM Macros live
%%_pshooter_rpmmacrodir %{macro_dir}
# Prefix for all macro files.  Use as %{_pshooter_rpmmacroprefix}foo
%%_pshooter_rpmmacroprefix %{macro_prefix}

# Internal commands
%%_pshooter_internals %{_pshooter_libexecdir}/internals

# Where all classes live
%%_pshooter_classes %{_pshooter_libexecdir}/classes

# pshooter front-end comands
%%_pshooter_commands %{_pshooter_libexecdir}/commands

# pshooter daemons
%%_pshooter_daemons %{_pshooter_libexecdir}/daemons

EOF


%files
%attr(444,root,root) %{macro_prefix}*
