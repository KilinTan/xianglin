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

from subprocess import Popen
import subprocess
import os
import re
import sys

def shellcmd(command):
    try:
        p = Popen(command, stdout=subprocess.PIPE, shell=True)
    except ValueError:
        return -1
    status = p.wait()
    if status != 0:
        return -1
    return p.stdout

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

def find_addr2line():
    ndk_home_path = os.environ["ANDROID_NDK_HOME"]
    if ndk_home_path == None:
        sys.stderr.write("Don't find the ANDROID_NDK_HOME environment in you OS\n");
        return None

    return search_file(os.path.join(ndk_home_path, "toolchains"), "^arm.*addr2line$", True)

def execute_addr2line(addr2line, libpath, addr):
    command = "%s -f -e %s %x" %(addr2line, libpath, addr)
    fp = shellcmd(command)
    if fp == -1:
        return (None, None, None)
    func = fp.readline().strip()
    src = fp.readline().strip()
    src = src.split(":")
    return (func, src[0], src[1])