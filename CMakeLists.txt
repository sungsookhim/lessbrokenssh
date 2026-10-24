# ssheven
#
# Copyright (c) 2021 by cy384 <cy384@cy384.com>
# See LICENSE file for details

cmake_minimum_required(VERSION 3.9)

project(ssheven)

# CPU to tune for; applied to the app and the bundled libraries (see build-ssheven.bash)
# 68k: 68020, 68030, 68040 (always soft-float, since many 030/040 Macs lack an FPU)
# PPC: 601, 750 (G3)
IF(CMAKE_SYSTEM_NAME MATCHES Retro68)
  set(SSHEVEN_CPU 68020 CACHE STRING "target CPU")
  add_compile_options(-msoft-float)
ELSE()
  set(SSHEVEN_CPU 601 CACHE STRING "target CPU")
ENDIF()
add_application(ssheven CREATOR "SSH7" ssheven.c ssheven-console.c ssheven.r ssheven-net.c ssheven-debug.c ssheven-glyph.c)

# set up and build mbedtls
set(ENABLE_PROGRAMS OFF CACHE BOOL "disable mbedtls programs" FORCE)
set(UNSAFE_BUILD ON CACHE BOOL "ignore mac os jank for mbedtls" FORCE)
set(ENABLE_TESTING OFF CACHE BOOL "disable mbedtls tests" FORCE)
add_subdirectory(opentransport-mbedtls)

# set up and build libssh2
set(CRYPTO_BACKEND mbedTLS)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "disable libssh2 shared libs" FORCE)
set(BUILD_EXAMPLES OFF CACHE BOOL "disable libssh2 examples" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "disable libssh2 tests" FORCE)
add_subdirectory(opentransport-libssh2)

# set up and build libvterm
add_subdirectory(libvterm)

# the submodules hard-code -mcpu=68020 or -mcpu=601; add ours per target so it
# comes last on the command line and wins
foreach(lib ssheven mbedtls mbedx509 mbedcrypto everest p256m libssh2_static vterm)
  if(TARGET ${lib})
    target_compile_options(${lib} PRIVATE -mcpu=${SSHEVEN_CPU})
  endif()
endforeach()

IF(CMAKE_SYSTEM_NAME MATCHES Retro68)
# for 68k
  set_target_properties(ssheven PROPERTIES COMPILE_FLAGS "-ffunction-sections -O3 -Wall -Wextra -Wno-unused-parameter")
  set_target_properties(ssheven PROPERTIES LINK_FLAGS "-Wl,-gc-sections -Wl,--mac-segments -Wl,${CMAKE_CURRENT_SOURCE_DIR}/ssheven.segmap")
  target_link_libraries(ssheven libssh2 mbedtls mbedx509 mbedcrypto OpenTransportApp OpenTransport OpenTptInet vterm retrocrt)
ELSE()
# for PPC
  set_target_properties(ssheven PROPERTIES COMPILE_FLAGS "-ffunction-sections -O3 -Wall -Wextra -Wno-unused-parameter")
  set_target_properties(ssheven PROPERTIES LINK_FLAGS "-Wl,-gc-sections")
  target_link_libraries(ssheven ThreadsLib libssh2 mbedtls mbedx509 mbedcrypto OpenTransportAppPPC OpenTransportLib OpenTptInternetLib vterm retrocrt)
ENDIF()
