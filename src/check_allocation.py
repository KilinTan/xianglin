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

if __name__ == "__main__":
    org_alloc = file(sys.argv[1]);
    new_alloc = file(sys.argv[2], "w");
    filter_str = sys.argv[3];
    print filter_str
    include = True
    if filter_str[0] == '!':
        filter_str = filter_str[1:]
        include = False
    alloc_array = []
    flag = False
    write_flag = False
    for line in org_alloc:
        if line.find("Allocations:") == 0:
            if not flag:
                flag = True
            else:
                if (include and write_flag) or (not include and not write_flag):
                    for l in alloc_array:
                        new_alloc.write(l)
                        print l,
                alloc_array = []
                write_flag = False
        alloc_array.append(line)
        
        if line.find(filter_str) != -1:
            write_flag = True
