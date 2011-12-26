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

import sys
import re
import os
import subprocess
from subprocess import Popen 
from optparse import OptionParser

sohead = re.compile('(.+\.so):')
funchead = re.compile('([0-9a-f]{8}) <(.+)>:')
funcline = re.compile('^[ ]+([0-9a-f]+):.+')
crashline = re.compile('.+pc.([0-9a-f]{8})\s(.+?\.so).*')

def shellcmd(command):
    try:
        p = Popen(command, stdout=subprocess.PIPE, shell=True)
    except ValueError:
        return -1
    status = p.wait()
    if status != 0:
        return -1
    return p.stdout

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

def find_addr2line():
    ndk_home_path = os.environ["ANDROID_NDK_HOME"]
    if ndk_home_path == None:
        sys.stderr.write("Don't find the ANDROID_NDK_HOME environment in you OS\n");
        return None

    return search_file(os.path.join(ndk_home_path, "toolchains"), "^arm.*addr2line$", True)

def search_file(directory, name, regular = False):
    if os.path.exists(directory) != True:
        return None
    if regular:
        search = re.compile(name)
    else:
        search = None
    for root, dirs, files in os.walk(directory):
        for fname in files:
            if search == None:
                if fname == name:
                    return os.path.join(root, fname)
            else:
                rs = search.match(fname)
                if rs is not None:
                    return os.path.join(root, fname);
    return None

def execute_addr2line(addr2line, libpath, addr):
    command = "%s -f -e %s %x" %(addr2line, libpath, addr)
    fp = shellcmd(command)
    if fp == -1:
        return (None, None, None)
    func = fp.readline().strip()
    src = fp.readline().strip()
    src = src.split(":")
    return (func, src[0], src[1])

def print_crash_stack(output, rs):
    output.write("Crash statck ===================================================\n")
    for line in rs:
        output.write("%s\n" %(line))
    output.write("Crash statck ===================================================\n")

def parse_crash_stack(options, addr2line, stack, output):

    parse_rs = []
    while True:
        try:
            line = stack.readline()
        except KeyboardInterrupt:
            break
        if not line:
            break
        if line.strip() == "print":
            print_crash_stack(output, parse_rs)
            parse_rs = []
        addr, libname = parsestackline(line)
        if addr == 0 or libname == None:
            continue
        libpath = os.path.join(options.symbols, libname)
        if not os.path.exists(libpath):
            continue

        func, src, line = execute_addr2line(addr2line, libpath, addr)
        if func and src and line:
            parse_rs.append("0x%08x:%32s    %s:%s" % (addr, func, src, line))

    if len(parse_rs) > 0:
        print_crash_stack(output, parse_rs)
        parse_rs = []
    return 0

def getPID(process_name):
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

def getSoMaps(pid):
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

def parse_memory_stack(options, addr2line, alloc, output):
    if options.process == None:
        sys.stderr.write("The process name is required for parse memory stack\n")
        return -1
    pid = getPID(options.process)
    if pid == -1:
        return -1
    so_maps = getSoMaps(pid)
    if not so_maps:
        sys.stderr.write("Don't find the libraries of pid %d\n" % (pid))
        return -1
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
            libpath = os.path.join(options.symbols, so_name)
            (func, fs, line_num) = execute_addr2line(addr2line, libpath, addr)
            if func is not None:
                output.write("%s\t%s %s %s\n" %(line.rstrip(), func, fs, line_num))
            else:
                output.write(line)
    return 0
if __name__=="__main__":

    parser = OptionParser(usage="%prog -s <path> [-d <file>] [-a <file> -p <process> [-o <file>]] [--android_ndk_home=<path>]" )
    parser.add_option('-s', "--symbols", dest="symbols", help="Contains full path to the root directory for symbols.", metavar="path")
    parser.add_option('-d', "--dump", dest="dump", help="The crash dump. This is an optional parameter. If omitted, parse_stack will read input data from stdin", metavar="file")
    parser.add_option('-p', "--process", dest="process", help="Process name you want to parse the memory stack", metavar="process_name")
    parser.add_option('-a', "--allocation", dest="alloc", help="The allocation memory stack file", metavar="file")
    parser.add_option("-o", "--out", dest="out", help="write the result into the out file. If omitted, the result is written into the stdout", metavar="file")
    parser.add_option("--android_ndk_home", dest="ndk_home", help="path of the Android NDK home[optional]. If omitted, get it from environment by \"ANDROID_NDK_HOME\"", metavar="path")

    (options, args) = parser.parse_args()
    
    if options.symbols is None:
        sys.stderr.write("The symbols is required\n")
        parser.print_help();
        exit(1)
    else:
        if not os.path.exists(options.symbols):
            sys.stderr.write("The symbols(%s) is not existed\n" %(options.symbols))
            exit(1)

    if options.dump is not None:
        stack = file(options.dump, "r")
    else:
        stack = sys.stdin

    if options.alloc is not None:
        alloc = file(options.alloc, "r")
    else:
        alloc = None

    if options.out is not None:
        output = file(options.out, "w")
    else:
        output = sys.stdout
    if options.ndk_home is not None:
        if os.path.exists(options.ndk_home):
            addr2line = search_file(os.path.join(options.ndk_home, "toolchains"), "^arm.*addr2line$", True)
        else:
            sys.stderr.write("The android_ndk_home is incorrect path\n")
            exit(1)
    else:
        addr2line = find_addr2line()
    if addr2line is None:
        sys.stderr.write("Can find the addr2line command from the ANDROID_NDK_HOME.\n")
        exit(1)

    if alloc is not None:
        rs = parse_memory_stack(options, addr2line, alloc, output)
    else:
        rs = parse_crash_stack(options, addr2line, stack, output)
    exit(rs)
