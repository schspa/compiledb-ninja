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
    try:
        stdout = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as proce:
        return proce.returncode, stdout

    return 0, stdout


DESCRIPTION_PATTERN = re.compile(r"(?:^[\s]*)(?:description = )(?P<TARGET_TPYE>[^:]+)"
                                 + r"(?:\:[\s]*)(?P<TARGET>[\S]+)"
                                 + r"(?:[\s]*<=[\s]*)(?P<FILE>[\S]+)")
CMD_PATTERN = re.compile(r"(?:^[\s]*)(?:command = /bin/bash -c \")(?P<CMD>[^\"]+)")
FILE_REGEX = re.compile(r"^.+\.c$|^.+\.cc$|^.+\.cpp$|^.+\.cxx$|^.+\.s$", re.IGNORECASE)

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
            cmd = cmd.replace(r"\$$", r"$")
            status, output = get_status_output("echo " + cmd)
            if status != 0:
                print("""Error parsing line:{:d} current_file :{:s}
                cmd= \n{:s} \n""".format(
                    line_num, current_file, cmd))
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
              help="Output file path (Default: std output)",
              required=False, default='compile_commands.json')
def compiledb_ninja(infile, outfile):
    """compiledb entry"""
    parse_file(infile, outfile)

if __name__ == '__main__':
    compiledb_ninja()
