#!/usr/bin/env python3
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

import json
import os
import queue
import re
import subprocess
import sys
import click
from multiprocessing import Process, Queue, Value

DESCRIPTION_PATTERN = re.compile(r"(?:^[\s]*)(?:description = )(?P<TARGET_TPYE>[^:]+)"
                                 + r"(?:\:[\s]*)(?P<TARGET>[\S]+)"
                                 + r"(?:[\s]*<=[\s]*)(?P<FILE>[\S]+)")
CMD_PATTERN = re.compile(r"(?:^[\s]*)(?:command = /bin/bash -c )(?P<CMD>.+)$")
FILE_REGEX = re.compile(r"^.+\.c$|^.+\.cc$|^.+\.cpp$|^.+\.cxx$|^.+\.s$", re.IGNORECASE)
FIRST_CMD_REGEX = re.compile(r"(?P<BEG>^\"\()(?P<PWD>PWD=\S*\s*)?(?P<CMD>[^&]*)(?P<END>\)\s*\&)")
MANUAL_EXITCODE = 1
source_dir = os.getenv("ANDROID_BUILD_TOP", os.getcwd())


def get_status_output(cmd):
    """For parsing a cmd from ninja format to original shell command format"""
    stdout = ''
    try:
        stdout = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as proce:
        return proce.returncode, stdout
    return 0, stdout.decode('utf-8')


def has_multiple_cmds(cmdline):
    return cmdline[:2] == '"('


def extract_first_cmd(cmdline):
    obj = re.search(FIRST_CMD_REGEX, cmdline)
    if obj is not None:
        first_cmd = obj.group('CMD')
        return f'"{first_cmd}"'
    else:
        print("Error parsing multiline cmd, txt={:s}\n".format(cmdline))
        exit(-1)


def parse_func(parsing_queue, result_queue, working, processed_lines, exit_flag, quite):
    """Parse Ninja commands which were read from file in another proc"""
    # qsize, full, empty in Python multiprocessing Queue are all unreliable
    while (exit_flag.value == 0) and (working.value != 0):
        try:
            s = parsing_queue.get_nowait()
        except queue.Empty:
            continue
        cmd, current_file = s

        if cmd is None and current_file is None:
            # notify all parse func to stop
            working.value = 0
            break

        processed_lines.value += 1
        if quite == 0:
            print(processed_lines.value)
        status, output = get_status_output("echo " + cmd)
        if status != 0:
            print("""Error parsing current_file :{:s}
            cmd= \n{:s} \n """.format(current_file, cmd))
            exit(status)
        outputs = re.split('[ \n]', output)
        result_queue.put({"file": current_file,
                          "directory": source_dir,
                          "arguments": outputs})
    result_queue.put(None)


def parse_file(infile, parsing_queue, working, exit_flag):
    """parse Ninja file to obtain all command line"""
    line_num = 0
    current_file = None
    for txt in infile:
        line_num += 1
        obj = re.search(DESCRIPTION_PATTERN, txt)
        if obj is not None and FILE_REGEX.match(obj.group('FILE')):
            current_file = obj.group('FILE')
        if current_file is None:
            continue
        obj = re.search(CMD_PATTERN, txt)
        if obj is not None:
            cmd = obj.group('CMD')
            if has_multiple_cmds(cmd):
                cmd = extract_first_cmd(cmd)
            parsing_queue.put([cmd, current_file])
            current_file = None
    parsing_queue.put([None, None])


def write_ret(result_queue, outfile, nprocs):
    with open(outfile, 'w') as f:
        n_parse_cmd_proc_return = 0
        result_list = []
        while n_parse_cmd_proc_return < nprocs:
            r = result_queue.get()
            if r is None:
                n_parse_cmd_proc_return += 1
            else:
                result_list.append(r)
        print("Writing result to disk")
        f.write(json.dumps(result_list, sort_keys=True, indent=4))


@click.command()
@click.option('-q', '--quite', 'quite', flag_value='quite', default=False,
              help='Use quite output')
@click.option('-j', '--nprocs', 'nprocs', default=1,
              help='Number of threads parsing commands')
@click.option('-p', '--parse', 'infile', type=click.File('r'),
              help='Build log file to parse compilation commands from.' +
                   '(Default: stdin)', required=False, default=sys.stdin)
@click.option('-o', '--output', 'outfile',
              help="Output file path (Default: compile_commands.json)",
              required=False, default='compile_commands.json')
def compiledb_ninja(infile, outfile, nprocs, quite):
    """compiledb entry"""
    working = Value('i', 1)
    exit_flag = Value('i', 0)
    processed_lines = Value('i', 0)
    parsing_queue = Queue()
    result_queue = Queue()
    main_pid = os.getpid()
    print(f"Using {nprocs} to parse commands")

    th_parse_file = Process(target=parse_file,
                            args=(infile,
                                  parsing_queue,
                                  working,
                                  exit_flag
                                  ))
    th_write_ret = Process(target=write_ret,
                           args=(result_queue,
                                 outfile,
                                 nprocs
                                 ))
    th_parse_cmds = []
    for i in range(0, nprocs):
        th_parse_cmds.append(Process(target=parse_func,
                                     args=(parsing_queue,
                                           result_queue,
                                           working,
                                           processed_lines,
                                           exit_flag,
                                           quite
                                           )))
    th_parse_file.start()
    th_write_ret.start()
    for i in range(0, nprocs):
        th_parse_cmds[i].start()
    th_parse_file.join()
    th_write_ret.join()
    for i in range(0, nprocs):
        th_parse_cmds[i].join()


if __name__ == '__main__':
    compiledb_ninja()
