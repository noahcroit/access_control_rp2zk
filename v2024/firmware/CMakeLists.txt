cmake_minimum_required(VERSION 3.13)

# initialize the SDK based on PICO_SDK_PATH
# note: this must happen before project()
include(pico_sdk_import.cmake)

project(failsecure_fw)

# initialize the Raspberry Pi Pico SDK
pico_sdk_init()

# rest of your project
add_executable(failsecure_fw
    src/main_app.c
)

# Add pico_stdlib library which aggregates commonly used features
target_link_libraries(failsecure_fw
    pico_stdlib
    pico_cyw43_arch_lwip_threadsafe_background
    pico_lwip_mqtt
)

target_include_directories(failsecure_fw PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/include # for our common lwipopts
)

# create map/bin/hex/uf2 file in addition to ELF.
pico_add_extra_outputs(failsecure_fw)

# enable USB
pico_enable_stdio_usb(failsecure_fw 1)
pico_enable_stdio_uart(failsecure_fw 0)
