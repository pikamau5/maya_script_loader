# Maya Script Loader
## (Work in progress)
Installs scripts to user's local Maya scripts folder from a network drive.

![enter image description here](https://raw.githubusercontent.com/pikamau5/maya_script_loader/master/screenshot.png)

![enter image description here](https://raw.githubusercontent.com/pikamau5/maya_script_loader/master/Capture.PNG)



Features:

* Load list of whl packages from a remote location. A database defines the project folder locations and categories.
* Install the package
	* Extract whl to Maya scripts folder
	* Install dependencies if needed
* Uninstall
* Run
* Check if the script is up to date

Requirements for whl:
* setup.py must have following fields:
	* name
	* version
	* install_requires
* check example_package_src folder for examples

How to use:

* Copy the script_loader_pkg (in pkg folder) to maya scripts folder.
* Run with command:

import script_loader_pkg
reload(script_loader_pkg)

* the installed scripts will be copied into this folder.

* Set the correct path to the database in script_loader_config.py

Requirements:

* Pip asdasd