'''
Install python dependencies as admin.
TODO: check if dependencies are already installed
'''

import ctypes
import sys


def pip_auto_install(dependency):
    """
    Automatically installs all requirements if pip is installed.
    Args:
        dependency: dependency list to send to pip
    """
    # requirements_file = script_folder + "/requirements.txt"
    try:
        from pip._internal import main as pip_main
        pip_main(['install', dependency])  # run pip to install the dependencies
    except ImportError:
        print("Failed to import pip. Please ensure that pip is installed.")
        sys.exit(-1)
    except Exception as err:
        print("Failed to install pip requirements: " + err.message)
        sys.exit(-1)


def is_admin():
    """
    Check if user is admin
    Returns: True if admin
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print str(e)
        return False


def install_dependencies(dependency):
    """
    Run install dependencies if admin. If not admin, re-run the script as admin.
    Args:
        dependency: dependency list
    """
    if is_admin():
        # Code of your program here
        pip_auto_install(dependency)
    else:
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, u"runas", unicode(sys.executable), unicode(__file__ + " " + dependency), None, 1)

    is_admin()


install_dependencies(str(sys.argv[1]))
