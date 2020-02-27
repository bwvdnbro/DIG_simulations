import sys
import re
import time
import datetime


def read_parameterfile(filename):
    file = open(filename, "r")

    params = {}
    indent = 0
    groupname = []
    lines = 0
    for line in file.readlines():
        if line[0] == "#":
            continue
        m = re.match(r"(?P<indent>[ ]*)(?P<groupname>.*?):([ ]?#.*?)?$", line)
        if m:
            lines += 1
            current_indent = len(m.group("indent"))
            if current_indent > indent:
                indent = current_indent
            if current_indent < indent:
                indent = current_indent
                groupname.pop()
            groupname.append(m.group("groupname"))
        m = re.match(
            r"(?P<indent>[ ]*)(?P<key>.*?):[ ]*" "(?P<value>.+?)[#\n]", line
        )
        if m:
            lines += 1
            current_indent = len(m.group("indent"))
            if current_indent > indent:
                indent = current_indent
            if current_indent < indent:
                indent = current_indent
                groupname.pop()
            groupname.append(m.group("key"))
            full_name = ":".join(groupname)
            groupname.pop()
            params[full_name] = m.group("value")

    return params


def write_parameterfile(filename, params):
    file = open(filename, "w")

    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime(
        "%d/%m/%Y, %H:%M:%S"
    )
    file.write(
        "# file automatically written by write_parameterfile.py on "
        "{timestamp}\n".format(timestamp=timestamp)
    )

    groupname = []
    stream = ""
    for key in sorted(params):
        keygroups = key.split(":")
        keyname = keygroups[-1]
        keygroups.pop()
        indent = ""
        if len(keygroups) > len(groupname):
            i = 0
            while i < len(groupname) and groupname[i] == keygroups[i]:
                i += 1
            for j in range(i):
                indent += "  "
            for j in range(i, len(groupname)):
                groupname.pop()
            for j in range(i, len(keygroups)):
                groupname.append(keygroups[j])
                stream += indent + keygroups[j] + ":\n"
                indent += "  "
        else:
            while len(keygroups) < len(groupname):
                groupname.pop()
            i = 0
            while i < len(keygroups) and groupname[i] == keygroups[i]:
                i += 1
            for j in range(i):
                indent += "  "
            for j in range(i, len(keygroups)):
                groupname.pop()
            for j in range(i, len(keygroups)):
                groupname.append(keygroups[j])
                stream += indent + keygroups[j] + ":\n"
                indent += "  "

        stream += indent + keyname + ": " + params[key] + "\n"

    file.write(stream)


if __name__ == "__main__":
    params = read_parameterfile(sys.argv[1])
    write_parameterfile(sys.argv[2], params)
