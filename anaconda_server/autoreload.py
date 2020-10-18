#!/usr/bin/env python
#
# Autoreloader for jsonserver for development.
# Run with:
# python3 autoreload.py python3 jsonserver.py -p<project_name> 9999 DEBUG
#

import os
import sys
import subprocess
import time
from pathlib import Path


def file_filter(path):
    return (not path.name.startswith(".")) and (path.suffix not in (".swp",) )


def file_times(path):
    absolute_path = path.resolve()
    for file in filter(file_filter, absolute_path.iterdir()):
        if file.is_dir():
            for x in file_times(file):
                yield x
        else:
            yield os.path.getctime(file)


def print_stdout(process):
    stdout = process.stdout
    if stdout != None:
        print(stdout)
    stderr = process.stderr
    if stderr != None:
        print(stderr)


# We concatenate all of the arguments together, and treat that as the command to run
command = " ".join(sys.argv[1:])

# The path to watch
path = Path("..")

# How often we check the filesystem for changes (in seconds)
wait = 1

# The process to autoreload
print("Started: ", command)
process = subprocess.Popen(command, shell=True)

# The current maximum file modified time under the watched directory
last_mtime = max(file_times(path))

while True:
    max_mtime = max(file_times(path))
    print_stdout(process)
    if max_mtime > last_mtime:
        last_mtime = max_mtime
        print("Restarting process.")
        process.kill()
        process = subprocess.Popen(command, shell=True)
    time.sleep(wait)
