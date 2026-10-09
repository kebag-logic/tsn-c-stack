# SPDX-License-Identifier: MIT
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR riscv32)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
find_program(RV32_CC NAMES riscv64-unknown-elf-gcc riscv64-elf-gcc REQUIRED)
set(CMAKE_C_COMPILER "${RV32_CC}")
set(CMAKE_ASM_COMPILER "${RV32_CC}")
execute_process(COMMAND "${RV32_CC}" -print-file-name=include
  OUTPUT_VARIABLE RV32_BUILTIN_HEADERS OUTPUT_STRIP_TRAILING_WHITESPACE
  COMMAND_ERROR_IS_FATAL ANY)
set(CMAKE_C_FLAGS_INIT "-march=rv32i -mabi=ilp32 -ffreestanding -fno-builtin -nostdinc -isystem ${RV32_BUILTIN_HEADERS}")
set(CMAKE_ASM_FLAGS_INIT "-march=rv32i -mabi=ilp32")
set(TSN_TESTS OFF CACHE BOOL "Hosted tests" FORCE)
set(TSN_FREESTANDING ON CACHE BOOL "Freestanding link and smoke test" FORCE)
