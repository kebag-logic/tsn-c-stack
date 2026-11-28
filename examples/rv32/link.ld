/* SPDX-License-Identifier: MIT */
ENTRY(_start)
MEMORY { ram (rwx) : ORIGIN = 0x80000000, LENGTH = 128M }
PHDRS { text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }
SECTIONS {
    .text : { KEEP(*(.text.start)) *(.text .text.*) } > ram :text
    .rodata : { *(.rodata .rodata.*) } > ram :text
    .data ALIGN(4096) : {
        __global_pointer$ = . + 0x800;
        *(.sdata .sdata.* .data .data.*)
    } > ram :data
    .bss (NOLOAD) : {
        . = ALIGN(4);
        __bss_start = .;
        *(.sbss .sbss.* .bss .bss.* COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > ram :data
    .stack (NOLOAD) : { . = ALIGN(16); . += 65536; __stack_top = .; } > ram :data
}
