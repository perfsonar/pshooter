#
# RPM Spec for pShooter Server
#

# TODO: Need to write proper systemd services for this package and
# make the scriptlets use them on CentOS 7.  For now the old-style
# init scripts function just fine.

Name:		pshooter-server
Version:	1.1
Release:	0.2.b1%{?dist}

Summary:	pShooter Server
BuildArch:	noarch
License:	ASL 2.0
Vendor:		Internet2
Group:		Unspecified

Source0:	%{name}-%{version}.tar.gz

Provides:	%{name} = %{version}-%{release}


# Database
BuildRequires:	postgresql-init
BuildRequires:	postgresql-load
BuildRequires:	%{_pshooter_postgresql_package}-server

Requires:	drop-in
Requires:	gzip
Requires:	%{_pshooter_postgresql_package}-server
Requires:	postgresql-load
Requires:	pshooter-account
Requires:	pscheduler-database-init
Requires:	random-string >= 1.1

# Daemons
BuildRequires:	m4
Requires:	curl
Requires:	pshooter-account
Requires:	python-daemon
Requires:	python-flask

# TODO: Do we need these?
Requires:	python-ipaddr
Requires:	python-requests
Requires:	python-jsontemplate

# API Server
BuildRequires:	pshooter-account
BuildRequires:	pshooter-rpm
BuildRequires:	python-pscheduler >= 1.3.1.3
BuildRequires:	m4
Requires:	httpd-wsgi-socket
Requires:	pshooter-server
# Note that the actual definition of what protocol is used is part of
# python-pscheduler, but this package is what does the serving, so
# mod_ssl is required here.
Requires:	mod_ssl
Requires:	mod_wsgi
Requires:	python-pscheduler >= 1.3.1.3
Requires:	python-requests
Requires:	pytz


# General
BuildRequires:	pshooter-rpm

%if 0%{?el7}
BuildRequires:	systemd
%{?systemd_requires: %systemd_requires}
%endif

%description
The pShooter server


# Database

%define pgsql_service postgresql-%{_pshooter_postgresql_version}
%define pg_data %{_sharedstatedir}/pgsql/%{_pshooter_postgresql_version}/data

%define daemon_config_dir %{_pshooter_sysconfdir}/daemons
%define db_config_dir %{_pshooter_sysconfdir}/database
%define db_user %{_pshooter_user}
%define password_file %{db_config_dir}/database-password
%define database_name %{db_user}
%define dsn_file %{db_config_dir}/database-dsn
%define pgpass_file %{db_config_dir}/pgpassfile
%define rpm_macros %{_pshooter_rpmmacroprefix}%{name}

# Daemons
%define log_dir %{_var}/log/pshooter

# API Server
%define httpd_conf_d   %{_sysconfdir}/httpd/conf.d
%define api_httpd_conf %{httpd_conf_d}/pshooter-api-server.conf

%define server_conf_dir %{_pshooter_sysconfdir}

# Note that we want this here because it seems to work well without
# assistance on systems where selinux is enabled.  Anywhere else and
# there'd have to be a 'chcon -R -t httpd_user_content_t'.
%define api_dir	     %{_var}/www/%{name}

# ------------------------------------------------------------------------------

%prep

%if 0%{?el7} == 0
echo "This package cannot be built for %{dist}."
false
%endif
%setup -q


# ------------------------------------------------------------------------------

%build

#
# Database
#
make -C database \
     CHECK_SYNTAX=1 \
     DATABASE=%{db_user} \
     DATADIR=%{_pshooter_datadir} \
     PASSWORDFILE=%{password_file} \
     DSNFILE=%{dsn_file} \
     PGPASSFILE=%{pgpass_file} \
     ROLE=%{db_user} \
     PGPASSFILE=$RPM_BULID_ROOT/%{pgpass_file}

#
# Daemons
#
make -C daemons \
     COMMANDSDIR=$RPM_BUILD_ROOT/%{_pshooter_commands} \
     COMMANDSINSTALLED=%{_pshooter_commands} \
     CONFIGDIR=%{daemon_config_dir} \
     DAEMONDIR=%{_pshooter_daemons} \
     INTERNALSDIR=%{_pshooter_internals} \
     DSNFILE=%{dsn_file} \
     LOGDIR=%{log_dir} \
     PGDATABASE=%{database_name} \
     PGPASSFILE=%{_pshooter_database_pgpass_file} \
     PGSERVICE=%{pgsql_service}.service \
     PGUSER=%{_pshooter_database_user} \
     PSUSER=%{_pshooter_user} \
     RUNDIR=%{_rundir} \
     VAR=%{_var}

#
# API Server
#
# (Nothing)


# ------------------------------------------------------------------------------

%install

#
# Database
#
make -C database \
     DATADIR=$RPM_BUILD_ROOT/%{_pshooter_datadir} \
     INTERNALSDIR=$RPM_BUILD_ROOT/%{_pshooter_internals} \
     install

mkdir -p $RPM_BUILD_ROOT/%{db_config_dir}

# These will be populated on installation
for FILE in %{password_file} %{dsn_file} %{pgpass_file}
do
    DIR=$(dirname "$RPM_BUILD_ROOT/${FILE}")
    mkdir -p "${DIR}"
    touch "$RPM_BUILD_ROOT/${FILE}"
    chmod 440 "$RPM_BUILD_ROOT/${FILE}"
done

# RPM Macros
mkdir -p $(dirname $RPM_BUILD_ROOT/%{rpm_macros})
cat > $RPM_BUILD_ROOT/%{rpm_macros} <<EOF
# %{name} %{version}


# Database
%%_pshooter_database_user %{db_user}
%%_pshooter_database_name %{db_user}
%%_pshooter_database_dsn_file %{dsn_file}
%%_pshooter_database_password_file %{password_file}
%%_pshooter_database_pgpass_file %{pgpass_file}
EOF

%define profile_d %{_sysconfdir}/profile.d

# Shell Aliases
mkdir -p $RPM_BUILD_ROOT/%{profile_d}
cat > $RPM_BUILD_ROOT/%{profile_d}/%{name}.sh <<EOF
alias pshsql='PGPASSFILE=%{pgpass_file} psql -U pshooter'
EOF
cat > $RPM_BUILD_ROOT/%{profile_d}/%{name}.csh <<EOF
alias pshsql 'setenv PGPASSFILE "%{pgpass_file}" && psql -U pshooter'
EOF

#
# Daemons
#
make -C daemons \
     BINDIR=$RPM_BUILD_ROOT/%{_bindir} \
     CONFIGDIR=$RPM_BUILD_ROOT/%{daemon_config_dir} \
%if 0%{?el7}
     UNITDIR=$RPM_BUILD_ROOT/%{_unitdir} \
%endif
     DAEMONDIR=$RPM_BUILD_ROOT/%{_pshooter_daemons} \
     COMMANDDIR=$RPM_BUILD_ROOT/%{_pshooter_commands} \
     COMMANDSINSTALLED=%{_pshooter_commands} \
     install

mkdir -p $RPM_BUILD_ROOT/%{log_dir}

#
# API Server
#
API_ROOT=/pshooter

make -C api-server \
     'USER_NAME=%{_pshooter_user}' \
     'GROUP_NAME=%{_pshooter_group}' \
     "API_ROOT=${API_ROOT}" \
     "API_DIR=%{api_dir}" \
     "CONF_D=%{httpd_conf_d}" \
     "PREFIX=${RPM_BUILD_ROOT}" \
     "DSN_FILE=%{dsn_file}" \
     "LIMITS_FILE=%{_pshooter_limit_config}" \
     install

mkdir -p ${RPM_BUILD_ROOT}/%{server_conf_dir}

# ------------------------------------------------------------------------------

%pre

#
# Database
#

# (Nothing)


#
# Daemons
#
if [ "$1" -eq 2 ]
then
    for SERVICE in service
    do
        NAME="pshooter-${SERVICE}"
%if 0%{?el7}
        systemctl stop "${NAME}"
%endif
    done
fi

#
# API Server
#
# (Nothing)


# ------------------------------------------------------------------------------

%post

#
# Database
#

# Increase the number of connections to something substantial

%define pgsql_max_connections 500

# Note that this must be dropped in at the end so it overrides
# anything else in the file.
drop-in -n %{name} - "%{pg_data}/postgresql.conf" <<EOF
#
# pshooter
#
max_connections = %{pgsql_max_connections}
EOF


%if 0%{?el7}
systemctl enable "%{pgsql_service}"
systemctl start "%{pgsql_service}"
%endif

# Restart the server only if the current maximum connections is less
# than what we just installed.  This is more for development
# convenience than anything else since regular releases don't happen
# often.

SERVER_MAX=$( (echo "\\t" && echo "\\a" && echo "show max_connections") \
    | postgresql-load)

if [ "${SERVER_MAX}" -lt "%{pgsql_max_connections}" ]
then
%if 0%{?el7}
    systemctl restart "%{pgsql_service}"
%endif
fi




# Load the database

# TODO: Note that if this fails, the scriptlet stops but RPM doesn't
# exit zero.  This is apparently not getting fixed.
#
# Discussion:
#   https://bugzilla.redhat.com/show_bug.cgi?id=569930
#   http://rpm5.org/community/rpm-users/0834.html
#

pshooter internal db-update

# Note that this is safe to do because all of the daemons are stopped
# at this point and they, along with the web server, will be
# retstarted later.
pshooter internal db-change-password


#
# Allow the account we created to authenticate locally.
#

HBA_FILE=$( (echo "\t on" ; echo "show hba_file;") \
	    | postgresql-load \
	    | head -1 \
	    | sed -e 's/^\s*//' )

drop-in -n -t %{name} - "${HBA_FILE}" <<EOF
#
# pshooter
#
# This user should never need to access the database from anywhere
# other than locally.
#
%if 0%{?el7}
local     pshooter      pshooter                            md5
host      pshooter      pshooter     127.0.0.1/32           md5
host      pshooter      pshooter     ::1/128                md5
%endif
EOF

# Make Pg reload what we just changed.
postgresql-load <<EOF
DO \$\$
DECLARE
    status BOOLEAN;
BEGIN
    SELECT INTO status pg_reload_conf();
    IF NOT status
    THEN
        RAISE EXCEPTION 'Failed to reload the server configuration';
    END IF;
END;
\$\$ LANGUAGE plpgsql;
EOF


#
# Daemons
#
%if 0%{?el7}
systemctl daemon-reload
%endif
for SERVICE in service
do
    NAME="pshooter-${SERVICE}"
%if 0%{?el7}
    systemctl enable "${NAME}"
    systemctl start "${NAME}"
%endif
done


# Some old installations ended up with root-owned files in the run
# directory.  Make their ownership correct.
# Note that this uses options specific to GNU Findutils.
find %{_rundir} -name "pshooter-*" ! -user "%{_pshooter_user}" -print0 \
    | xargs -0 -r chown "%{_pshooter_user}.%{_pshooter_group}"



#
# API Server
#
# On systems with SELINUX, allow database connections.
if selinuxenabled
then
    STATE=$(getsebool httpd_can_network_connect_db | awk '{ print $3 }')
    if [ "${STATE}" != "on" ]
    then
        echo "Setting SELinux permissions (may take awhile)"
        setsebool -P httpd_can_network_connect_db 1
    fi

    # HACK: BWCTLBC  Remove when BWCTL backward compatibility is removed.  See #107.
    STATE=$(getsebool httpd_can_network_connect | awk '{ print $3 }')
    if [ "${STATE}" != "on" ]
    then
        echo "Setting SELinux permissions (may take awhile)"
        setsebool -P httpd_can_network_connect 1
    fi

fi


%if 0%{?el7}
systemctl enable httpd
systemctl restart httpd
%endif


# ------------------------------------------------------------------------------

%preun
#
# Daemons
#
for SERVICE in service
do
    NAME="pshooter-${SERVICE}"
%if 0%{?el7}
    systemctl stop "${NAME}"
%endif
done

# Have to stop this while we're uninstalling so connections to the
# database go away.
%if 0%{?el7}
systemctl stop httpd
%endif


#
# API Server
#
# (Nothing)

#
# Database  (This has to be done after all services are stopped.)
#
if [ "$1" = "0" ]
then
    # Have to do this before the files are erased.
    postgresql-load %{_pshooter_datadir}/database-teardown.sql
fi


# ------------------------------------------------------------------------------

%postun

#only do this stuff if we are actually uninstalling
if [ "$1" = "0" ]; then
    #
    # Database
    #
    HBA_FILE=$( (echo "\t on" ; echo "show hba_file;") \
            | postgresql-load \
            | head -1 \
            | sed -e 's/^\s*//' )

    drop-in -r %{name} /dev/null $HBA_FILE

    drop-in -r %{name} /dev/null "%{pg_data}/postgresql.conf"

    # Removing the max_connections change requires a restart, which
    # will also catch the HBA changes.
%if 0%{?el7}
    systemctl restart "%{pgsql_service}"
%endif



    #
    # Daemons
    #
    # (Nothing)
%if 0%{?el7}
    systemctl daemon-reload
%endif



    #
    # API Server
    #
    # TODO: Determine if we want to shut this off, as other services might
    # be using it.
    # if selinuxenabled
    # then
    #     echo "Setting SELinux permissions (may take awhile)"
    #     setsebool -P httpd_can_network_connect_db 1
    # fi
else
    #we're doing an update so restart services
    for SERVICE in service
    do
        NAME="pshooter-${SERVICE}"
%if 0%{?el7}
        systemctl restart "${NAME}"
%endif
    done
fi

%if 0%{?el7}
systemctl start httpd
%endif


# ------------------------------------------------------------------------------

# Triggers

# Any upgrade of python-pscheduler needs to force a database restart
# because Pg doesn't see module upgrades.

%triggerin -- python-pscheduler
%if 0%{?el7}
systemctl restart "%{pgsql_service}"
%endif


# ------------------------------------------------------------------------------
%files

#
# Database
#
%defattr(-,%{_pshooter_user},%{_pshooter_group},-)
%license LICENSE
%{_pshooter_datadir}/*
%attr(400,-,-)%verify(user group mode) %{db_config_dir}/*
%{_pshooter_internals}/*
%{rpm_macros}
%{profile_d}/*

#
# Daemons
#

%defattr(-,root,root,-)
%license LICENSE
%attr(755,%{_pshooter_user},%{_pshooter_group})%verify(user group mode) %{daemon_config_dir}
%attr(600,%{_pshooter_user},%{_pshooter_group})%verify(user group mode) %config(noreplace) %{daemon_config_dir}/*
%{_bindir}/*
%if 0%{?el7}
%{_unitdir}/*
%endif
%{_pshooter_daemons}/*
%{_pshooter_commands}/*
%attr(750,%{_pshooter_user},%{_pshooter_group}) %{log_dir}

#
# API Server
#
%defattr(-,%{_pshooter_user},%{_pshooter_group},-)
%license LICENSE
%{api_dir}
%config(noreplace) %{api_httpd_conf}
