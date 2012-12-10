# Copyright (c) 2000-2007, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
%define _with_gcj_support 1
%define _without_maven 1
%define gcj_support %{?_with_gcj_support:1}%{!?_with_gcj_support:%{?_without_gcj_support:0}%{!?_without_gcj_support:%{?_gcj_support:%{_gcj_support}}%{!?_gcj_support:0}}}

# If you don't want to build with maven, and use straight ant instead,
# give rpmbuild option '--without maven'

%define with_maven %{!?_without_maven:1}%{?_without_maven:0}
%define without_maven %{?_without_maven:1}%{!?_without_maven:0}

%define section   free
%define base_name commons-compress
%define svnrev 561811

Name:           jakarta-%{base_name}
Version:        0.1
Release:        %mkrel 4.0.6
Epoch:          0
Summary:        Commons Compress
License:        Apache Software License
Url:            http://jakarta.apache.org/commons/sandbox/compress/
Group:          Development/Java
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Source0:        commons-compress-0.1-561811.tar.gz
# svn export http://svn.apache.org/repos/asf/commons/sandbox/compress/trunk commons-compress-0.1-561811

Source1:        pom-maven2jpp-depcat.xsl
Source2:        pom-maven2jpp-newdepmap.xsl
Source3:        pom-maven2jpp-mapdeps.xsl
Source4:        commons-compress-0.1-jpp-depmap.xml
Source5:        commons-sandbox-build-project.xml
Source6:        commons-compress-0.1-build.xml

Patch0:         commons-compress-0.1-project_xml.patch

BuildRequires:  java-rpmbuild
BuildRequires:  ant >= 0:1.6
BuildRequires:  junit
%if %{with_maven}
BuildRequires:  maven >= 0:1.1
BuildRequires:  saxon
BuildRequires:  saxon-scripts
%endif
%if %{gcj_support}
BuildRequires:          java-gcj-compat-devel
%endif
%if ! %{gcj_support}
BuildArch:      noarch
%endif

%description
Commons Compress is a component that contains 
Tar, Zip and BZip2 packages.

%package javadoc
Summary:        Javadoc for %{name}
Group:          Development/Java
Requires(post):   /bin/rm,/bin/ln
Requires(postun): /bin/rm

%description javadoc
%{summary}.

%prep
%setup -q -n %{base_name}-%{version}-%{svnrev}
find . -name "*.jar" -exec rm -f {} \;
cp %{SOURCE5} .
cp %{SOURCE6} build.xml

%if %{with_maven}
export DEPCAT=$(pwd)/commons-compress-0.1-depcat.new.xml
echo '<?xml version="1.0" standalone="yes"?>' > $DEPCAT
echo '<depset>' >> $DEPCAT
for p in $(find . -name project.xml); do
    pushd $(dirname $p)
    %{_bindir}/saxon project.xml %{SOURCE1} >> $DEPCAT
    popd
done
echo >> $DEPCAT
echo '</depset>' >> $DEPCAT
%{_bindir}/saxon $DEPCAT %{SOURCE2} > commons-compress-0.1-depmap.new.xml
%endif

%patch0 -b .sav

%build
%if %{with_maven}
for p in $(find . -name project.xml); do
    pushd $(dirname $p)
    cp project.xml project.xml.orig
    %{_bindir}/saxon -o project.xml project.xml.orig %{SOURCE3} map=%{SOURCE4}
    popd
done

maven -e \
        -Dmaven.repo.remote=file:/usr/share/maven/repository \
        -Dmaven.javadoc.source=1.4 \
        -Dmaven.test.failure.ignore=true \
        -Dmaven.home.local=$(pwd)/.maven \
        jar javadoc 
%else
export CLASSPATH=target/classes:target/test-classes
%{ant} \
    -Djunit.jar=file://$(build-classpath junit) \
    -Dbuild.sysclasspath=only \
    jar javadoc
%endif
%install
rm -rf $RPM_BUILD_ROOT
# jars
install -d -m 755 $RPM_BUILD_ROOT%{_javadir}
install -m 644 target/commons-compress-0.1-dev.jar \
           $RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar

(cd $RPM_BUILD_ROOT%{_javadir} && for jar in jakarta-*; do \
ln -sf ${jar} ${jar/jakarta-/}; done)
(cd $RPM_BUILD_ROOT%{_javadir} && for jar in *-%{version}*; do \
ln -sf ${jar} ${jar/-%{version}/}; done)

# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
cp -pr target/docs/apidocs/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name} # ghost symlink
rm -rf target/docs/apidocs

## manual
install -d -m 755 $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
cp -p LICENSE.txt $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}

%if %{gcj_support}
%{_bindir}/aot-compile-rpm
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%if %{gcj_support}
%post
if [ -x %{_bindir}/rebuild-gcj-db ]
then
  %{_bindir}/rebuild-gcj-db
fi
%endif

%if %{gcj_support}
%postun
if [ -x %{_bindir}/rebuild-gcj-db ]
then
  %{_bindir}/rebuild-gcj-db
fi
%endif

%files
%defattr(0644,root,root,0755)
%{_docdir}/%{name}-%{version}/LICENSE.txt
%{_javadir}/*
%if %{gcj_support}
%attr(-,root,root) %dir %{_libdir}/gcj/%{name}
%attr(-,root,root) %{_libdir}/gcj/%{name}/%{name}-%{version}.jar.*
%endif


%files javadoc
%defattr(0644,root,root,0755)
%{_javadocdir}/%{name}-%{version}
%{_javadocdir}/%{name}


%changelog
* Fri Dec 10 2010 Oden Eriksson <oeriksson@mandriva.com> 0:0.1-4.0.6mdv2011.0
+ Revision: 619741
- the mass rebuild of 2010.0 packages

* Wed Sep 09 2009 Thierry Vignaud <tv@mandriva.org> 0:0.1-4.0.5mdv2010.0
+ Revision: 436044
- rebuild
- fix no-buildroot-tag
- kill re-definition of %%buildroot on Pixel's request

* Sun Dec 16 2007 Anssi Hannula <anssi@mandriva.org> 0:0.1-4.0.4mdv2008.1
+ Revision: 120810
- buildrequires java-rpmbuild

* Sat Sep 15 2007 Anssi Hannula <anssi@mandriva.org> 0:0.1-4.0.3mdv2008.0
+ Revision: 87402
- rebuild to filter out autorequires of GCJ AOT objects
- remove unnecessary Requires(post) on java-gcj-compat

* Sat Aug 18 2007 David Walluck <walluck@mandriva.org> 0:0.1-4.0.2mdv2008.0
+ Revision: 65410
- fix build without maven calling saxon
- add macros for /usr/bin
- actually remove jars before building
- Import jakarta-commons-compress



* Thu Aug 02 2007 Alexander Kurtakov <akurtakov@active-lynx.com> - 0:0.1-4.0.1mdv2008.0
- Use mdv macros

* Wed Aug 01 2007 Ralph Apel <r.apel@r-apel.de> 0:0.1-4jpp
- Switch to Revision 561811
- Optionally build without maven
- Wait for TLP 1.0 for further changes

* Tue May 15 2007 Ralph Apel <r.apel@r-apel.de> 0:0.1-3jpp
- Make Vendor, Distribution based on macro
- Fix aot build

* Wed Sep 27 2006 Ralph Apel <r.apel@r-apel.de> 0:0.1-2jpp
- Upgrade to r450385 as of 2006-09-27
- Adapt to maven-1.1
- Add post/postun Requires for javadoc
- Add gcj_support option

* Mon Sep 05 2005 Ralph Apel <r.apel@r-apel.de> 0:0.1-1jpp
- First release
