from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.scm import Version
from conans import tools
from conans.model import Generator
import configparser
import itertools
import os

required_conan_version = ">=1.52.0"


class qt(Generator):
    @property
    def filename(self):
        return "qt.conf"

    @property
    def content(self):
        return """[Paths]
Prefix = %s
ArchData = bin/archdatadir
HostData = bin/archdatadir
Data = bin/datadir
Sysconf = bin/sysconfdir
LibraryExecutables = bin/archdatadir/bin
Plugins = bin/archdatadir/plugins
Imports = bin/archdatadir/imports
Qml2Imports = bin/archdatadir/qml
Translations = bin/datadir/translations
Documentation = bin/datadir/doc
Examples = bin/datadir/examples""" % self.conanfile.deps_cpp_info["qt"].rootpath.replace("\\", "/")


class QtConan(ConanFile):
    _submodules = ["qtsvg", "qtdeclarative", "qtactiveqt", "qtscript", "qtmultimedia", "qttools", "qtxmlpatterns",
    "qttranslations", "qtdoc", "qtlocation", "qtsensors", "qtconnectivity", "qtwayland",
    "qt3d", "qtimageformats", "qtgraphicaleffects", "qtquickcontrols", "qtserialbus", "qtserialport", "qtx11extras",
    "qtmacextras", "qtwinextras", "qtandroidextras", "qtwebsockets", "qtwebchannel", "qtwebengine", "qtwebview",
    "qtquickcontrols2", "qtpurchasing", "qtcharts", "qtdatavis3d", "qtvirtualkeyboard", "qtgamepad", "qtscxml",
    "qtspeech", "qtnetworkauth", "qtremoteobjects", "qtwebglplugin", "qtlottie", "qtquicktimeline", "qtquick3d",
    "qtknx", "qtmqtt", "qtcoap", "qtopcua"]

    name = "qt"
    description = "Qt is a cross-platform framework for graphical user interfaces."
    topics = ("qt", "ui")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.qt.io"
    license = "LGPL-3.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "commercial": [True, False],

        "opengl": ["no", "es2", "desktop", "dynamic"],
        "with_vulkan": [True, False],
        "openssl": [True, False],
        "with_pcre2": [True, False],
        "with_glib": [True, False],
        # "with_libiconv": [True, False],  # QTBUG-84708 Qt tests failure "invalid conversion from const char** to char**"
        "with_doubleconversion": [True, False],
        "with_freetype": [True, False],
        "with_fontconfig": [True, False],
        "with_icu": [True, False],
        "with_harfbuzz": [True, False],
        "with_libjpeg": ["libjpeg", "libjpeg-turbo", False],
        "with_libpng": [True, False],
        "with_sqlite3": [True, False],
        "with_mysql": [True, False],
        "with_pq": [True, False],
        "with_odbc": [True, False],
        "with_libalsa": [True, False],
        "with_openal": [True, False],
        "with_zstd": [True, False],
        "with_gstreamer": [True, False],
        "with_pulseaudio": [True, False],
        "with_dbus": [True, False],
        "with_gssapi": [True, False],
        "with_atspi": [True, False],
        "with_md4c": [True, False],

        "gui": [True, False],
        "widgets": [True, False],

        "device": "ANY",
        "cross_compile": "ANY",
        "sysroot": "ANY",
        "config": "ANY",
        "multiconfiguration": [True, False]
    }
    options.update({module: [True, False] for module in _submodules})

    default_options = {
        "shared": False,
        "commercial": False,
        "opengl": "desktop",
        "with_vulkan": False,
        "openssl": True,
        "with_pcre2": True,
        "with_glib": False,
        # "with_libiconv": True, # QTBUG-84708
        "with_doubleconversion": True,
        "with_freetype": True,
        "with_fontconfig": True,
        "with_icu": True,
        "with_harfbuzz": False,
        "with_libjpeg": "libjpeg",
        "with_libpng": True,
        "with_sqlite3": True,
        "with_mysql": True,
        "with_pq": True,
        "with_odbc": True,
        "with_libalsa": False,
        "with_openal": True,
        "with_zstd": True,
        "with_gstreamer": False,
        "with_pulseaudio": False,
        "with_dbus": False,
        "with_gssapi": False,
        "with_atspi": False,
        "with_md4c": True,

        "gui": True,
        "widgets": True,

        "device": None,
        "cross_compile": None,
        "sysroot": None,
        "config": None,
        "multiconfiguration": False
    }
    default_options.update({module: (module in ["qttools", "qttranslations"]) for module in _submodules})

    no_copy_source = True
    short_paths = True
    generators = "pkg_config"

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export(self):
        self.copy("qtmodules%s.conf" % self.version)

    def build_requirements(self):
        if self._settings_build.os == "Windows" and self._is_msvc:
            self.build_requires("jom/1.1.3")

    def config_options(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_icu
            del self.options.with_fontconfig
            del self.options.with_libalsa
            del self.options.qtx11extras
        if self.settings.compiler == "apple-clang":
            if Version(self.settings.compiler.version) < "10.0":
                raise ConanInvalidConfiguration("Old versions of apple sdk are not supported by Qt (QTBUG-76777)")
        if self.settings.compiler in ["gcc", "clang"]:
            if Version(self.settings.compiler.version) < "5.0":
                raise ConanInvalidConfiguration("qt 5.15.X does not support GCC or clang before 5.0")
        if self.settings.compiler in ["gcc", "clang"] and Version(self.settings.compiler.version) < "5.3":
            del self.options.with_mysql
        if self.settings.os == "Windows":
            self.options.with_mysql = False
            self.options.opengl = "dynamic"
            del self.options.with_gssapi
        self.options.qtwayland = False
        self.options.with_atspi = False

        if self.settings.os != "Windows":
            del self.options.qtwinextras
            del self.options.qtactiveqt

        if self.settings.os != "Macos":
            del self.options.qtmacextras

    def configure(self):
        # if self.settings.os != "Linux":
        #         self.options.with_libiconv = False # QTBUG-84708

        if not self.options.gui:
            del self.options.opengl
            del self.options.with_vulkan
            del self.options.with_freetype
            del self.options.with_fontconfig
            del self.options.with_harfbuzz
            del self.options.with_libjpeg
            del self.options.with_libpng
            del self.options.with_md4c

        if not self.options.with_dbus:
            del self.options.with_atspi


        if self.options.multiconfiguration:
            del self.settings.build_type

        config = configparser.ConfigParser()
        config.read(os.path.join(self.recipe_folder, "qtmodules%s.conf" % self.version))
        submodules_tree = {}
        for s in config.sections():
            section = str(s)
            assert section.startswith("submodule ")
            assert section.count('"') == 2
            modulename = section[section.find('"') + 1: section.rfind('"')]
            status = str(config.get(section, "status"))
            if status != "obsolete" and status != "ignore":
                submodules_tree[modulename] = {"status": status,
                                "path": str(config.get(section, "path")), "depends": []}
                if config.has_option(section, "depends"):
                    submodules_tree[modulename]["depends"] = [str(i) for i in config.get(section, "depends").split()]

        for m in submodules_tree:
            assert m in ["qtbase", "qtqa", "qtrepotools"] or m in self._submodules, "module %s is not present in recipe options : (%s)" % (m, ",".join(self._submodules))

        for m in self._submodules:
            if m not in submodules_tree:
                delattr(self.options, m)

        def _enablemodule(mod):
            if mod != "qtbase":
                setattr(self.options, mod, True)
            for req in submodules_tree[mod]["depends"]:
                _enablemodule(req)

        for module in self._submodules:
            if self.options.get_safe(module):
                _enablemodule(module)

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "11")
        if self.options.widgets and not self.options.gui:
            raise ConanInvalidConfiguration("using option qt:widgets without option qt:gui is not possible. "
                                            "You can either disable qt:widgets or enable qt:gui")

        if self.settings.os == "Android" and self.options.get_safe("opengl", "no") == "desktop":
            raise ConanInvalidConfiguration("OpenGL desktop is not supported on Android. Consider using OpenGL es2")

        if self.settings.os != "Windows" and self.options.get_safe("opengl", "no") == "dynamic":
            raise ConanInvalidConfiguration("Dynamic OpenGL is supported only on Windows.")

        if self.options.get_safe("with_fontconfig", False) and not self.options.get_safe("with_freetype", False):
            raise ConanInvalidConfiguration("with_fontconfig cannot be enabled if with_freetype is disabled.")

        if not self.options.with_doubleconversion and str(self.settings.compiler.libcxx) != "libc++":
            raise ConanInvalidConfiguration("Qt without libc++ needs qt:with_doubleconversion. "
                                            "Either enable qt:with_doubleconversion or switch to libc++")

        if "MT" in self.settings.get_safe("compiler.runtime", default="") and self.options.shared:
            raise ConanInvalidConfiguration("Qt cannot be built as shared library with static runtime")

        if self.settings.compiler == "apple-clang":
            if Version(self.settings.compiler.version) < "10.0":
                raise ConanInvalidConfiguration("Old versions of apple sdk are not supported by Qt (QTBUG-76777)")
        if self.settings.compiler in ["gcc", "clang"]:
            if Version(self.settings.compiler.version) < "5.0":
                raise ConanInvalidConfiguration("qt 5.15.X does not support GCC or clang before 5.0")

        if self.options.get_safe("with_pulseaudio", default=False) and not self.options["pulseaudio"].with_glib:
            # https://bugreports.qt.io/browse/QTBUG-95952
            raise ConanInvalidConfiguration("Pulseaudio needs to be built with glib option or qt's configure script won't detect it")

        if self.settings.os in ['Linux', 'FreeBSD'] and self.options.with_gssapi:
            raise ConanInvalidConfiguration("gssapi cannot be enabled until conan-io/conan-center-index#4102 is closed")

    def requirements(self):
        self.requires("zlib/1.2.13")
        if self.options.openssl:
            self.requires("openssl/1.1.1q")
        if self.options.with_pcre2:
            self.requires("pcre2/10.40")
        if self.options.get_safe("with_vulkan"):
            self.requires("vulkan-loader/1.3.224.0")
            if is_apple_os(self):
                self.requires("moltenvk/1.1.10")
        if self.options.with_glib:
            self.requires("glib/2.74.0")
        # if self.options.with_libiconv: # QTBUG-84708
        #     self.requires("libiconv/1.16")# QTBUG-84708
        if self.options.with_doubleconversion and not self.options.multiconfiguration:
            self.requires("double-conversion/3.2.1")
        if self.options.get_safe("with_freetype", False) and not self.options.multiconfiguration:
            self.requires("freetype/2.12.1")
        if self.options.get_safe("with_fontconfig", False):
            self.requires("fontconfig/2.13.93")
        if self.options.get_safe("with_icu", False):
            self.requires("icu/71.1")
        if self.options.get_safe("with_harfbuzz", False) and not self.options.multiconfiguration:
            self.requires("harfbuzz/5.3.1")
        if self.options.get_safe("with_libjpeg", False) and not self.options.multiconfiguration:
            if self.options.with_libjpeg == "libjpeg-turbo":
                self.requires("libjpeg-turbo/2.1.4")
            else:
                self.requires("libjpeg/9e")
        if self.options.get_safe("with_libpng", False) and not self.options.multiconfiguration:
            self.requires("libpng/1.6.38")
        if self.options.with_sqlite3 and not self.options.multiconfiguration:
            self.requires("sqlite3/3.39.4")
            self.options["sqlite3"].enable_column_metadata = True
        if self.options.get_safe("with_mysql", False):
            self.requires("libmysqlclient/8.0.30")
        if self.options.with_pq:
            self.requires("libpq/14.5")
        if self.options.with_odbc:
            if self.settings.os != "Windows":
                self.requires("odbc/2.3.11")
        if self.options.get_safe("with_libalsa", False):
            self.requires("libalsa/1.2.7.2")
        if self.options.gui and self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("xorg/system")
            self.requires("xkbcommon/1.4.1")
        if self.options.get_safe("opengl", "no") != "no":
            self.requires("opengl/system")
        if self.options.with_zstd:
            self.requires("zstd/1.5.2")
        if self.options.get_safe("with_gstreamer", False):
            self.requires("gst-plugins-base/1.19.2")
        if self.options.get_safe("with_pulseaudio", False):
            self.requires("pulseaudio/14.2")
        if self.options.with_dbus:
            self.requires("dbus/1.15.2")
        if self.settings.os in ['Linux', 'FreeBSD'] and self.options.with_gssapi:
            self.requires("krb5/1.18.3") # conan-io/conan-center-index#4102
        if self.options.get_safe("with_atspi"):
            self.requires("at-spi2-core/2.46.0")
        if self.options.get_safe("with_md4c", False):
            self.requires("md4c/0.4.8")

    def _make_program(self):
        if self._is_msvc:
            return "jom"
        elif tools.os_info.is_windows:
            return "mingw32-make"
        else:
            return "make"

    def _xplatform(self):
        if self.settings.os == "Linux":
            if self.settings.compiler == "gcc":
                return {"x86": "linux-g++-32",
                        "armv6": "linux-arm-gnueabi-g++",
                        "armv7": "linux-arm-gnueabi-g++",
                        "armv7hf": "linux-arm-gnueabi-g++",
                        "armv8": "linux-aarch64-gnu-g++"}.get(str(self.settings.arch), "linux-g++")
            elif self.settings.compiler == "clang":
                if self.settings.arch == "x86":
                    return "linux-clang-libc++-32" if self.settings.compiler.libcxx == "libc++" else "linux-clang-32"
                elif self.settings.arch == "x86_64":
                    return "linux-clang-libc++" if self.settings.compiler.libcxx == "libc++" else "linux-clang"

        elif self.settings.os == "Macos":
            return {"clang": "macx-clang",
                    "apple-clang": "macx-clang",
                    "gcc": "macx-g++"}.get(str(self.settings.compiler))

        elif self.settings.os == "iOS":
            if self.settings.compiler == "apple-clang":
                return "macx-ios-clang"

        elif self.settings.os == "watchOS":
            if self.settings.compiler == "apple-clang":
                return "macx-watchos-clang"

        elif self.settings.os == "tvOS":
            if self.settings.compiler == "apple-clang":
                return "macx-tvos-clang"

        elif self.settings.os == "Android":
            if self.settings.compiler == "clang":
                return "android-clang"

        elif self.settings.os == "Windows":
            return {
                "Visual Studio": "win32-msvc",
                "msvc": "win32-msvc",
                "gcc": "win32-g++",
                "clang": "win32-clang-g++",
            }.get(str(self.settings.compiler))

        elif self.settings.os == "WindowsStore":
            if self._is_msvc:
                if self.settings.compiler == "Visual Studio":
                    msvc_version = str(self.settings.compiler.version)
                else:
                    msvc_version = {
                        "190": "14",
                        "191": "15",
                        "192": "16",
                    }.get(str(self.settings.compiler.version))
                return {
                    "14": {
                        "armv7": "winrt-arm-msvc2015",
                        "x86": "winrt-x86-msvc2015",
                        "x86_64": "winrt-x64-msvc2015",
                    },
                    "15": {
                        "armv7": "winrt-arm-msvc2017",
                        "x86": "winrt-x86-msvc2017",
                        "x86_64": "winrt-x64-msvc2017",
                    },
                    "16": {
                        "armv7": "winrt-arm-msvc2019",
                        "x86": "winrt-x86-msvc2019",
                        "x86_64": "winrt-x64-msvc2019",
                    }
                }.get(msvc_version).get(str(self.settings.arch))

        elif self.settings.os == "FreeBSD":
            return {"clang": "freebsd-clang",
                    "gcc": "freebsd-g++"}.get(str(self.settings.compiler))

        elif self.settings.os == "SunOS":
            if self.settings.compiler == "sun-cc":
                if self.settings.arch == "sparc":
                    return "solaris-cc-stlport" if self.settings.compiler.libcxx == "libstlport" else "solaris-cc"
                elif self.settings.arch == "sparcv9":
                    return "solaris-cc64-stlport" if self.settings.compiler.libcxx == "libstlport" else "solaris-cc64"
            elif self.settings.compiler == "gcc":
                return {"sparc": "solaris-g++",
                        "sparcv9": "solaris-g++-64"}.get(str(self.settings.arch))
        elif self.settings.os == "Neutrino" and self.settings.compiler == "qcc":
            return {"armv8": "qnx-aarch64le-qcc",
                    "armv8.3": "qnx-aarch64le-qcc",
                    "armv7": "qnx-armle-v7-qcc",
                    "armv7hf": "qnx-armle-v7-qcc",
                    "armv7s": "qnx-armle-v7-qcc",
                    "armv7k": "qnx-armle-v7-qcc",
                    "x86": "qnx-x86-qcc",
                    "x86_64": "qnx-x86-64-qcc"}.get(str(self.settings.arch))
        elif self.settings.os == "Emscripten" and self.settings.arch == "wasm":
            return "wasm-emscripten"

        return None


    def package_id(self):
        del self.info.options.cross_compile
        del self.info.options.sysroot
        if self.options.multiconfiguration and self._is_msvc:
            if self.settings.compiler == "Visual Studio":
                if "MD" in self.settings.compiler.runtime:
                    self.info.settings.compiler.runtime = "MD/MDd"
                else:
                    self.info.settings.compiler.runtime = "MT/MTd"
            else:
                self.info.settings.compiler.runtime_type = "Release/Debug"

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Qt5")

        self.cpp_info.names["cmake_find_package"] = "Qt5"
        self.cpp_info.names["cmake_find_package_multi"] = "Qt5"

        build_modules = {}
        def _add_build_module(component, module):
            if component not in build_modules:
                build_modules[component] = []
            build_modules[component].append(module)
            self.cpp_info.components[component].build_modules["cmake_find_package"].append(module)
            self.cpp_info.components[component].build_modules["cmake_find_package_multi"].append(module)

        libsuffix = ""
        if not self.options.multiconfiguration:
            if self.settings.build_type == "Debug":
                if self.settings.os == "Windows" and self._is_msvc:
                    libsuffix = "d"
                elif is_apple_os(self):
                    libsuffix = "_debug"

        def _get_corrected_reqs(requires):
            reqs = []
            for r in requires:
                reqs.append(r if "::" in r else "qt%s" % r)
            return reqs

        def _create_module(module, requires=[], has_include_dir=True):
            componentname = "qt%s" % module
            assert componentname not in self.cpp_info.components, "Module %s already present in self.cpp_info.components" % module
            self.cpp_info.components[componentname].set_property("cmake_target_name", "Qt5::{}".format(module))
            self.cpp_info.components[componentname].names["cmake_find_package"] = module
            self.cpp_info.components[componentname].names["cmake_find_package_multi"] = module
            if module.endswith("Private"):
                libname = module[:-7]
            else:
                libname = module
            self.cpp_info.components[componentname].libs = ["Qt5%s%s" % (libname, libsuffix)]
            if has_include_dir:
                self.cpp_info.components[componentname].includedirs = ["include", os.path.join("include", "Qt%s" % module)]
            self.cpp_info.components[componentname].defines = ["QT_%s_LIB" % module.upper()]
            if module != "Core" and "Core" not in requires:
                requires.append("Core")
            self.cpp_info.components[componentname].requires = _get_corrected_reqs(requires)

        def _create_plugin(pluginname, libname, plugintype, requires):
            componentname = "qt%s" % pluginname
            assert componentname not in self.cpp_info.components, "Plugin %s already present in self.cpp_info.components" % pluginname
            self.cpp_info.components[componentname].set_property("cmake_target_name", "Qt5::{}".format(pluginname))
            self.cpp_info.components[componentname].names["cmake_find_package"] = pluginname
            self.cpp_info.components[componentname].names["cmake_find_package_multi"] = pluginname
            if not self.options.shared:
                self.cpp_info.components[componentname].libs = [libname + libsuffix]
            self.cpp_info.components[componentname].libdirs = [os.path.join("bin", "archdatadir", "plugins", plugintype)]
            self.cpp_info.components[componentname].includedirs = []
            if "Core" not in requires:
                requires.append("Core")
            self.cpp_info.components[componentname].requires = _get_corrected_reqs(requires)

        core_reqs = ["zlib::zlib"]
        if self.options.with_pcre2:
            core_reqs.append("pcre2::pcre2")
        if self.options.with_doubleconversion:
            core_reqs.append("double-conversion::double-conversion")
        if self.options.get_safe("with_icu", False):
            core_reqs.append("icu::icu")
        if self.options.with_zstd:
            core_reqs.append("zstd::zstd")
        if self.options.with_glib:
            core_reqs.append("glib::glib-2.0")

        _create_module("Core", core_reqs)
        if self.settings.os == "Windows":
            module = "WinMain"
            componentname = "qt%s" % module
            self.cpp_info.components[componentname].set_property("cmake_target_name", "Qt5::{}".format(module))
            self.cpp_info.components[componentname].names["cmake_find_package"] = module
            self.cpp_info.components[componentname].names["cmake_find_package_multi"] = module
            self.cpp_info.components[componentname].libs = ["qtmain%s" % libsuffix]
            self.cpp_info.components[componentname].includedirs = []
            self.cpp_info.components[componentname].defines = []

        if self.options.gui:
            gui_reqs = []
            if self.options.with_dbus:
                gui_reqs.append("DBus")
            if self.options.with_freetype:
                gui_reqs.append("freetype::freetype")
            if self.options.with_libpng:
                gui_reqs.append("libpng::libpng")
            if self.options.get_safe("with_fontconfig", False):
                gui_reqs.append("fontconfig::fontconfig")
            if self.settings.os in ["Linux", "FreeBSD"]:
                gui_reqs.extend(["xorg::xorg", "xkbcommon::xkbcommon"])
            if self.options.get_safe("opengl", "no") != "no":
                gui_reqs.append("opengl::opengl")
            if self.options.get_safe("with_vulkan", False):
                gui_reqs.append("vulkan-loader::vulkan-loader")
                if is_apple_os(self):
                    gui_reqs.append("moltenvk::moltenvk")
            if self.options.with_harfbuzz:
                gui_reqs.append("harfbuzz::harfbuzz")
            if self.options.with_libjpeg == "libjpeg-turbo":
                gui_reqs.append("libjpeg-turbo::libjpeg-turbo")
            if self.options.with_libjpeg == "libjpeg":
                gui_reqs.append("libjpeg::libjpeg")
            if self.options.with_md4c:
                gui_reqs.append("md4c::md4c")
            _create_module("Gui", gui_reqs)

            event_dispatcher_reqs = ["Core", "Gui"]
            if self.options.with_glib:
                event_dispatcher_reqs.append("glib::glib")
            _create_module("EventDispatcherSupport", event_dispatcher_reqs)
            _create_module("FontDatabaseSupport", ["Core", "Gui"])
            if self.settings.os == "Windows":
                self.cpp_info.components["qtFontDatabaseSupport"].system_libs.extend(["advapi32", "ole32", "user32", "gdi32"])
            elif is_apple_os(self):
                self.cpp_info.components["qtFontDatabaseSupport"].frameworks.extend(["CoreFoundation", "CoreGraphics", "CoreText","Foundation"])
                self.cpp_info.components["qtFontDatabaseSupport"].frameworks.append("AppKit" if self.settings.os == "Macos" else "UIKit")
            if self.options.get_safe("with_fontconfig"):
                self.cpp_info.components["qtFontDatabaseSupport"].requires.append("fontconfig::fontconfig")
            if self.options.get_safe("with_freetype"):
                self.cpp_info.components["qtFontDatabaseSupport"].requires.append("freetype::freetype")


            _create_module("ThemeSupport", ["Core", "Gui"])
            _create_module("AccessibilitySupport", ["Core", "Gui"])
            if self.options.get_safe("with_vulkan"):
                _create_module("VulkanSupport", ["Core", "Gui"])

            if is_apple_os(self):
                _create_module("ClipboardSupport", ["Core", "Gui"])
                self.cpp_info.components["qtClipboardSupport"].frameworks = ["ImageIO"]
                if self.settings.os == "Macos":
                    self.cpp_info.components["qtClipboardSupport"].frameworks.append("AppKit")
                _create_module("GraphicsSupport", ["Core", "Gui"])

            if self.settings.os in ["Android", "Emscripten"]:
                _create_module("EglSupport", ["Core", "Gui"])

            if self.settings.os == "Windows":
                windows_reqs = ["Core", "Gui"]
                windows_reqs.extend(["EventDispatcherSupport", "FontDatabaseSupport", "ThemeSupport", "AccessibilitySupport"])
                _create_module("WindowsUIAutomationSupport", ["Core", "Gui"])
                windows_reqs.append("WindowsUIAutomationSupport")
                if self.options.get_safe("with_vulkan"):
                    windows_reqs.append("VulkanSupport")
                _create_plugin("QWindowsIntegrationPlugin", "qwindows", "platforms", windows_reqs)
                _create_plugin("QWindowsVistaStylePlugin", "qwindowsvistastyle", "styles", windows_reqs)
                self.cpp_info.components["qtQWindowsIntegrationPlugin"].system_libs = ["advapi32", "dwmapi", "gdi32", "imm32",
                    "ole32", "oleaut32", "shell32", "shlwapi", "user32", "winmm", "winspool", "wtsapi32"]
            elif self.settings.os == "Android":
                android_reqs = ["Core", "Gui", "EventDispatcherSupport", "AccessibilitySupport", "FontDatabaseSupport", "EglSupport"]
                if self.options.get_safe("with_vulkan"):
                    android_reqs.append("VulkanSupport")
                _create_plugin("QAndroidIntegrationPlugin", "qtforandroid", "platforms", android_reqs)
                self.cpp_info.components["qtQAndroidIntegrationPlugin"].system_libs = ["android", "jnigraphics"]
            elif self.settings.os == "Macos":
                cocoa_reqs = ["Core", "Gui", "ClipboardSupport", "ThemeSupport", "FontDatabaseSupport", "GraphicsSupport", "AccessibilitySupport"]
                if self.options.get_safe("with_vulkan"):
                    cocoa_reqs.append("VulkanSupport")
                if self.options.widgets:
                    cocoa_reqs.append("PrintSupport")
                _create_plugin("QCocoaIntegrationPlugin", "qcocoa", "platforms", cocoa_reqs)
                _create_plugin("QMacStylePlugin", "qmacstyle", "styles", cocoa_reqs)
                self.cpp_info.components["QCocoaIntegrationPlugin"].frameworks = ["AppKit", "Carbon", "CoreServices", "CoreVideo",
                    "IOKit", "IOSurface", "Metal", "QuartzCore"]
            elif self.settings.os in ["iOS", "tvOS"]:
                _create_plugin("QIOSIntegrationPlugin", "qios", "platforms", ["ClipboardSupport", "FontDatabaseSupport", "GraphicsSupport"])
                self.cpp_info.components["QIOSIntegrationPlugin"].frameworks = ["AudioToolbox", "Foundation", "Metal",
                    "MobileCoreServices", "OpenGLES", "QuartzCore", "UIKit"]
            elif self.settings.os == "watchOS":
                _create_plugin("QMinimalIntegrationPlugin", "qminimal", "platforms", ["EventDispatcherSupport", "FontDatabaseSupport"])
            elif self.settings.os == "Emscripten":
                _create_plugin("QWasmIntegrationPlugin", "qwasm", "platforms", ["Core", "Gui", "EventDispatcherSupport", "FontDatabaseSupport", "EglSupport"])
            elif self.settings.os in ["Linux", "FreeBSD"]:
                service_support_reqs = ["Core", "Gui"]
                if self.options.with_dbus:
                    service_support_reqs.append("DBus")
                _create_module("ServiceSupport", service_support_reqs)
                _create_module("EdidSupport")
                _create_module("XkbCommonSupport", ["Core", "Gui", "xkbcommon::libxkbcommon-x11"])
                xcb_qpa_reqs = ["Core", "Gui", "ServiceSupport", "ThemeSupport", "FontDatabaseSupport", "EdidSupport", "XkbCommonSupport", "xorg::xorg"]
                if self.options.with_dbus and self.options.with_atspi:
                    _create_module("LinuxAccessibilitySupport", ["Core", "DBus", "Gui", "AccessibilitySupport", "at-spi2-core::at-spi2-core"])
                    xcb_qpa_reqs.append("LinuxAccessibilitySupport")
                if self.options.get_safe("with_vulkan"):
                    xcb_qpa_reqs.append("VulkanSupport")
                _create_module("XcbQpa", xcb_qpa_reqs, has_include_dir=False)
                _create_plugin("QXcbIntegrationPlugin", "qxcb", "platforms", ["Core", "Gui", "XcbQpa"])

        if self.options.with_sqlite3:
            _create_plugin("QSQLiteDriverPlugin", "qsqlite", "sqldrivers", ["sqlite3::sqlite3"])
        if self.options.with_pq:
            _create_plugin("QPSQLDriverPlugin", "qsqlpsql", "sqldrivers", ["libpq::libpq"])
        if self.options.get_safe("with_mysql", False):
            _create_plugin("QMySQLDriverPlugin", "qsqlmysql", "sqldrivers", ["libmysqlclient::libmysqlclient"])
        if self.options.with_odbc:
            if self.settings.os != "Windows":
                _create_plugin("QODBCDriverPlugin", "qsqlodbc", "sqldrivers", ["odbc::odbc"])
        networkReqs = []
        if self.options.openssl:
            networkReqs.append("openssl::openssl")
        if self.settings.os in ['Linux', 'FreeBSD'] and self.options.with_gssapi:
            networkReqs.append("krb5::krb5-gssapi")
        _create_module("Network", networkReqs)
        _create_module("Sql")
        _create_module("Test")
        if self.options.widgets:
            _create_module("Widgets", ["Gui"])
        if self.options.gui and self.options.widgets and not self.settings.os in ["iOS", "watchOS", "tvOS"]:
            _create_module("PrintSupport", ["Gui", "Widgets"])
            if self.settings.os == "Macos" and not self.options.shared:
                self.cpp_info.components["PrintSupport"].system_libs.append("cups")
        if self.options.get_safe("opengl", "no") != "no" and self.options.gui:
            _create_module("OpenGL", ["Gui"])
        if self.options.widgets and self.options.get_safe("opengl", "no") != "no":
            _create_module("OpenGLExtensions", ["Gui"])
        if self.options.with_dbus:
            _create_module("DBus", ["dbus::dbus"])
        _create_module("Concurrent")
        _create_module("Xml")

        if self.settings.os != "Windows":
            self.cpp_info.components["qtCore"].cxxflags.append("-fPIC")

        if self.options.get_safe("qtx11extras"):
            _create_module("X11Extras")

        if self.options.get_safe("qtwinextras"):
            _create_module("WinExtras")

        if self.options.get_safe("qtmacextras"):
            _create_module("MacExtras")


        if self.options.get_safe("qtactiveqt"):
            _create_module("AxBase", ["Gui", "Widgets"])
            self.cpp_info.components["qtAxBase"].includedirs = ["include", os.path.join("include", "ActiveQt")]
            self.cpp_info.components["qtAxBase"].system_libs.extend(["ole32", "oleaut32", "user32", "gdi32", "advapi32"])
            if self.settings.compiler == "gcc":
                self.cpp_info.components["qtAxBase"].system_libs.append("uuid")
            _create_module("AxContainer", ["Core", "Gui", "Widgets", "AxBase"])
            self.cpp_info.components["qtAxContainer"].includedirs = [os.path.join("include", "ActiveQt")]
            _create_module("AxServer", ["Core", "Gui", "Widgets", "AxBase"])
            self.cpp_info.components["qtAxServer"].includedirs = [os.path.join("include", "ActiveQt")]
            self.cpp_info.components["qtAxServer"].system_libs.append("shell32")


        if not self.options.shared:
            if self.settings.os == "Windows":
                self.cpp_info.components["qtCore"].system_libs.append("version")  # qtcore requires "GetFileVersionInfoW" and "VerQueryValueW" which are in "Version.lib" library
                self.cpp_info.components["qtCore"].system_libs.append("winmm")    # qtcore requires "__imp_timeSetEvent" which is in "Winmm.lib" library
                self.cpp_info.components["qtCore"].system_libs.append("netapi32") # qtcore requires "NetApiBufferFree" which is in "Netapi32.lib" library
                self.cpp_info.components["qtCore"].system_libs.append("userenv")  # qtcore requires "__imp_GetUserProfileDirectoryW " which is in "UserEnv.Lib" library
                self.cpp_info.components["qtCore"].system_libs.append("ws2_32")  # qtcore requires "WSAStartup " which is in "Ws2_32.Lib" library
                self.cpp_info.components["qtNetwork"].system_libs.append("dnsapi")  # qtnetwork from qtbase requires "DnsFree" which is in "Dnsapi.lib" library
                self.cpp_info.components["qtNetwork"].system_libs.append("iphlpapi")
                if self.options.widgets:
                    self.cpp_info.components["qtWidgets"].system_libs.append("UxTheme")
                    self.cpp_info.components["qtWidgets"].system_libs.append("dwmapi")
                if self.options.get_safe("qtwinextras"):
                    self.cpp_info.components["qtWinExtras"].system_libs.append("dwmapi")  # qtwinextras requires "DwmGetColorizationColor" which is in "dwmapi.lib" library

            if is_apple_os(self):
                self.cpp_info.components["qtCore"].frameworks.append("CoreServices" if self.settings.os == "Macos" else "MobileCoreServices")
                self.cpp_info.components["qtNetwork"].frameworks.append("SystemConfiguration")
                if self.options.with_gssapi:
                    self.cpp_info.components["qtNetwork"].frameworks.append("GSS")
                if not self.options.openssl: # with SecureTransport
                    self.cpp_info.components["qtNetwork"].frameworks.append("Security")
            if self.settings.os == "Macos":
                self.cpp_info.components["qtCore"].frameworks.append("IOKit")     # qtcore requires "_IORegistryEntryCreateCFProperty", "_IOServiceGetMatchingService" and much more which are in "IOKit" framework
                self.cpp_info.components["qtCore"].frameworks.append("Cocoa")     # qtcore requires "_OBJC_CLASS_$_NSApplication" and more, which are in "Cocoa" framework
                self.cpp_info.components["qtCore"].frameworks.append("Security")  # qtcore requires "_SecRequirementCreateWithString" and more, which are in "Security" framework

        self.cpp_info.components["qtCore"].builddirs.append(os.path.join("bin","archdatadir","bin"))



        build_modules_list = []

        def _add_build_modules_for_component(component):
            for req in self.cpp_info.components[component].requires:
                if "::" in req: # not a qt component                   
                    continue
                _add_build_modules_for_component(req)
            build_modules_list.extend(build_modules.pop(component, []))

        for c in self.cpp_info.components:
            _add_build_modules_for_component(c)

        self.cpp_info.set_property("cmake_build_modules", build_modules_list)

    @staticmethod
    def _remove_duplicate(l):
        seen = set()
        seen_add = seen.add
        for element in itertools.filterfalse(seen.__contains__, l):
            seen_add(element)
            yield element

    def _gather_libs(self, p):
        if not p in self.deps_cpp_info.deps:
            return []
        libs = ["-l" + i for i in self.deps_cpp_info[p].libs + self.deps_cpp_info[p].system_libs]
        if is_apple_os(self):
            libs += ["-framework " + i for i in self.deps_cpp_info[p].frameworks]
        libs += self.deps_cpp_info[p].sharedlinkflags
        for dep in self.deps_cpp_info[p].public_deps:
            libs += self._gather_libs(dep)
        return self._remove_duplicate(libs)