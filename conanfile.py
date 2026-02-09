from os.path import join
from conan import ConanFile
from conan.tools.files import get, copy
from conan.tools.files import replace_in_file, rmdir
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.scm import Git
from conan.tools.env import Environment

required_conan_version = ">=1.53.0"


class MAVSDKConan(ConanFile):
    name = "mavsdk"
    version = "1.4.16"
    license = "BSD-3-Clause"
    author = "SINTEF Ocean"
    homepage = "https://mavsdk.mavlink.io/main/en/"
    url = "https://github.com/mavlink/MAVSDK.git"
    description = "C++ library to interface with MAVLink systems"
    settings = "os", "compiler", "build_type", "arch"
    package_type = "library"
    options = {
        "fPIC": [True, False],
        "shared": [True, False]
        }
    default_options = {
        "fPIC": True,
        "shared": False
        }

    @property
    def _build_testing(self):
        # TODO: DISABLED for time-being
        return False and not self.conf.get("tools.build:skip_test",
                             default=True, check_type=bool)

    def export_sources(self):
        pass
        #export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("jsoncpp/[>=1.9.5 <2]")
        self.requires("tinyxml2/[>=9.0.0 <10]")
        self.requires("libcurl/[>=7.86.0 <8]")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def build_requirements(self):
        if self._build_testing:
            self.test_requires("gtest/1.10.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["sdk"], strip_root=True)
        sources = self.conan_data["sources"][self.version]["mavlink"]
        mavlink_dir = join(self.source_folder, "src", "third_party",
                           "mavlink", "include", "mavlink", "v2.0")
        git = Git(self, folder=mavlink_dir)
        git.fetch_commit(sources["url"], sources["commit"])

        # tinyxml.h is used in camera_definition_test, so unit_tests must link to tinyxml2::tinyxml2
        replace_in_file(self, join(self.source_folder, "src", "cmake", "unit_tests.cmake"),
                        "gtest_main", "gtest_main\n    tinyxml2::tinyxml2")

        # TODO: create instead patch files to simplify building versions
        replace_in_file(self, join(self.source_folder, "CMakeLists.txt"),
                        'message(STATUS "Version: ${VERSION_STR}")',
                        f'set(VERSION_STR v{self.version})\nmessage(STATUS "Version: ${{VERSION_STR}}")')

        replace_in_file(self, join(self.source_folder, "src", "CMakeLists.txt"),
                        'add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/third_party/gtest EXCLUDE_FROM_ALL)',
                        '')

        # Link gtest from conan
        tests = [(join(self.source_folder, "src", "integration_tests", "CMakeLists.txt"), "integration_tests"),
                 (join(self.source_folder, "src", "cmake", "unit_tests.cmake"), "unit_tests")]

        gtests = [("    gtest_main", "    GTest::Main"),
                  ("    gtest", "    GTest::gtest"),
                  ("    gmock", "    GTest::gmock")]

        for a_test in tests:
            replace_in_file(self, a_test[0],
                            f"target_link_libraries({a_test[1]}_runner",
                            f"find_package(GTest REQUIRED)\ntarget_link_libraries({a_test[1]}_runner")

            for gt in gtests:
                replace_in_file(self, a_test[0],
                                gt[0], gt[1])

        replace_in_file(self, join(self.source_folder, "src/core/connection.h"),
                        "#include <unordered_set>",
                        "#include <unordered_set>\n#include <atomic>")

        link_jsonpp = ["src/cmake/unit_tests.cmake",
                       "src/plugins/mission_raw/CMakeLists.txt",
                       "src/plugins/mission/CMakeLists.txt"]

        for f in link_jsonpp:
            replace_in_file(self, join(self.source_folder, f),
                            "JsonCpp::jsoncpp", "JsonCpp::JsonCpp")
        
        # JJF -- Debug only
        # print(self.conan_data)
        
        
    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SUPERBUILD"] = False
        tc.variables["BUILD_MAVSDK_SERVER"] = False
        tc.variables["BUILD_TESTS"] = self._build_testing
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()


    def build(self):
        #apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

        if self._build_testing:
            env = Environment()
            env.define("CTEST_OUTPUT_ON_FAILURE", "ON")
            with env.vars(self).apply():
                cmake.test()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(self, "LICENSE", self.source_folder,
             join(self.package_folder, "licenses"))
        rmdir(self, join(self.package_folder, "lib", "cmake"))
        if self.options.shared:
            copy(self, "*mavsdk*.dll", dst=join(self.package_folder, "bin"), src=join(self.build_folder, "src"), keep_path=False)

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "MAVSDK")
        self.cpp_info.set_property("cmake_target_name", "MAVSDK::MAVSDK")

        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m", "dl", "pthread"]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32"]

        self.cpp_info.libs = [
                "mavsdk",
                "mavsdk_action",
                "mavsdk_calibration",
                "mavsdk_camera",
                "mavsdk_failure",
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
                "mavsdk_server_utility",
                "mavsdk_shell",
                "mavsdk_telemetry",
                "mavsdk_tracking_server",
                "mavsdk_transponder",
                "mavsdk_tune"
            ]

        self.cpp_info.includedirs.extend([
            "include/mavsdk",
            "include/mavsdk/plugins/action",
            "include/mavsdk/plugins/calibration",
            "include/mavsdk/plugins/camera",
            "include/mavsdk/plugins/failure",
            "include/mavsdk/plugins/follow_me",
            "include/mavsdk/plugins/ftp",
            "include/mavsdk/plugins/geofence",
            "include/mavsdk/plugins/gimbal",
            "include/mavsdk/plugins/info",
            "include/mavsdk/plugins/log_files",
            "include/mavsdk/plugins/manual_control",
            "include/mavsdk/plugins/mavlink_passthrough",
            "include/mavsdk/plugins/mission",
            "include/mavsdk/plugins/mission_raw",
            "include/mavsdk/plugins/mocap",
            "include/mavsdk/plugins/offboard",
            "include/mavsdk/plugins/param",
            "include/mavsdk/plugins/server_utility",
            "include/mavsdk/plugins/shell",
            "include/mavsdk/plugins/telemetry",
            "include/mavsdk/plugins/tracking_server",
            "include/mavsdk/plugins/transponder",
            "include/mavsdk/plugins/tune",
        ])