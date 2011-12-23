#!/usr/bin/python
#
# Copyright (C) 2011 Qilin Tan (tanqilin@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from utils import shellcmd, execute_addr2line,\
    check_args
import sys
import os
import argparse

def get_pid(process_name):
    command = "adb shell ps | grep %s" % (process_name)
    fp = shellcmd(command)
    if fp == -1:
        errMsg = "Don't get the PID of process %s, please make sure the given name is right\n" % (process_name)
        sys.stderr.write(errMsg)
        return -1
    
    rs = fp.readlines()
    if len(rs) != 1:
        pids = []
        for i in rs:
            p = i.split()
            if p[len(p) - 1] == process_name:
                return int(p[1])
            pids.append(i.split()[1])
        errMsg = "Get more then one PID (%s), please given a more accurate process name\n" % (", ".join(pids))
        sys.stderr.write(errMsg) 
        return -1
    return int(rs[0].split()[1])

def get_so_maps(pid):
    command = "adb shell cat /proc/%d/maps" % (pid)
    fp = shellcmd(command)
    if fp == -1:
        print("error in get so maps")
        return None
    rs = fp.readlines()
    so_maps = {}
    for i in rs:
        if i.find("/data/data/") == -1:
            continue;

        pos = i.find("-")
        if (pos == -1):
            continue
        addr = int(i[0:pos], 16)
        pos = i.rfind("/")
        if (pos == -1):
            continue
        so_name = i[pos+1:].strip()
        if not so_name in so_maps.keys():
            so_maps[so_name] = addr
    return so_maps

def parse_memory_stack(args):
    if args.alloc:
        alloc = open(args.alloc)
    else:
        return 1

    pid = get_pid(args.process)
    if pid == -1:
        return 2

    so_maps = get_so_maps(pid)
    if not so_maps:
        sys.stderr.write("Don't find the libraries of pid %d\n" % (pid))
        return 3
    if args.out:
        output = open(args.out, "w")
    else:
        output = sys.stdout
    for line in alloc:
        if line.find("/data/data") == -1:
            output.write(line)
        else:
            sp = line.split()
            if len(sp) <= 0:
                output.write(line)
                continue
            addr = int(sp[0], 16)
            pos = sp[1].rfind("/");
            if pos != -1:
                so_name = sp[1][pos+1:]
            else:
                continue
            if so_name not in so_maps:
                continue
            addr = addr - so_maps[so_name]
            libpath = os.path.join(args.symbols, so_name)
            (func, fs, line_num) = execute_addr2line(args.addr2line, libpath, addr)
            if func is not None:
                output.write("%s\t%s %s %s\n" %(line.rstrip(), func, fs, line_num))
            else:
                output.write(line)
    return 0

def generate_help(parser, category = False):
    if not parser:
        return;
    required = True
    parser.add_argument('-s', "--symbols", dest="symbols",
                        help="Contains full path to the root directory for symbols.",
                        metavar="path", required=True)
    parser.add_argument("-o", "--out", dest="out",
                        help="write the result into the out file. If omitted, the result is written into the stdout",
                        metavar="file")
    parser.add_argument("--android_ndk_home", dest="ndk_home",
                        help="path of the Android NDK home[optional]. If omitted, get it from environment by \"ANDROID_NDK_HOME\"",
                        metavar="path")
    if category:
        parser = parser.add_argument_group("memory")
        required = False
    parser.add_argument('-p', "--process", dest="process",
                        help="Process name you want to parse the memory stack",
                        metavar="process_name", required=required)
    parser.add_argument('-a', "--allocation", dest="alloc",
                        help="The allocation memory stack file",
                        metavar="file", required=required)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyze the memory stack to check memory leak")
    generate_help(parser, False);
    args = parser.parse_args()
    rs = check_args(args)
    if not rs:
        rs = parse_memory_stack(args)
    exit(rs)