cmake_minimum_required(VERSION 3.16)
project(ebpf)
set(CMAKE_CXX_STANDARD 20)

# Tell cmake where to find BpfObject module
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/libbpf-bootstrap/tools/cmake)

# Build vendored libbpf
include(ExternalProject)
ExternalProject_Add(libbpf
    PREFIX libbpf
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/libbpf-bootstrap/libbpf/src
    CONFIGURE_COMMAND ""
    BUILD_COMMAND make
    BUILD_STATIC_ONLY=1
    OBJDIR=${CMAKE_CURRENT_BINARY_DIR}/libbpf/libbpf
    DESTDIR=${CMAKE_CURRENT_BINARY_DIR}/libbpf
    INCLUDEDIR=
    LIBDIR=
    UAPIDIR=
    install install_uapi_headers
    BUILD_IN_SOURCE TRUE
    INSTALL_COMMAND ""
    STEP_TARGETS build
    )

ExternalProject_Add(bpftool
    PREFIX bpftool
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/libbpf-bootstrap/bpftool/src
    CONFIGURE_COMMAND ""
    BUILD_COMMAND make bootstrap
    OUTPUT=${CMAKE_CURRENT_BINARY_DIR}/bpftool/
    BUILD_IN_SOURCE TRUE
    INSTALL_COMMAND ""
    STEP_TARGETS build
    )

# Set BpfObject input parameters -- note this is usually not necessary unless
# you're in a highly vendored environment (like libbpf-bootstrap)
if(${CMAKE_SYSTEM_PROCESSOR} MATCHES "x86_64")
    set(ARCH "x86")
elseif(${CMAKE_SYSTEM_PROCESSOR} MATCHES "arm")
    set(ARCH "arm")
elseif(${CMAKE_SYSTEM_PROCESSOR} MATCHES "aarch64")
    set(ARCH "arm64")
elseif(${CMAKE_SYSTEM_PROCESSOR} MATCHES "ppc64le")
    set(ARCH "powerpc")
elseif(${CMAKE_SYSTEM_PROCESSOR} MATCHES "mips")
    set(ARCH "mips")
elseif(${CMAKE_SYSTEM_PROCESSOR} MATCHES "riscv64")
    set(ARCH "riscv")
elseif(${CMAKE_SYSTEM_PROCESSOR} MATCHES "loongarch64")
    set(ARCH "loongarch")
endif()

set(BPFOBJECT_BPFTOOL_EXE ${CMAKE_CURRENT_BINARY_DIR}/bpftool/bootstrap/bpftool)
set(BPFOBJECT_VMLINUX_H ${CMAKE_CURRENT_SOURCE_DIR}/libbpf-bootstrap/vmlinux/${ARCH}/vmlinux.h)
set(LIBBPF_INCLUDE_DIRS ${CMAKE_CURRENT_BINARY_DIR}/libbpf)
set(LIBBPF_LIBRARIES ${CMAKE_CURRENT_BINARY_DIR}/libbpf/libbpf.a)
find_package(BpfObject REQUIRED)

# Generate BPF skeleton
bpf_object(ebpf ebpf.bpf.c)
add_dependencies(ebpf_skel libbpf-build bpftool-build)

# Add BPF skeleton to target
add_executable(ebpf ebpf.cpp)
target_link_libraries(ebpf ebpf_skel)

# For highlighting in IDE
add_library(ebpf_bpf OBJECT ${BPF_C_FILE})
target_include_directories(ebpf_bpf PRIVATE ${GENERATED_VMLINUX_DIR})
target_include_directories(ebpf_bpf SYSTEM PRIVATE ${LIBBPF_INCLUDE_DIRS})
set_target_properties(ebpf_bpf PROPERTIES EXCLUDE_FROM_ALL TRUE)


add_executable(main main.cpp)

