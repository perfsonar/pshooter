dnl
dnl Build Order for pSshooter RPMs
dnl
dnl
dnl Pre-process with M4.
dnl
dnl
changequote(<!,!>)dnl
changecom()dnl
dnl
#
# Packages must be listed in an order where dependent packages are
# built after their dependencies.
#
#
# Options that can be added to a package line:
#
#  --bundle b   Include the package in bundle b and not the default
#               full bundle.
#

pshooter-rpm
pshooter-account
pshooter-server
