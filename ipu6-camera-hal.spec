%global commit 884b81aae0ea19a974eb8ccdaeef93038136bdd4
%global commitdate 20230208
%global shortcommit %(c=%{commit}; echo ${c:0:7})

# We want to specify multiple separate build-dirs for the different variants
%global __cmake_in_source_build 1

Name:           ipu6-camera-hal
Summary:        Hardware abstraction layer for Intel IPU6
URL:            https://github.com/intel/ipu6-camera-hal
Version:        0.0
Release:        16.%{commitdate}git%{shortcommit}%{?dist}
License:        Apache-2.0

Source0:        https://github.com/intel/%{name}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        60-intel-ipu6.rules
Source2:        v4l2-relayd-adl
Source3:        v4l2-relayd-tgl
Source4:        intel_ipu6_isys.conf

# Patches

BuildRequires:  systemd-rpm-macros
BuildRequires:  ipu6-camera-bins-devel
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  g++
BuildRequires:  expat-devel

ExclusiveArch:  x86_64

Requires:       ipu6-camera-bins

%description
ipu6-camera-hal provides the basic hardware access APIs for IPU6.

%package devel
Summary:        IPU6 header files for HAL
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       ipu6-camera-bins-devel

%description devel
This provides the necessary header files for IPU6 HAL development.

%prep
%autosetup -p1 -n %{name}-%{commit}


%build
for i in ipu6 ipu6ep; do
  export PKG_CONFIG_PATH=%{_libdir}/$i/pkgconfig/
  export LDFLAGS="$RPM_LD_FLAGS -Wl,-rpath=%{_libdir}/$i"
  sed -i.orig "s|/usr/share/defaults/etc/camera/|/usr/share/defaults/etc/$i/|g" \
    src/platformdata/PlatformData.h
  mkdir $i && pushd $i
  %cmake -DCMAKE_BUILD_TYPE=Release -DIPU_VER=$i \
         -DENABLE_VIRTUAL_IPU_PIPE=OFF -DUSE_PG_LITE_PIPE=ON \
         -DUSE_STATIC_GRAPH=OFF ..
  %make_build
  popd
  mv src/platformdata/PlatformData.h.orig src/platformdata/PlatformData.h
done


%install
for i in ipu6 ipu6ep; do
  pushd $i
  %make_install
  mkdir %{buildroot}%{_libdir}/$i
  mv %{buildroot}%{_libdir}/libcamhal.so %{buildroot}%{_libdir}/$i/
  mv %{buildroot}%{_datadir}/defaults/etc/camera %{buildroot}%{_datadir}/defaults/etc/$i
  popd
done

# We don't want static libs
rm %{buildroot}%{_libdir}/libcamhal.a

# symbolic link + udev is used to resolve the library name conflict. 
ln -sf %{_rundir}/libcamhal.so %{buildroot}%{_libdir}/libcamhal.so
install -p -m 0644 -D %{SOURCE1} %{buildroot}%{_udevrulesdir}/60-intel-ipu6.rules

# Make sure libcamhal.so can be found when building code on systems without an IPU6
sed -i -e "s|}/lib64|}/lib64/ipu6|" %{buildroot}%{_libdir}/pkgconfig/libcamhal.pc

# v4l2-relayd configuration examples
install -p -D -m 0644 %{SOURCE2} %{buildroot}%{_datadir}/defaults/etc/ipu6ep/v4l2-relayd
install -p -D -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/defaults/etc/ipu6/v4l2-relayd

# Make kmod-intel-ipu6 use /dev/video7 leaving /dev/video0 for loopback
install -p -D -m 0644 %{SOURCE4} %{buildroot}%{_modprobedir}/intel_ipu6_isys.conf


%post
# skip triggering if udevd isn't even accessible, e.g. containers or
# rpm-ostree-based systems
if [ -S /run/udev/control ]; then
    /usr/bin/udevadm control --reload
    /usr/bin/udevadm trigger /sys/devices/pci0000:00/0000:00:05.0
fi


%files
%license LICENSE
%{_libdir}/*/libcamhal.so
%{_libdir}/libcamhal.so
%{_datadir}/defaults/etc/*
%{_modprobedir}/intel_ipu6_isys.conf
%{_udevrulesdir}/60-intel-ipu6.rules


%files devel
%{_includedir}/libcamhal
%{_libdir}/pkgconfig/libcamhal.pc


%changelog
* Tue Oct 10 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-16.20230208git884b81a
- Update /lib/modprobe.d/intel_ipu6_isys.conf for newer versions of
  intel-ipu6-kmod creating up to 8 /dev/video# nodes

* Tue Aug 08 2023 Kate Hsuan <hpa@redhat.com> - 0.0-15.20230208git884b81a
- Updated to commit 884b81aae0ea19a974eb8ccdaeef93038136bdd4

* Thu Aug 03 2023 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-14.20221112gitcc0b859
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Thu Jun  8 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-13.20221112gitcc0b859
- Add Raptor Lake IPU6EP PCI-id to 60-intel-ipu6.rules

* Tue May 30 2023 Kate Hsuan <hpa@redhat.com> - 0.0-12.20221112gitcc0b859
- Fix 11 and skip udev command for container and rpm-ostree environments

* Mon May 29 2023 Kate Hsuan <hpa@redhat.com> - 0.0-11.20221112gitcc0b859
- Add a sysfs path check for rpm-ostree since udev is unable to access in a container

* Mon May 15 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-10.20221112gitcc0b859
- Add intel_ipu6_isys.conf to make ipu6-driver not clobber /dev/video0

* Mon May 08 2023 Kate Hsuan <hpa@redhat.com> - 0.0-9.20221112gitcc0b859
- Fix settings for Tiger lake CPU

* Wed Mar 22 2023 Kate Hsuan <hpa@redhat.com> - 0.0-8.20221112gitcc0b859
- Included v4l2-relayd configuration examples

* Mon Mar 20 2023 Kate Hsuan <hpa@redhat.com> - 0.0-7.20221112gitcc0b859
- udev rules for supporting v4l2-relayd

* Wed Feb 15 2023 Kate Hsuan <hpa@redhat.com> - 0.0-6.20221112gitcc0b859
- Allow ordinary users to access the camera

* Fri Feb 3 2023 Kate Hsuan <hpa@redhat.com> - 0.0-5.20221112gitcc0b859
- Patch path settings for the configuration files
- Remove udev workaround
- Fix rpmlint warnings

* Tue Jan 31 2023 Kate Hsuan <hpa@redhat.com> - 0.0-4.20221112gitcc0b859
- Remove udev scripts and the simplified rules are used
- Fix and patch gcc13 compile issues

* Tue Jan 17 2023 Kate Hsuan <hpa@redhat.com> - 0.0-3.20221112gitcc0b859
- Add symbolic link for camera configuration files

* Fri Nov 25 2022 Kate Hsuan <hpa@redhat.com> - 0.0-2.20221112gitcc0b859
- push udev rules
- format and style fixes

* Fri Nov 25 2022 Kate Hsuan <hpa@redhat.com> - 0.0-1.20221112gitcc0b859
- First commit
