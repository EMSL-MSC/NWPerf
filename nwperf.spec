%define name nwperf
%define version 0.1
%define unmangled_version 0.1
%define release 1

Summary: A set of utilities for gathering and stroing performance information for clusters of computers
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: EMSL MSC team <UNKNOWN>
Url: https://github.com/EMSL-MSC/NWPerf/

%description
UNKNOWN

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
