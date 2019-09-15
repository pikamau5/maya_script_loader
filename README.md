
SyntaxEditor Code Snippet

# Maya Script Loader
## (Work in progress)
Installs scripts to users maya install from a network drive.

![enter image description here](https://raw.githubusercontent.com/pikamau5/maya_script_loader/master/screenshot.png)

![enter image description here](https://raw.githubusercontent.com/pikamau5/maya_script_loader/master/Capture.PNG)



Features:

* Load list of whl packages from remote location using database
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