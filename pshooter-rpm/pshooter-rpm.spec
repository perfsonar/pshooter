#
# RPM Spec for pSshooter RPM Macros
#

# TODO: Some of these macros may be unused.

Name:		pshooter-rpm
Version:	1.0
Release:	%{version}%{?dist}

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
cat > $RPM_BUILD_ROOT/%{macro_prefix}%{name} <<EOF
#
# Macros used in building pshooter RPMs  (Version %{version})
#

# TODO: This needs to be scrubbed of unused items.

%%_pshooter_api_root https://localhost/pshooter 

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
%%_pshooter_sudoersdir %{_sysconfdir}/sudoers.d
%%_pshooter_docdir %{_defaultdocdir}/pshooter
%%_pshooter_datadir %{_datadir}/pshooter
%%_pshooter_vardir %{_var}/lib/pshooter

# Where RPM Macros live
%%_pshooter_rpmmacrodir %{macro_dir}
# Prefix for all macro files.  Use as %{_pshooter_rpmmacroprefix}foo
%%_pshooter_rpmmacroprefix %{macro_prefix}

# Internal commands
%%_pshooter_internals %{_pshooter_libexecdir}/internals

# Where all classes live
%%_pshooter_classes %{_pshooter_libexecdir}/classes

# Tests
%%_pshooter_test_libexec %{_pshooter_classes}/test
%%_pshooter_test_doc %{_pshooter_docdir}/test
%%_pshooter_test_confdir %{_pshooter_sysconfdir}/test

# Tools
%%_pshooter_tool_libexec %{_pshooter_classes}/tool
%%_pshooter_tool_doc %{_pshooter_docdir}/tool
%%_pshooter_tool_confdir %{_pshooter_sysconfdir}/tool
%%_pshooter_tool_vardir %{_pshooter_vardir}/tool

# Archivers
%%_pshooter_archiver_libexec %{_pshooter_classes}/archiver
%%_pshooter_archiver_doc %{_pshooter_docdir}/archiver

# Context Changers
%%_pshooter_context_libexec %{_pshooter_classes}/context
%%_pshooter_context_doc %{_pshooter_docdir}/context

# pshooter front-end comands
%%_pshooter_commands %{_pshooter_libexecdir}/commands

# pshooter daemons
%%_pshooter_daemons %{_pshooter_libexecdir}/daemons

EOF


%files
%attr(444,root,root) %{macro_prefix}*
