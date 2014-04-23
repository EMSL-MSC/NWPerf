# Copyright 2013 Battelle Memorial Institute.
# This software is licensed under the Battelle “BSD-style” open source license;
# the full text of that license is available in the COPYING file in the root of the repository

%if 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

Summary: A set of utilities for gathering and storing performance information for clusters of computers
Name: nwperf
Version: 0.4
Release: 1
Source0: %{name}-%{version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch
Vendor: EMSL MSC team <UNKNOWN>
BuildRequires: python2-devel
Url: https://github.com/EMSL-MSC/NWPerf/

%description
UNKNOWN

%package web
Summary: The web bits to NWPerf
Group:         Applications/Communications
Requires:	httpd

%description web
UNKNOWN

# this is only for built .so shared objects
# but its handy to have just in case
%{?filter_setup:
%filter_provides_in %{python_sitearch}/.*\.so$
%filter_setup
}

%prep
%setup
%if 0%{?rhel} <= 6
cat << \EOF > %{name}-python-prov
#!/bin/sh
%{__python_provides} $* |\
sed -e '/.*Lib%{name}.so.*/d'
EOF

%global __python_provides %{_builddir}/%{name}-%{version}/%{name}-python-prov
chmod +x %{__python_provides}
%endif

%build
%{__python} setup.py build

%install
%{__python} setup.py install --root=%{buildroot}
%if 0%{?fedora} > 15
rm -rf %{buildroot}/etc/rc.d
%else
%if 0%{?rhel} < 6
rm -rf %{buildroot}/etc/init 
%else
rm -rf %{buildroot}/etc/rc.d
%endif
%endif

%if 0%{?rhel} <= 6
%clean
rm -rf %{buildroot}
%endif

%post
%if 0%{?fedora} > 15
%if 0%{?fedora} > 17
%systemd_post %{name}.service
%else
if [ $1 -eq 1 ] ; then
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
%endif
%else # EPEL thing
if [ $1 -eq 1 ] ; then
    # Initial installation 
    /sbin/chkconfig --add %{name}
fi
%endif

%preun
%if 0%{?fedora} > 15
%if 0%{?fedora} > 17
%systemd_preun %{name}.service
%else
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}.service > /dev/null 2>&1 || :
fi
%endif
%else # EPEL thing
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service %{name} stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del %{name} >/dev/null 2>&1 || :
fi
%endif

%postun
%if 0%{?fedora} > 15
%if 0%{?fedora} > 17
%systemd_postun_with_restart %{name}.service
%else
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi
%endif
%else #EPEL thing
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service %{name} condrestart
fi
%endif

%files
%defattr(-,root,root,-)
%if 0%{?fedora} > 15
%{_unitdir}/%{name}@.service
%{_unitdir}/%{name}-service.service
%else
%if 0%{?rhel} < 6
%{_sysconfdir}/rc.d/init.d/%{name}
%else
%{_sysconfdir}/init/%{name}.conf
%{_sysconfdir}/init/%{name}-service.conf
%endif
%endif
%{_sysconfdir}/nwperf.conf
%{_bindir}/*
%{_sbindir}/*
%{python_sitelib}/%{name}
%if 0%{?rhel}%{?fedora} > 5
%{python_sitelib}/%{name}-*egg-info
%endif

%files web
%defattr(-,root,root,-)

