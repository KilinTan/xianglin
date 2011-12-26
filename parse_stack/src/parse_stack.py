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
import argparse
from subprocess import Popen 

import crash_statck 
import memory_stack
import utils

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Analyze the android native crash stack or native memory stack")
    memory_stack.generate_help(parser, True);
    crash_statck.generate_help(parser, True);
    args = parser.parse_args()
    rs = utils.check_args(args)
    if rs:
        exit(rs)
    if args.alloc:
        rs = memory_stack.parse_memory_stack(args)
    else:
        rs = crash_statck.parse_crash_stack(args)
    exit(rs)
