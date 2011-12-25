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
import re
import os
from utils import execute_addr2line, check_args
import argparse
import sys


sohead = re.compile('(.+\.so):')
funchead = re.compile('([0-9a-f]{8}) <(.+)>:')
funcline = re.compile('^[ ]+([0-9a-f]+):.+')
crashline = re.compile('.+pc.([0-9a-f]{8})\s(.+?\.so).*')

def parsestack(lines):
    ret = []
    for l in lines:
        addr, libname = parsestackline(l)
        if addr == 0 or libname == None:
            continue
        ret.append((addr, libname))
    return ret

def parsestackline(line):
    m = crashline.match(line)
    ret = 0
    libname = None
    if m:
        addr =  m.groups()[0]
        ret = int(addr,16)
        libname = m.groups()[1][m.groups()[1].rfind("/")+1:]
    return (ret, libname)

def print_crash_stack(output, rs):
    output.write("Crash statck ===================================================\n")
    for line in rs:
        output.write("%s\n" %(line))
    output.write("Crash statck ===================================================\n")

def parse_crash_stack(args):
    if os.path.exists(args.dump):
        stack = open(args.dump);
    else:
        return 1
    if args.out:
        output = open(args.out, "w")
    else:
        output = sys.stdout
    parse_rs = []
    print_flag = False
    while True:
        try:
            line = stack.readline()
        except KeyboardInterrupt:
            break
        if not line:
            break
        if line.find("*** *** ***") != -1:
            print_flag = False
        if line.strip() == "print":
            print_crash_stack(output, parse_rs)
            parse_rs = []
        addr, libname = parsestackline(line)
        if addr == 0 or libname == None:
            continue
        libpath = os.path.join(args.symbols, libname)
        if not os.path.exists(libpath):
            continue

        func, src, line = execute_addr2line(args.addr2line, libpath, addr)
        if func and src and line:
            if print_flag:
                output.write("0x%08x:%32s\t\t%s:%s\n" % (addr, func, src, line))
            else:
                parse_rs.append("0x%08x:%32s\t\t%s:%s" % (addr, func, src, line))

    if len(parse_rs) > 0:
        print_crash_stack(output, parse_rs)
        parse_rs = []
    return 0

def generate_help(parser, category=False):
    if not parser:
        return;
    required = True
    try:
        parser.add_argument('-s', "--symbols", dest="symbols",
                            help="Contains full path to the root directory for symbols.",
                            metavar="path", required=True)
        parser.add_argument("-o", "--out", dest="out",
                            help="write the result into the out file. If omitted,"
                            " the result is written into the stdout",
                            metavar="file")
        parser.add_argument("--android_ndk_home", dest="ndk_home",
                            help="path of the Android NDK home[optional]. If omitted,"
                            " get it from environment by \"ANDROID_NDK_HOME\"",
                            metavar="path")
    except argparse.ArgumentError:
        pass
    if category:
        parser = parser.add_argument_group("crash")
        required = False
    parser.add_argument('-d', "--dump", dest="dump",
                      help="The crash dump. This is an optional parameter."
                           " If omitted, parse_stack will read input data from stdin",
                      metavar="file", required=required)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyze the crash stack to print crash functions")
    generate_help(parser, False);
    args = parser.parse_args()
    rs = check_args(args)
    if not rs:
        rs = parse_crash_stack(args)
    exit(rs)
