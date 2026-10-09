# SPDX-License-Identifier: MIT
"""Compile the comment-policy controls before checking their expected refusals."""
from pathlib import Path
import shutil
import subprocess
import tempfile
from compiler_tokens import compiler


def selftest(work):
    from check_comments import check, check_file
    cases = {
        'c-identifier-digit': ('c', "#define V x1'a' /* prose */ 'b'\n", True),
        'cpp-identifier-digit': ('c++', "#define V x1'a' /* prose */ 'b'\n", True),
        'c-identifier-R': ('c', '#define XR\n#define S XR"(" /* prose */ ")"\n', True),
        'cpp-identifier-R': ('c++', '#define XR\n#define S XR"(" /* prose */ ")"\n', True),
        'cpp-digit-separator': ('c++', "int value = 1'000; // prose\n", True),
        'block-tail': ('c', '/* SPDX-License-Identifier: MIT\n * prose\n */\n', True),
        'spliced-delimiter': ('c', '/\\\n/ prose\n', True),
        'crlf-spliced-delimiter': ('c', '/\\\r\n/ prose\r\n', True),
        'carriage-return': ('c', '/* prose */\rint value;\r', True),
        'disabled-character': ('c', "#if '\\0'\nprose\n#endif\n", True),
        'disabled-elif': ('c++', "#if 1\n#elif L'\\0'\nprose\n#endif\n", True),
        'disabled-macro': ('c', '#ifdef UNLISTED\nprose\n#endif\n', True),
        'disabled-expression': ('c', '#if !1\nprose\n#endif\n', True),
        'inert-pragma': ('c', '#pragma message("prose")\n', True),
        'guard-macro-spoof': ('c', '#ifndef UNUSED_H\n#define UNUSED_H\nint value;\n#endif\n', True),
        'macro-override': ('c', '#define NDEBUG 1\n#ifndef NDEBUG\nprose\n#endif\n', True),
        'assembly-quote': ('asm', '.equ quote, \'" # prose "\n', True),
        'assembly-define-quote': ('asm', '#define V \'" # prose "\n.word V\n', True),
        'assembly-define-prose': ('asm', '#define V 4 # prose\n.word V\n', True),
        'assembly-macro-hash': ('asm', '#define HASH #\nnop HASH prose\n', True),
        'assembly-macro-trace': ('asm', '#define HASH #\nnop HASH REQ: PORT-01\n', True),
        'assembly-plain-define': ('asm', '#define V 4\n.word V\n', True),
        'assembly-spliced-define': ('asm', '#def\\\nine V 4\n.word V\n', True),
        'assembly-prose': ('asm', 'nop # prose\n', True),
        'assembly-formfeed': ('asm', 'nop \f#define prose\n', True),
        'assembly-formfeed-define': ('asm', '#define V 4 \f#define prose\n.word V\n', True),
        'assembly-verticaltab': ('asm', 'nop \v#define prose\n', True),
        'non-ascii': ('c', '/* caf\u00e9 */\nint value;\n', True),
        'control-byte': ('c', '/* \x1c */\nint value;\n', True),
        'assembly-pragma': ('asm', '#pragma prose\nnop\n', True),
        'assembly-conditional': ('asm', '.if 0\nprose\n.endif\n', True),
        'assembly-macro': ('asm', '.macro UNUSED\nprose\n.endm\n', True),
        'assembly-repeat': ('asm', '.rept 0\nprose\n.endr\n', True),
        'assembly-c-comment': ('asm', 'nop /* prose */\n', True),
        'c-tracing': ('c', '/* SPDX-License-Identifier: MIT */\n// IEEE 1722-2016 Figure 5\n', False),
        'cpp-raw-string': ('c++', 'const char *value = R"tag(// prose\n#if 0\n)tag";\n', False),
        'cpp-character': ('c++', "char quote = '\\''; // REQ: PORT-01\n", False),
        'cpp-number': ('c++', "int value = 1'000; // REQ: PORT-01\n", False),
        'allowed-conditional': ('c', '#ifdef NDEBUG\nint value;\n#else\nlong value;\n#endif\n', False),
        'assembly-tracing': ('asm', '# SPDX-License-Identifier: MIT\nnop # REQ: PORT-01\n', False),
        'assembly-string': ('asm', '.ascii "ordinary string"\n', False),
    }
    work.mkdir(parents=True, exist_ok=True)
    cross = shutil.which('riscv64-unknown-elf-gcc') or shutil.which('riscv64-elf-gcc')
    if not cross:
        raise RuntimeError('comment controls require an RV32 compiler')
    with tempfile.TemporaryDirectory(dir=work) as name:
        directory = Path(name)
        assembly = directory / 'link.S'
        assembly.write_text('.global _start\n_start:\nnop\n')
        obj = directory / 'link.o'
        subprocess.run([cross, '-march=rv32i', '-mabi=ilp32', '-c', str(assembly), '-o', str(obj)], check=True)
        linker = directory / 'link.ld'
        for label, source, refused in (
                ('linker-quote', "PROVIDE(probe' = 1); /* prose */ PROVIDE(end' = 2);\n", True),
                ('linker-tracing', '/* REQ: PORT-01 */\n', False)):
            linker.write_text(source + 'SECTIONS { . = 0x80000000; .text : { *(.text) } }\n')
            command = [cross, '-march=rv32i', '-mabi=ilp32', '-nostdlib',
                       '-T' + str(linker), str(obj), '-o', str(directory / 'link.elf')]
            subprocess.run(command, check=True, capture_output=True)
            errors = check(linker.read_text(), path='examples/rv32/link.ld')
            fatal = subprocess.run([*command, '-Wl,--fatal-warnings'], capture_output=True)
            if bool(errors) != refused or bool(fatal.returncode) != refused:
                raise RuntimeError(label + ': linker warning or policy result changed')
            print('comment control ' + label + ': linked; policy and fatal warnings ' + ('refuse' if refused else 'pass'))
        included = directory / 'tests/control.inc'
        included.parent.mkdir()
        included.write_text('// prose\n')
        unit = directory / 'unit.cpp'
        unit.write_text('#include "tests/control.inc"\nint value;\n')
        subprocess.run([compiler(), '-x', 'c++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                        '-c', str(unit), '-o', str(directory / 'unit.o')], check=True)
        if check_file(included, directory) != ['unscanned file suffix is forbidden']:
            raise RuntimeError('included unscanned suffix accepted')
        print('comment control included-suffix: compiled; refused')
        header = '#define IGNORE(a) 0\nenum { value = IGNORE(1\'2 // prose \'\n) };\n'
        for suffix in ('.h', '.hpp'):
            path = directory / ('control' + suffix)
            path.write_text(header)
            for language, standard in (('c', 'c11'), ('c++', 'c++20')):
                subprocess.run([compiler(), '-x', language, '-std=' + standard,
                                '-Wall', '-Wextra', '-Werror', '-c', str(path),
                                '-o', str(directory / 'header.o')], check=True)
            for fragment in (False, True):
                if not check(header, path='include/control' + suffix, fragment=fragment):
                    raise RuntimeError('header comment hidden from C++ accepted')
                if check('// REQ: PORT-01\n', path='include/control' + suffix, fragment=fragment):
                    raise RuntimeError('header tracing refused')
            print('comment control header' + suffix + ': C11 and C++20 compiled; source and fragment refused; tracing passes')
        for label, (language, source, refused) in cases.items():
            path = directory / (label + ('.S' if language == 'asm' else '.c'))
            path.write_text(source)
            command = ([cross, '-march=rv32i', '-mabi=ilp32'] if language == 'asm' else
                       [compiler(), '-x', language, '-std=' + ('c11' if language == 'c' else 'c++20'),
                        '-Wno-error=\u0023pragma-messages'])
            result = subprocess.run([*command, '-Wall', '-Wextra', '-Werror',
                                     '-c', str(path), '-o', str(path.with_suffix('.o'))],
                                    text=True, capture_output=True, timeout=30)
            if result.returncode:
                raise RuntimeError(label + ': control does not compile\n' + result.stderr)
            errors = check(source, language == 'asm', language if language != 'asm' else 'c')
            if bool(errors) != refused:
                raise RuntimeError(label + ': unexpected policy result: ' + str(errors))
            print('comment control ' + label + ': compiled; ' + ('refused' if refused else 'pass'))
