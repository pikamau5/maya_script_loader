'''
how to

open commandline
run this script with mayapy
TODO: check if dependencies are already installed
'''

import sys
import ctypes, sys, os
import time

def pip_auto_install(selected_item):
    """
    Automatically installs all requirements if pip is installed.
    """


    maya_exe = sys.executable.split(".")[0] + "py.exe"
    maya_exe = maya_exe.replace("\\", "/")
    # install dependencies
    command = "\"" + str(maya_exe) + "\"" + " -m pip install " + "\"" + selected_item + "\""
    print command
    os.system('"' + command + " & pause" + '"')


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_dependencies(selected_item):
    whl = str(selected_item).split(".")
    whl = whl[-1]
    if whl != "whl":
        print "not a whl file"
        return

    if is_admin():
        # Code of your program here
        pip_auto_install(selected_item)
    else:
        # Re-run the program with admin rights

        maya_exe = sys.executable.split(".")[0] + "py.exe"
        maya_exe = maya_exe.replace("\\", "/")
        # install dependencies as admin
        ctypes.windll.shell32.ShellExecuteW(None, u"runas",unicode(maya_exe), unicode(" -m pip install " + "\"" + selected_item + "\""), None, 1)

    is_admin()
