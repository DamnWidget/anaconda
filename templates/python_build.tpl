{
    "name": "Anaconda Python Builder",
    "shell_cmd": "\"${python_interpreter}\" -u \"$file\"",
    "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
    "selector": "source.python"
}
