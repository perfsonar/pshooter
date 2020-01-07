#
# RPM Spec for pShooter Account
#

Name:		pshooter-account
Version:	0.1.0
Release:	%{?dist}

Summary:	Account for pshooter
BuildArch:	noarch

License:	ASL 2.0
Vendor:	perfSONAR
Group:		Unspecified

# No Source:

Provides:	%{name} = %{version}-%{release}

BuildRequires:	pshooter-rpm
Requires: shadow-utils
Requires(post): shadow-utils

%define user pshooter
%define group pshooter
%define gecos pShooter

%define macros %{_pshooter_rpmmacroprefix}%{name}

%description
This package creates an account and group for pshooter.

%install

mkdir -p $RPM_BUILD_ROOT/%{_pshooter_rpmmacrodir}
cat > $RPM_BUILD_ROOT/%{macros} <<EOF
#
# RPM Macros for %{name} Version %{version}
#

%%_pshooter_user %{user}
%%_pshooter_group %{group}
EOF


%post

if [ $1 -eq 1 ]  # One instance, new install
then
    groupadd '%{group}'

    # Note: The default behavior for this is to have the password
    # disabled.  That makes it su-able but not login-able.
    useradd -c '%{gecos}' -g '%{group}' '%{user}'
fi

# Make sure the account is never never disabled or requires a password
# change.  Do this under all conditions to bring older versions into
# line.

chage \
    --expiredate -1 \
    --inactive -1 \
    --maxdays 99999 \
    '%{user}'



%postun
if [ $1 -eq 0 ]  # No more instances left.
then
    # This takes the group with it.
    userdel -r -f '%{user}'
fi


%files
%attr(444,root,root) %{_pshooter_rpmmacroprefix}*
