%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?gtk_binary_version: %define gtk_binary_version %(pkg-config  --variable=gtk_binary_version gtk+-2.0)}

%define glib_ver %([ -a %{_libdir}/pkgconfig/glib-2.0.pc ] && pkg-config --modversion glib-2.0 | cut -d. -f 1,2 || echo -n "999")
%define gconf2_version 2.12.0
%define dbus_python_version 0.83.0
%define im_chooser_version 1.2.5

Name:       ibus
Version:    1.3.4
Release:    3%{?dist}
Summary:    Intelligent Input Bus for Linux OS
License:    LGPLv2+
Group:      System Environment/Libraries
URL:        http://code.google.com/p/ibus/
Source0:    http://ibus.googlecode.com/files/%{name}-%{version}.tar.gz
Source1:    xinput-ibus
Source2:    ibus-pt_BR.po
Patch0:     ibus-HEAD.patch
Patch1:     ibus-01-linguas.patch

BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)


BuildRequires:  cvs
BuildRequires:  gettext-devel
BuildRequires:  libtool
BuildRequires:  python
BuildRequires:  gtk2-devel
BuildRequires:  dbus-glib-devel
BuildRequires:  dbus-python-devel >= %{dbus_python_version}
BuildRequires:  desktop-file-utils
BuildRequires:  gtk-doc
BuildRequires:  GConf2-devel
BuildRequires:  pygobject2-devel
BuildRequires:  intltool
BuildRequires:  iso-codes-devel

Requires:   %{name}-libs = %{version}-%{release}
Requires:   %{name}-gtk = %{version}-%{release}

Requires:   pygtk2
Requires:   pyxdg
Requires:   iso-codes
Requires:   dbus-python >= %{dbus_python_version}
Requires:   im-chooser >= %{im_chooser_version}
Requires:   GConf2 >= %{gconf2_version}
Requires:   notify-python
Requires:   librsvg2

Requires(post):  desktop-file-utils
Requires(postun):  desktop-file-utils

Requires(pre): GConf2 >= %{gconf2_version}
Requires(post): GConf2 >= %{gconf2_version}
Requires(preun): GConf2 >= %{gconf2_version}

Requires(post):  %{_sbindir}/alternatives
Requires(postun):  %{_sbindir}/alternatives

Obsoletes:  ibus-qt < 1.1.0

%define _xinputconf %{_sysconfdir}/X11/xinit/xinput.d/ibus.conf

%description
IBus means Intelligent Input Bus. It is an input framework for Linux OS.

%package libs
Summary:    IBus libraries
Group:      System Environment/Libraries

Requires:   glib2 >= %{glib_ver}
Requires:   dbus >= 1.2.4

%description libs
This package contains the libraries for IBus

%package gtk
Summary:    IBus im module for gtk2
Group:      System Environment/Libraries
Requires:   %{name} = %{version}-%{release}
Requires(post): glib2 >= %{glib_ver}

%description gtk
This package contains ibus im module for gtk2

%package devel
Summary:    Development tools for ibus
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}
Requires:   glib2-devel
Requires:   dbus-devel

%description devel
The ibus-devel package contains the header files and developer
docs for ibus.

%package devel-docs
Summary:    Developer documents for ibus
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}

%description devel-docs
The ibus-devel-docs package contains developer documentation for ibus


%prep
%setup -q
if [ ! -f po/pt_BR.po ] ; then
    cp %SOURCE2 po/pt_BR.po
fi
%patch0 -p1
%patch1 -p1

%build
%configure --disable-static \
           --enable-gtk-doc
# make -C po update-gmo
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install
rm -f $RPM_BUILD_ROOT%{_libdir}/libibus.la
rm -f $RPM_BUILD_ROOT%{_libdir}/gtk-2.0/%{gtk_binary_version}/immodules/im-ibus.la

# install xinput config file
install -pm 644 -D %{SOURCE1} $RPM_BUILD_ROOT%{_xinputconf}

# install .desktop files
echo "NoDisplay=true" >> $RPM_BUILD_ROOT%{_datadir}/applications/ibus.desktop
echo "NoDisplay=true" >> $RPM_BUILD_ROOT%{_datadir}/applications/ibus-setup.desktop
echo "X-GNOME-Autostart-enabled=false" >> $RPM_BUILD_ROOT%{_sysconfdir}/xdg/autostart/ibus.desktop
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/xdg/autostart/ibus.desktop
desktop-file-install --delete-original          \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications \
  $RPM_BUILD_ROOT%{_datadir}/applications/*

%find_lang %{name}

%clean
rm -rf $RPM_BUILD_ROOT

%post
# recreate icon cache
touch --no-create %{_datadir}/icons/hicolor || :
[ -x %{_bindir}/gtk-update-icon-cache ] && \
  %{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :

%{_sbindir}/alternatives --install %{_sysconfdir}/X11/xinit/xinputrc xinputrc %{_xinputconf} 83 || :

export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
gconftool-2 --makefile-install-rule %{_sysconfdir}/gconf/schemas/ibus.schemas >& /dev/null || :

%pre
if [ "$1" -gt 1 ]; then
    export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
    gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/ibus.schemas >& /dev/null || :
fi

%preun
if [ "$1" -eq 0 ]; then
    export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
    gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/ibus.schemas >& /dev/null || :
fi

%postun
# recreate icon cache
touch --no-create %{_datadir}/icons/hicolor || :
[ -x %{_bindir}/gtk-update-icon-cache ] && \
  %{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :

if [ "$1" = "0" ]; then
  %{_sbindir}/alternatives --remove xinputrc %{_xinputconf} || :
  # if alternative was set to manual, reset to auto
  [ -L %{_sysconfdir}/alternatives/xinputrc -a "`readlink %{_sysconfdir}/alternatives/xinputrc`" = "%{_xinputconf}" ] && %{_sbindir}/alternatives --auto xinputrc || :
fi

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%post gtk
%{_bindir}/update-gtk-immodules %{_host} || :

%postun gtk
%{_bindir}/update-gtk-immodules %{_host} || :

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc AUTHORS COPYING README
%dir %{python_sitelib}/ibus
%{python_sitelib}/ibus/*
%dir %{_datadir}/ibus/
%{_bindir}/ibus-daemon
%{_bindir}/ibus-setup
%{_datadir}/ibus/*
%{_datadir}/applications/*
%{_datadir}/icons/hicolor/*/apps/*
%{_libexecdir}/ibus-gconf
%{_libexecdir}/ibus-ui-gtk
%{_libexecdir}/ibus-x11
# %{_sysconfdir}/xdg/autostart/ibus.desktop
%{_sysconfdir}/gconf/schemas/ibus.schemas
%config %{_xinputconf}

%files libs
%defattr(-,root,root,-)
%{_libdir}/libibus.so.*

%files gtk
%defattr(-,root,root,-)
%{_libdir}/gtk-2.0/%{gtk_binary_version}/immodules/im-ibus.so

%files devel
%defattr(-,root,root,-)
%{_libdir}/lib*.so
%{_includedir}/*
%{_libdir}/pkgconfig/*

%files devel-docs
%defattr(-,root,root,-)
%{_datadir}/gtk-doc/html/*

%changelog
* Mon Aug 09 2010 Takao Fujiwara <tfujiwar@redhat.com> - 1.3.4-3
- Resolves: #563053 Add pt_BR translation

* Tue Jul 06 2010 Takao Fujiwara <tfujiwar@redhat.com> - 1.3.4-2
- Revert the version not to be rebased.
- Fix bug 608988 - Cannot de-select Hanja lock in applet menu
  Resolves: #608988

* Tue Jul 06 2010 Takao Fujiwara <tfujiwar@redhat.com> - 1.3.6-1
- Update to 1.3.6
- Fix bug 608988 - Cannot de-select Hanja lock in applet menu
  Resolves: #608988

* Sat May 29 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.4-1
- Update to 1.3.4

* Tue May 04 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.3-1
- Update to 1.3.3

* Sun May 02 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.2-3
- Embedded language bar in menu by default.
- Fix bug 587353 - [abrt] crash in ibus-1.3.2-2.fc12

* Sat Apr 24 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.2-2
- Add requires librsvg2
- Update ibus-HEAD.patch: Update po files and and setting 

* Wed Apr 21 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.2-1
- Update to 1.3.2
- Fix bug 583446 - [abrt] crash in ibus-1.3.1-1.fc12

* Mon Apr 05 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.1-1
- Update to 1.3.1

* Fri Mar 26 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.0-3
- Update ibus-HEAD.patch
- Fix bug - some time panel does not show candidates.
- Update some po files

* Mon Mar 22 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.0-2
- Does not check glib micro version in ibus im module.

* Mon Mar 22 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.3.0-1
- Update to 1.3.0

* Tue Feb 02 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.2.99.20100202-1
- Update to 1.2.99.20100202

* Mon Jan 11 2010 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20100111-1
- Update to 1.2.0.20100111

* Fri Dec 25 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20091225-1
- Update to 1.2.0.20091225
- Fix bug 513895 - new IME does not show up in ibus-setup
- Fix bug 531857 - applet order should correspond with preferences order
- Fix bug 532856 - should not list already added input-methods in Add selector

* Wed Dec 15 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20091215-1
- Update to 1.2.0.20091215

* Thu Dec 10 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20091204-2
- Fix rpmlint warnings and errors.

* Fri Dec 04 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20091204-1
- Update to 1.2.0.20091204
- Fix Bug 529920 - language panel pops up on the wrong monitor
- Fix Bug 541197 - Ibus crash

* Tue Nov 24 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20091124-1
- Update to 1.2.0.20091124
- Update some translations.
- Fix bug 538147 - [abrt] crash detected in firefox-3.5.5-1.fc12 

* Sat Oct 24 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20091024-1
- Update to 1.2.0.20091024

* Wed Oct 14 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20091014-2
- Update to 1.2.0.20091014
- Change ICON in ibus.conf 

* Mon Sep 27 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090927-1
- Update to 1.2.0.20090927

* Tue Sep 15 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090915-1
- Update to 1.2.0.20090915
- Fix bug 521591 - check if the icon filename is a real file before trying to open it
- Fix bug 522310 - Memory leak on show/hide
- Fix bug 509518 - ibus-anthy should only override to jp layout for kana input

* Fri Sep 04 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090904-2
- Refresh the tarball.

* Fri Sep 04 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090904-1
- Update to 1.2.0.20090904

* Mon Aug 31 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090828-2
- Change icon path in ibus.conf

* Fri Aug 28 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090828-1
- Update to 1.2.0.20090828
- Change the icon on systray.
- Fix segment fault in ibus_hotkey_profile_destroy
- Fix some memory leaks.

* Wed Aug 12 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090812-1
- Update to 1.2.0.20090812

* Mon Aug 10 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090807-4
- Update ibus-HEAD.patch
- Fix Numlock problem.
- Fix some memory leaks.

* Fri Aug 07 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090807-2
- Update ibus-HEAD.patch
- Fix bug 516154.

* Fri Aug 07 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090807-1
- Update to 1.2.0.20090807

* Thu Aug 06 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090806-1
- Update to 1.2.0.20090806
- Fix bug 515106 - don't install duplicate files

* Tue Jul 28 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090723-3
- Update xinput-ibus: setup QT_IM_MODULE if the ibus qt input method plugin exists. 

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.0.20090723-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul 23 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090723-1
- Update to 1.2.0.20090723
- Fix dead loop in ibus-gconf

* Wed Jul 22 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090722-1
- Update to 1.2.0.20090722

* Sun Jul 19 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090719-1
- Update to 1.2.0.20090719

* Mon Jun 22 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.2.0.20090617-1
- Update to 1.2.0.20090617

* Fri Jun 12 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090612-1
- Update to 1.1.0.20090612
- Fix bug 504942 - PageUp and PageDown do not work in candidate list
- Fix bug 491040 - Implememnt mouse selection in candidate list

* Wed Jun 10 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090609-1
- Update to Update to 1.1.0.20090609
- Fix bug 502414 - Implemented on-screen help facility
- Fix bug 502561 - iBus should show keymap name on iBus panel
- Fix bug 498043 - ibus Alt-grave trigger conflicts with openoffice.org
- Implemented API for setting labels for candidates in LookupTable

* Sun May 31 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090531-1
- Update to Update to 1.1.0.20090531

* Tue May 26 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090508-5
- Update ibus-HEAD.patch.
- Show the default input method with bold text
- Add information text below input methods list

* Mon May 25 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090508-4
- Update ibus-HEAD.patch.
- Fix bug 501211 - ibus-setup window should be raised if running or just stay on top/grab focus
- Fix bug 501640 - ibus should adds new IMEs at end of engine list not beginning
- Fix bug 501644 - [IBus] focus-out and disabled IME should hide language panel

* Thu May 14 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090508-2
- Remove requires notification-daemon
- Fix bug 500588 - Hardcoded requirement for notification-daemon

* Fri May 08 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090508-1
- Update to 1.1.0.20090508
- Fix bug 499533 - [Indic] ibus should allow input in KDE using all supported Indic locales
- Fix bug 498352 - hotkey config table should list keys in same order as on main setup page
- Fix bug 497707 - ibus French translation update

* Fri May 08 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090423-3
- Fix bug 498541 - ibus-libs should not contain devel file libibus.so

* Tue May 05 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090423-2
- Fix bug 498141 - new ibus install needs gtk immodules
- Separate ibus document from ibus-devel to ibus-devel-docs

* Thu Apr 23 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090423-1
- Update to ibus-1.1.0.20090423.
- Fix bug 497265 - [mai_IN] Maithili language name is not correct.
- Fix bug 497279 - IBus does not works with evolution correctly.
- Enhance authentication both in daemon & clients

* Fri Apr 17 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090417-1
- Update to ibus-1.1.0.20090417.
- Fix bug 496199 -  cannot remove Ctrl+Space hotkey with ibus-setup

* Fri Apr 17 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090413-4
- Update ibus-HEAD.patch.
- Next Engine hotkey will do nothing if the IM is not active.

* Wed Apr 15 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090413-3
- Update ibus-HEAD.patch.
- Fix bug 495431 -  ibus Release modifier doesn't work with Alt
- Fix bug 494445 -  ibus-hangul missing Hangul Han/En mode
  (and Alt_R+release hotkey)
- Update te.po

* Tue Apr 14 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090413-2
- Update ibus-HEAD.patch.
- Change the mode of /tmp/ibus-$USER to 0700 to improve security
- Change the mode of /tmp/ibus-$USER/socket-address to 0600 to improve security
- Update as.po

* Mon Apr 13 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090413-1
- Update to ibus-1.1.0.20090413.
- Fix crash when restart the ibus-daemon
- Add some translations.

* Tue Apr 07 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090407-3
- Update the tarball.
- Fix bug 494511 - ibus-gtk makes gnome-terminal abort 
  when a key is pressed

* Tue Apr 07 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090407-2
- Update default hotkey settings.

* Tue Apr 07 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090407-1
- Update to ibus-1.1.0.20090407.
- Fix bug 491042 - ibus default trigger hotkeys
- Fix bug 492929 - ibus-hangul can cause gtk app to lockup
- Fix bug 493701 -  (ibus) imsettings disconnect/reconnect kills gtk app
- Fix bug 493687 -  ibus-hangul should default to vertical candidate selection
- Fix bug 493449 -  ibus broke Alt-F2 command auto-completion

* Tue Mar 31 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090331-1
- Update to ibus-1.1.0.20090331.
- Fix bug 492956 - screws up keyboard input in firefox
- Fix bug 490143 - ibus issue with gnome-keyring

* Sun Mar 29 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090311-3
- Recreate the ibus-HEAD.patch from upstream git source tree
- Fix bug 491999 - up/down arrow keys broken in xchat

* Sat Mar 28 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090311-2
- Recreate the ibus-HEAD.patch from upstream git source tree.
- Fix bug 490009 - Deleting Next Engine shortcuts doesn't work
- Fix bug 490381 - Change "Next/Previous engine" labels

* Wed Mar 11 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090311-1
- Update to ibus-1.1.0.20090311.
- Update setup ui follow GNOME Human Interface Guidelines 2.2 (#489497).

* Fri Mar  6 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090306-1
- Update to ibus-1.1.0.20090306.

* Tue Mar  3 2009 Jens Petersen <petersen@redhat.com>
- use post for ibus-gtk requires glib2

* Mon Mar  2 2009 Jens Petersen <petersen@redhat.com> - 1.1.0.20090225-2
- drop the superfluous ibus-0.1 engine obsoletes
- move glib2 requires to gtk package

* Tue Feb 25 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090225-1
- Update to ibus-1.1.0.20090225.
- Fix problems in %%post and %%postun scripts.
- Hide ibus & ibus preferences menu items.

* Tue Feb 17 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-10
- Recreate the ibus-HEAD.patch from upstream git source tree.
- Put 'Select an input method' in engine select combobox (#485861).

* Tue Feb 17 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-9
- Add requires im-chooser >= 1.2.5.

* Tue Feb 17 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-8
- Recreate the ibus-HEAD.patch from upstream git source tree.
- Fix ibus-hangul segfault (#485438).

* Mon Feb 16 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-6
- Recreate the ibus-HEAD.patch from upstream git source tree.
- The new patch fixes ibus-x11 segfault (#485661).

* Sun Feb 15 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-5
- Recreate the ibus-HEAD.patch from upstream git source tree.

* Sun Feb 15 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-4
- Remove gnome-python2-gconf from requires.

* Fri Feb 13 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-3
- Update ibus-HEAD.patch, to fix bug 484652.

* Fri Feb 13 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-2
- Add patch ibus-HEAD.patch, to update ibus to HEAD version.

* Wed Feb 11 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090211-1
- Add --xim argument in xinput-ibus
- Add Obsoletes:  ibus-qt <= 1.1.0
- Move libibus.so.* to ibus-libs to make ibus multilib.
- Update to 1.1.0.20090211.

* Thu Feb 05 2009 Peng Huang <shawn.p.huang@gmail.com> - 1.1.0.20090205-1
- Update to 1.1.0.20090205.

* Tue Feb 03 2009 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20090203-1
- Update to 0.1.1.20090203.

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 0.1.1.20081023-3
- Rebuild for Python 2.6

* Wed Nov 19 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20081023-2
- Move libibus-gtk.so from ibus.rpm to ibus-gtk.rpm to fix bug 472146.

* Thu Oct 23 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20081023-1
- Update to 0.1.1.20081023.

* Thu Oct 16 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20081016-1
- Update to 0.1.1.20081016.

* Tue Oct  7 2008 Jens Petersen <petersen@redhat.com> - 0.1.1.20081006-3
- remove the empty %%doc file entries

* Tue Oct  7 2008 Jens Petersen <petersen@redhat.com> - 0.1.1.20081006-2
- add xinputrc alternative when installing or uninstalling

* Mon Oct 06 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20081006-1
- Update to 0.1.1.20081006.

* Sun Oct 05 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20081005-1
- Update to 0.1.1.20081005.

* Sat Oct 04 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20081004-1
- Update to 0.1.1.20081004.

* Wed Oct 01 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20081001-1
- Update to 0.1.1.20081001.

* Tue Sep 30 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080930-1
- Update to 0.1.1.20080930.

* Tue Sep 23 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080923-1
- Update to 0.1.1.20080923.

* Wed Sep 17 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080917-1
- Update to 0.1.1.20080917.

* Tue Sep 16 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080916-1
- Update to 0.1.1.20080916.

* Mon Sep 15 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080914-1
- Update to 0.1.1.20080914.

* Mon Sep 08 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080908-1
- Update to 0.1.1.20080908.

* Mon Sep 01 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080901-1
- Update to 0.1.1.20080901.

* Sat Aug 30 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080830-1
- Update to 0.1.1.20080830.

* Mon Aug 25 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080825-1
- Update to 0.1.1.20080825.

* Sat Aug 23 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080823-1
- Update to 0.1.1.20080823.

* Fri Aug 15 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080815-1
- Update to 0.1.1.20080815.

* Thu Aug 12 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.1.20080812-1
- Update to 0.1.1.20080812.

* Mon Aug 11 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.0.20080810-2
- Add gnome-python2-gconf in Requires.

* Thu Aug 07 2008 Peng Huang <shawn.p.huang@gmail.com> - 0.1.0.20080810-1
- The first version.
