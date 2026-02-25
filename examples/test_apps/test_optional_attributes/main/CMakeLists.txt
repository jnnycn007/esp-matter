set(SRC_DIRS_LIST "." )
set(INCLUDE_DIRS_LIST ".")
list(APPEND PRIV_INCLUDE_DIRS_LIST "${ESP_MATTER_PATH}/examples/common/utils")


idf_component_register(SRC_DIRS          ${SRC_DIRS_LIST}
                      PRIV_INCLUDE_DIRS  "."  ${PRIV_INCLUDE_DIRS_LIST}
                      INCLUDE_DIRS       ${INCLUDE_DIRS_LIST})

target_compile_options(${COMPONENT_LIB} PRIVATE "-DCHIP_HAVE_CONFIG_H")
