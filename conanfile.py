import os
from os.path import join
from pathlib import Path
from conan import ConanFile
from conan.tools.files import get, copy, replace_in_file, rmdir
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.scm import Git
from conan.tools.env import Environment

required_conan_version = ">=1.53.0"

class MAVSDKConan(ConanFile):
    name = "mavsdk"
    version = "3.15.0"
    license = "BSD-3-Clause"
    author = "SINTEF Ocean"
    homepage = "https://mavsdk.mavlink.io/main/en/"
    url = "https://github.com/mavlink/MAVSDK.git"
    description = "C++ library to interface with MAVLink systems"
    settings = "os", "compiler", "build_type", "arch"
    package_type = "library"
    options = {"fPIC": [True, False], "shared": [True, False]}
    default_options = {"fPIC": True, "shared": False}

    @property
    def _build_testing(self):
        return False and not self.conf.get("tools.build:skip_test", default=True, check_type=bool)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("jsoncpp/[>=1.9.5 <2]")
        self.requires("tinyxml2/[>=9.0.0 <10]")
        self.requires("libcurl/[>=7.86.0 <8]")
        self.requires("xz_utils/5.4.2")  # <-- add this
        self.requires("libevent/2.1.12")  
        
    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def build_requirements(self):
        if self._build_testing:
            self.test_requires("gtest/1.10.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["sdk"], strip_root=True)

        sources = self.conan_data["sources"][self.version]["mavlink"]
        mavlink_dir = join(self.source_folder, "src", "third_party", "mavlink", "include", "mavlink", "v2.0")
        git = Git(self, folder=mavlink_dir)
        git.fetch_commit(sources["url"], sources["commit"])

        # Patch to bypass find_package(MAVLink)
        core_cmakelists = join(self.source_folder, "src/mavsdk/core/CMakeLists.txt")
        
        replace_in_file(
            self,
            core_cmakelists,
            'find_package(MAVLink REQUIRED)',
            '# find_package(MAVLink REQUIRED) -- disabled by conan recipe')
            
        # replace_in_file(
            # self,
            # core_cmakelists,
            # 'get_target_property\\(.*MAVLink::mavlink.*\\)',
            # '# removed by Conan recipe: MAVLink target not available')
        
        replace_in_file(
            self,
            join(self.source_folder, "CMakeLists.txt"),
            'message(STATUS "Version: ${VERSION_STR}")',
            f'set(VERSION_STR v{self.version})\nmessage(STATUS "Version: ${{VERSION_STR}}")'
        )
                
        core_cmakelists = join(self.source_folder, "src/mavsdk/core/CMakeLists.txt")

        # ---- Remove entire get_target_property(...) block ----
        with open(core_cmakelists, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(core_cmakelists, "w", encoding="utf-8") as f:
            skipping = False
            for line in lines:
                if "get_target_property(" in line:
                    skipping = True
                    continue
                if skipping:
                    if ")" in line:
                        skipping = False
                    continue
                f.write(line)

        # ---- Remove any remaining MAVLink::mavlink references ----
        with open(core_cmakelists, "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace("MAVLink::mavlink", "")
        content = content.replace("mavlink::mavlink", "")

        with open(core_cmakelists, "w", encoding="utf-8") as f:
            f.write(content)

        mavsdk_cmakelists = join(self.source_folder, "src/mavsdk/CMakeLists.txt")

        disable_packages = (
            "find_package(libevents",
            "find_package(picosha2",
            "find_package(mav",
            "find_package(GTest",
        )

        with open(mavsdk_cmakelists, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(mavsdk_cmakelists, "w", encoding="utf-8") as f:
            for line in lines:
                if any(p in line for p in disable_packages):
                    f.write("# " + line)
                else:
                    f.write(line)
                    
        # Also force-disable tests at top level
        top_cmakelists = join(self.source_folder, "CMakeLists.txt")
        with open(top_cmakelists, "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace("BUILD_TESTS", "BUILD_TESTS_DISABLED")

        with open(top_cmakelists, "w", encoding="utf-8") as f:
            f.write(content)

        with open(top_cmakelists, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(top_cmakelists, "w", encoding="utf-8") as f:
            for line in lines:
                if "add_subdirectory(unit_tests" in line:
                    f.write("# " + line)
                else:
                    f.write(line)
                    
        # ---- Remove ALL GTest find_package calls globally ----
        for root, _, files in os.walk(self.source_folder):
            for name in files:
                if name == "CMakeLists.txt":
                    path = join(root, name)
                    with open(path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    with open(path, "w", encoding="utf-8") as f:
                        for line in lines:
                            if "find_package(GTest" in line:
                                f.write("# " + line)
                            else:
                                f.write(line)
                        
        tests = [
            (join(self.source_folder, "src", "integration_tests", "CMakeLists.txt"), "integration_tests"),
            (join(self.source_folder, "src", "cmake", "unit_tests.cmake"), "unit_tests")
        ]
        gtests = [("gtest_main", "GTest::Main"), ("gtest", "GTest::gtest"), ("gmock", "GTest::gmock")]

        # for f, target in tests:
            # replace_in_file(self, f, f"target_link_libraries({target}_runner", f"find_package(GTest REQUIRED)\ntarget_link_libraries({target}_runner")
            # for old, new in gtests:
                # replace_in_file(self, f, old, new)

        # replace_in_file(
            # self,
            # join(self.source_folder, "src/core/connection.h"),
            # "#include <unordered_set>",
            # "#include <unordered_set>\n#include <atomic>"
        # )

        # for f in [
            # "src/cmake/unit_tests.cmake",
            # "src/plugins/mission_raw/CMakeLists.txt",
            # "src/plugins/mission/CMakeLists.txt"
        # ]:
            # replace_in_file(self, join(self.source_folder, f), "JsonCpp::jsoncpp", "JsonCpp::JsonCpp")

        cmakelists = join(self.source_folder, "CMakeLists.txt")
        with open(cmakelists, "r+", encoding="utf-8") as f:
            content = f.read()

        if "cmake_minimum_required" not in content or "3.19" not in content:
            content = "cmake_minimum_required(VERSION 3.19)\n" + content
        if "project(" not in content:
            content = "project(MAVSDK CXX)\n" + content

        # Prepend CMP0091 policy and project minimum version
        prepend = "cmake_policy(SET CMP0091 NEW)\ncmake_minimum_required(VERSION 3.19)\nproject(MAVSDK CXX)\n"
        new_content = prepend + content

        with open(cmakelists, "w", encoding="utf-8") as f:
            f.write(new_content)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SUPERBUILD"] = True
        tc.variables["BUILD_MAVSDK_SERVER"] = False
        tc.variables["BUILD_TESTS"] = self._build_testing
        
        # MAVLink paths (use forward slashes)
        mavlink_include = str(Path(self.source_folder) / "src/third_party/mavlink/include").replace("\\", "/")
        tc.variables["MAVLINK_INCLUDE_DIR"] = mavlink_include
        
        mavlink_dir = str(Path(self.source_folder) / "src/third_party/mavlink").replace("\\", "/")
        tc.variables["MAVLINK_DIR"] = mavlink_dir
        
        # Disable internal find_package calls that fail
        tc.variables["MAVLINK_USE_CONAN"] = True        
        

        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        if self.settings.os == "Windows" and "Visual" in str(self.settings.compiler):
            runtime = str(self.settings.compiler.runtime)
            if runtime:
                if "MD" in runtime:
                    cmake.cache_variables["CMAKE_MSVC_RUNTIME_LIBRARY"] = "MultiThreadedDLL" + ("Debug" if "d" in runtime.lower() else "")
                else:
                    cmake.cache_variables["CMAKE_MSVC_RUNTIME_LIBRARY"] = "MultiThreaded" + ("Debug" if "d" in runtime.lower() else "")

        cmake.configure()
        cmake.build()

        if self._build_testing:
            with Environment().define("CTEST_OUTPUT_ON_FAILURE", "ON").vars(self).apply():
                cmake.test()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", self.source_folder, join(self.package_folder, "licenses"))
        rmdir(self, join(self.package_folder, "lib", "cmake"))
        if self.options.shared:
            copy(self, "*mavsdk*.dll", dst=join(self.package_folder, "bin"), src=join(self.build_folder, "src"), keep_path=False)

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "MAVSDK")
        self.cpp_info.set_property("cmake_target_name", "MAVSDK::MAVSDK")

        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m", "dl", "pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32"]

        plugins = [
            "mavsdk",
            "mavsdk_action",
            "mavsdk_calibration",
            "mavsdk_camera",
            "mavsdk_follow_me",
            "mavsdk_ftp",
            "mavsdk_geofence",
            "mavsdk_gimbal",
            "mavsdk_info",
            "mavsdk_log_files",
            "mavsdk_manual_control",
            "mavsdk_mavlink_passthrough",
            "mavsdk_mission",
            "mavsdk_mission_raw",
            "mavsdk_mocap",
            "mavsdk_offboard",
            "mavsdk_param",
            "mavsdk_shell",
            "mavsdk_telemetry",
            "mavsdk_transponder",
            "mavsdk_tune"
        ]
        self.cpp_info.libs = plugins
        self.cpp_info.includedirs = ["include/mavsdk"] + [f"include/mavsdk/plugins/{p.split('_',1)[1]}" for p in plugins if "_" in p]
