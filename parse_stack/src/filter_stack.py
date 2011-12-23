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

def read_allocation_block(fp, filter_str, included = True):
    if fp == None or filter_str == None:
        return
    line = fp.readline();
    found = False
    block = []
    begin = False;
    while line:
        l = line.rstrip();
        if line.find("Allocations:") != -1:
            begin = True
            block.append(l)
        elif line.find("EndStacktrace") != -1:
            block.append(l)
            break;
        elif not l:
            break;
        elif begin == True:
            if (not found) and (line.find(filter_str) != -1):
                found = True
            block.append(l)
        line = fp.readline()
    if not line:
        return None
    if found and included:
        return block
    elif not (found or included):
        return block
    else:
        return []

def write_allocation_block(fp, block):
    for b in block:
        fp.write(b+"\n")
    fp.write("\n")

if __name__ == "__main__":
    if len(sys.argv) > 3:
        org_alloc = open(sys.argv[1], "r");
        new_alloc = open(sys.argv[2], "w");
        filter_str = sys.argv[3];
    elif len(sys.argv) == 3:
        org_alloc = open(sys.argv[1], "r");
        new_alloc = sys.stdout
        filter_str = sys.argv[2];
    else:
        exit(-1)
    included = True
    if filter_str[0] == '!':
        filter_str = filter_str[1:]
        included = False
    while True:
        block = read_allocation_block(org_alloc, filter_str, included)
        if block and len(block) > 0:
            write_allocation_block(new_alloc, block)
        elif block == None:
            break
    org_alloc.close()
    new_alloc.close()
