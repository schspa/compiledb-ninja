#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for generate comile_commands.json for for android"""
#
#   compiledb-ninja --- Tools for generate comile_commands.json for for android
#
#   Copyright (C) 2019, schspa , all rights reserved.
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import re
import subprocess
import json
import click

def get_status_output(cmd):
    """implement for shel command"""
    stdout = ''
    try:
        stdout = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as proce:
        return proce.returncode, stdout

    return 0, stdout


DESCRIPTION_PATTERN = re.compile(r"(?:^[\s]*)(?:description = )(?P<TARGET_TPYE>[^:]+)"
                                 + r"(?:\:[\s]*)(?P<TARGET>[\S]+)"
                                 + r"(?:[\s]*<=[\s]*)(?P<FILE>[\S]+)")
CMD_PATTERN = re.compile(r"(?:^[\s]*)(?:command = /bin/bash -c )(?P<CMD>.+)$")
FILE_REGEX = re.compile(r"^.+\.c$|^.+\.cc$|^.+\.cpp$|^.+\.cxx$|^.+\.s$", re.IGNORECASE)


# test_command="""
# command = /bin/bash -c "PWD=/proc/self/cwd  prebuilts/clang/host/linux-x86/clang-4691093/bin/clang++ 	-I miui/frameworks/base/native/libreshook/include -I frameworks/base/tools/aapt -I out/host/linux-x86/obj/EXECUTABLES/aapt_intermediates -I out/host/linux-x86/gen/EXECUTABLES/aapt_intermediates -I libnativehelper/include_jni \$$(cat out/host/linux-x86/obj/EXECUTABLES/aapt_intermediates/import_includes)  -I system/core/include -I system/media/audio/include -I hardware/libhardware/include -I hardware/libhardware_legacy/include -I hardware/ril/include -I libnativehelper/include -I frameworks/native/include -I frameworks/native/opengl/include -I frameworks/av/include  -c  -Wa,--noexecstack -fPIC -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=2 -fstack-protector -D__STDC_FORMAT_MACROS -D__STDC_CONSTANT_MACROS --gcc-toolchain=prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8 --sysroot prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8/sysroot -fstack-protector-strong -m64 -DANDROID -fmessage-length=0 -W -Wall -Wno-unused -Winit-self -Wpointer-arith -no-canonical-prefixes -DNDEBUG -UDEBUG -fno-exceptions -Wno-multichar -O2 -g -fno-strict-aliasing -fdebug-prefix-map=/proc/self/cwd= -D__compiler_offsetof=__builtin_offsetof -Werror=int-conversion -Wno-reserved-id-macro -Wno-format-pedantic -Wno-unused-command-line-argument -fcolor-diagnostics -Wno-expansion-to-defined -Wno-zero-as-null-pointer-constant -fdebug-prefix-map=\$$PWD/=   -target x86_64-linux-gnu -Bprebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8/x86_64-linux/bin  -Wsign-promo -Wno-inconsistent-missing-override -Wno-null-dereference -D_LIBCPP_ENABLE_THREAD_SAFETY_ANNOTATIONS -Wno-thread-safety-negative -Wno-gnu-include-next  -isystem prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8/x86_64-linux/include/c++/4.8 -isystem prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8/x86_64-linux/include/c++/4.8/backward -isystem prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8/x86_64-linux/include/c++/4.8/x86_64-linux -std=gnu++14  -DAAPT_VERSION=\\\"\$$(cat out/build_number.txt)\\\" -Wall -Werror -DMIUI_RES_HOOK -fPIE -D_USING_LIBCXX -DANDROID_STRICT -nostdinc++  -Werror=int-to-pointer-cast -Werror=pointer-to-int-cast -Werror=address-of-temporary -Werror=return-type -Wno-tautological-constant-compare -Wno-null-pointer-arithmetic -Wno-enum-compare -Wno-enum-compare-switch   -MD -MF out/host/linux-x86/obj/EXECUTABLES/aapt_intermediates/Main.d -o out/host/linux-x86/obj/EXECUTABLES/aapt_intermediates/Main.o frameworks/base/tools/aapt/Main.cpp"
# """

# obj = re.search(CMD_PATTERN, test_command)
# if obj is not None:
#     cmd = obj.group('CMD')
#     print(cmd)
#     status, output = get_status_output("echo " + cmd)
#     print("echo return {:}", status, output)

# exit(0)

def parse_file(infile, outfile):
    """parse command log file"""
    line_num = 0
    compile_command = []

    current_file = None
    for txt in infile:
        line_num = line_num + 1
        obj = re.search(DESCRIPTION_PATTERN, txt)
        if obj is not None and FILE_REGEX.match(obj.group('FILE')):
            current_file = obj.group('FILE')
        if current_file is None:
            continue
        obj = re.search(CMD_PATTERN, txt)
        if obj is not None:
            cmd = obj.group('CMD')
            status, output = get_status_output("echo " + cmd)
            if status != 0:
                print("""Error parsing line:{:d} current_file :{:s}
                cmd= \n{:s} \n txt={:s}\n""".format(
                    line_num, current_file, cmd, txt))
                exit(status)
            outputs = re.split(' |\n', output)
            if current_file is not None:
                source_dir = os.getenv("ANDROID_BUILD_TOP", os.getcwd())
                compile_command.append({"file": current_file,
                                        "directory": source_dir,
                                        "arguments": outputs})
                current_file = None
    outfile.write(json.dumps(compile_command, sort_keys=True, indent=4))

@click.command()
@click.option('-p', '--parse', 'infile', type=click.File('r'),
              help='Build log file to parse compilation commands from.' +
              '(Default: stdin)', required=False, default=sys.stdin)
@click.option('-o', '--output', 'outfile', type=click.File('w'),
              help="Output file path (Default: compile_commands.json)",
              required=False, default='compile_commands.json')
def compiledb_ninja(infile, outfile):
    """compiledb entry"""
    parse_file(infile, outfile)

if __name__ == '__main__':
    compiledb_ninja()
