'''
Script loader for maya -
Loads scripts using a database from a remote location and installs scripts w/ dependencies to local maya install.

By Laura K - laurakoekoek91@gmail.com - www.laurakart.fi

import script_loader
import script_loader_ui
reload(script_loader_ui)
reload(script_loader)

TODO: insert sentry
TODO: add Non Editable ? checkboxes
TODO: Add pip_test contents to installation def
    * figure out how to run "main" function..?'

TODO: add user popups + log tab
TODO: make UI Dockable and Scalable
'''

import os, shutil, imp, sys, pkg_resources, sqlite3
from PySide2 import QtWidgets, QtCore, QtGui
from distutils.version import LooseVersion
from script_loader_ui import Ui_Form
import maya.cmds as cmds
import excepthook_override
import script_loader_config
import script_loader_install_whl
from zipfile import ZipFile
from pip._internal.utils.misc import get_installed_distributions
import zipfile
import glob
import re


# override exception hook
ex = excepthook_override.Except()
ex.run_excepthook(os.path.basename(__file__))


class ScriptLoaderUI(QtWidgets.QWidget, Ui_Form):
    """
    Run the script inside maya with a pyqt ui
    """
    def __init__(self):
        """
        init function
        """
        super(ScriptLoaderUI, self).__init__(None)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.database = Database() # load logic class
        self.my_selected_path = ""
        self.log = ""

    def setup_ui(self):
        """
        PyQt window and function connection setup. inherits from the UI file.
        """
        form = self
        # get setupui method from generated pyqt file
        super(ScriptLoaderUI, self).setupUi(form)

        self.update_btn.clicked.connect(self.update_tree)  # connect update button
        self.treeWidget.itemClicked.connect(self.get_selected_path)  # get selected item
        #  run on double click
        self.treeWidget.itemDoubleClicked.connect(self.double_click)

        # for right clicking tree widget items
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.right_click)

        form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)  # Window always on top

        # expand tree on start
        self.treeWidget.expandToDepth(0)
        self.update_tree()  # update tree on launch

    def right_click(self):

        path = self.get_selected_path()
        script_item = self.check_if_script_item()
        maya_script_folder = self.get_maya_scripts_folder()
        self.contextMenuEvent(path, script_item, maya_script_folder)

    def double_click(self):

        maya_script_folder = self.get_maya_scripts_folder()
        b = self.treeWidget.selectedItems() # TODO clean up stuff like this
        name = b[0].data(0, 40)

        self.launch_script(maya_script_folder, name)

    def update_tree(self):
        """
        Update the treewidget list
        db column info: 0=ID, 1=name, 2=path, 3=category
        widget item data: 32=path, 33=version, 34=True if outdated, 35=True if script item
        """
        self.treeWidget.clear()
        # get db here
        db_entries = self.database.get_database()
        # get maya scripts folder
        maya_scripts_folder = self.get_maya_scripts_folder()
        categories = self.database.get_categories(db_entries)
        whl_paths = self.database.get_folder_contents()

        for category in categories:
            # create root items for categories
            cat_item = QtWidgets.QTreeWidgetItem(self.treeWidget)
            cat_item.setText(0, category)
            cat_item.setData(0, 35, False)  # not a script item
            # add entries to categories

            for path, cat in whl_paths.items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
                if cat == category:
                    # add path whl to list
                    script_item = QtWidgets.QTreeWidgetItem(cat_item)
                    # Read whl metadata TODO put in its own function
                    archive = ZipFile(path, 'r')

                    # parse the path name
                    last_folder = str(path).split("/")
                    name = last_folder[-1].split("-")
                    dist_folder = name[0] + "-" + name[1] + ".dist-info"
                    metadata = archive.open(dist_folder + '/METADATA')
                    # get name and version from metadata
                    name = ""
                    version = ""
                    for x in metadata:
                        if str(x).startswith("Name:"):
                            name = str(x).split(": ")[-1].rstrip("\n\r")
                        if str(x).startswith("Version:"):
                            version = str(x).split(": ")[-1].rstrip("\n\r")
                    # print name
                    script_item.setText(0, name + " " + version)

                    # set additional data
                    script_item.setData(0, 32, path)  # path
                    script_item.setData(0, 33, cat)  # category
                    script_item.setData(0, 35, True)  # script item
                    script_item.setData(0, 36, version)  # version
                    script_item.setData(0,40, name)  # name

                    # check if module is already installed ( if folder with dist_info exists )
                    installed = False
                    installed_version = ""
                    name_underscore = name.replace("-", "_")
                    for n in glob.glob(maya_scripts_folder + "/*"):
                        n = n.replace("\\", "/")
                        if n.endswith(".dist-info"):
                            last_folder = n.split("/")
                            if last_folder[-1].startswith(name_underscore):  #TODO check also if top level folder exists
                                installed = True
                                script_item.setFont(0, self.create_fonts()[0])  # set to bold
                                script_item.setForeground(0,self.create_brushes()[2])
                                with open(n + "/METADATA") as f:
                                    for x in f.readlines():
                                        if str(x).startswith("Version:"):
                                            installed_version = str(x).split(": ")[-1].rstrip("\n\r")

                    script_item.setData(0, 37, installed)  # mark if installed

                    outdated = False
                    # check if version is oudated
                    if installed:
                        if LooseVersion(installed_version) < LooseVersion(version):
                            script_item.setData(0, 34, True)  # set outdated status to true
                            script_item.setForeground(0, self.create_brushes()[2])  # set text color green
                            script_item.setText(0, name + " - New version: " + version)
                            outdated = True

                    script_item.setData(0, 38, outdated)  # mark if installed
                    '''
                    installed_packages = get_installed_distributions()
                    for i in installed_packages:
                        if str(i).startswith(name):

                            script_item.setFont(0, self.create_fonts()[0])  # set to bold
                            if str(i) == name + " " + version:
                                    script_item.setData(0, 34, False)  # set outdated status to false
                                    script_item.setForeground(0, self.create_brushes()[0])  # set text color to white

                            else:
                                    script_item.setData(0, 34, True)  # set outdated status to true
                                    script_item.setForeground(0, self.create_brushes()[2])  # set text color green
                                    script_item.setText(0, name + " - New: " + version)
                    '''
        '''
            for db_row in db_entries:
                for db_column in db_row:
                        if db_column[3] == category:
                            script_item = QtWidgets.QTreeWidgetItem(cat_item)
                            # set tree item data
                            script_item.setData(0,32, db_column[2])  # path
                            script_item.setData(0, 33, db_column[3])  # category
                            script_item.setData(0, 35, True)  # script item
                            script_item.setForeground(0, self.create_brushes()[1])
                            # Check if file already exists
                            maya_script_folder = self.get_maya_scripts_folder()
                            split_string = str(db_column[2]).split("/")
                            script_name = split_string[-1]
                            target_folder = maya_script_folder + "/" + script_name

                            # get versions + text
                            # check for whl file
                            whl = str(db_column[2]).split(".")
                            if whl[-1] == "whl":
                                whl = str(db_column[2]).split("/")[-1].split("-")
                                name_whl = whl[0]
                                version_whl = whl[1]
                                script_item.setText(0, name_whl + " " + version_whl)
                            else:
                                # if not a whl file
                                version_local, version_db, version_outdated = self.get_version(db_column[2])
                                # Set item text
                                script_item.setText(0, db_column[1] + " " + version_db)
                            # if folder exists
                            if os.path.exists(target_folder):
                                if version_outdated:  # if version is outdated
                                    script_item.setData(0, 34, True)  # set outdated status to true
                                    script_item.setForeground(0, self.create_brushes()[2])  # set text color green
                                    script_item.setText(0, db_column[1] + " - New version available: " + version_db)
                                else:
                                    script_item.setData(0, 34, False)  # set outdated status to false
                                    # set text color white + bold
                                    script_item.setForeground(0, self.create_brushes()[0])
                                    script_item.setFont(0, self.create_fonts()[0])
        '''
        # expand the tree
        self.treeWidget.expandToDepth(0)

        #script_loader_install_whl.install_dependencies(selected_item)


    def install_local(self, selected_path, maya_script_folder, selected_name):
        """
        Copy the script to the local maya scripts folder.
        Args:
            selected_path: the selected item in the treewidget menu
            maya_script_folder: path to local maya script folder
        """
        print selected_path
        whl = str(selected_path).split(".")
        whl = whl[-1]
        print whl
        if whl == "whl":
            print "whl file, installing.."

            archive = zipfile.ZipFile(selected_path)
            for file in archive.namelist():
                archive.extract(file, maya_script_folder)
            self.update_tree()

        # check dependencies
        name_underscore = selected_name.replace("-", "_")

        dependencies = []
        for n in glob.glob(maya_script_folder + "/*"):
            n = n.replace("\\", "/")
            if n.endswith(".dist-info"):
                last_folder = n.split("/")
                if last_folder[-1].startswith(name_underscore):  # TODO check also if top level folder exists
                    with open(n + "/METADATA") as f:
                        for x in f.readlines():
                            if str(x).startswith("Requires-Dist: "):
                                dependency = str(x).split(": ")[-1].rstrip("\n\r")
                                dependency = re.sub('[ ()]', '', dependency)
                                dependencies.append(dependency)

        # INSTALL DEPENDENCY
        try:
            for d in dependencies:
                print "DEPENDENCIES"
                print d
                pkg_resources.require(d)
        except:
            print "failed dependencies test. installing dependencies.."
            # do some wonky stuff to get the correct path to python executable..
            maya_exe = sys.executable.split(".")[0] + "py.exe"
            maya_exe = maya_exe.replace("\\", "/")
            dependencies_script = "script_loader_install_dependencies.py"
            # install dependencies
            dependencies_string  = ""
            for d in dependencies:
                dependencies_string += d + " "
            command = "\"" + str(
                maya_exe) + "\" " + maya_script_folder + "/" + dependencies_script + " \"" + dependencies_string + "\""
            os.system('"' + command + '"')


        '''
        # check dependencies:
        requirements_file = new_folder + "/requirements.txt"
        if not os.path.isfile(requirements_file):  # check that file exists
            self.log_message("requirements.txt not found.")
            return
        dependencies = [line.rstrip('\r\n') for line in open(new_folder + "/requirements.txt")]
        # Throw exception if dependencies are not met
        self.log_message("Dependencies: " + str(dependencies))
        try:
            pkg_resources.require(dependencies)
            self.log_message("Dependencies are OK.")
        except:
            dependencies_str = ""
            for d in dependencies:
                dependencies_str += d + ", "
            # notify user
            self.popup_message("Additional libraries needed", "The following libraries will be installed: \n"
                               + dependencies_str)
            # do some wonky stuff to get the correct path to python executable..
            maya_exe = sys.executable.split(".")[0] + "py.exe"
            maya_exe = maya_exe.replace("\\", "/")
            dependencies_script = "script_loader_install_dependencies.py"
            # install dependencies
            command = "\"" + str(
                maya_exe) + "\" " + maya_script_folder + "/" + dependencies_script + " \"" + new_folder + "\""
            os.system('"' + command + '"')
            try:
                pkg_resources.require(dependencies)
                self.log_message("Installed missing dependencies.")
            except:
                self.log_message("Couldn't install dependencies! uninstalling..")
                self.uninstall_local(selected_path)
            '''
        '''
        last_folder = ""
        try:
            last_folder = str(selected_path).split("/")
            last_folder = last_folder[-1]
            new_folder = maya_script_folder + "/" + last_folder
            # copy the folder
            shutil.copytree(selected_path, new_folder)
            # change text color to be white
            self.treeWidget.selectedItems()[0].setForeground(0, self.create_brushes()[0])
            self.treeWidget.selectedItems()[0].setFont(0, self.create_fonts()[0])
            self.log_message("Installed " + last_folder + " success!")
            
            
            

        except Exception as e:
            self.log_message("Failed to install " + last_folder + ", " + str(e))
        '''

    def uninstall_local(self, selected_item):
        """
        Delete folder where script is
        Args:
            selected_item: selected item in treewidget menu
        """
        b = self.treeWidget.selectedItems()
        name = b[0].data(0,40)
        maya_scripts_folder = self.get_maya_scripts_folder()

        name_underscore = name.replace("-", "_")
        script_folder = ""
        for n in glob.glob(maya_scripts_folder + "/*"):
            n = n.replace("\\", "/")
            if n.endswith(".dist-info"):
                last_folder = n.split("/")
                if last_folder[-1].startswith(name_underscore):  # TODO check also if top level folder exists
                    fo = open(n + "/top_level.txt")
                    with fo as f:
                        script_folder = f.readline().rstrip("\r\n")
                    fo.close()

                    shutil.rmtree(maya_scripts_folder + "/" + script_folder)
                    shutil.rmtree(n)

        self.update_tree()


        '''
        
        last_folder = str(selected_item).split("/")
        last_folder = last_folder[-1]
        if len(last_folder) > 2:
            target_folder = maya_scripts_folder + "/" + last_folder
            self.log_message("Uninstalling " + target_folder)
            shutil.rmtree(target_folder)
        self.treeWidget.selectedItems()[0].setForeground(0, self.create_brushes()[1])
        self.treeWidget.selectedItems()[0].setFont(0, self.create_fonts()[1])
        '''

    def contextMenuEvent(self, selected_path, is_script_item, maya_script_folder):
        """
        Context menu for treewidget items
        Args:
            installed: is script installed?
            outdated: is script outdated?
            is_script_item: is is a script item?
            maya_script_folder: path to local maya script folder
        """
        b = self.treeWidget.selectedItems()
        installed = b[0].data(0, 37)
        outdated = b[0].data(0, 38)
        name = b[0].data(0,40)

        self.menu = QtWidgets.QMenu(self)
        if not is_script_item: # skip category items
            return
        if installed:
            RunAction = QtWidgets.QAction("Run", self)
            RunAction.triggered.connect(lambda: self.launch_script(maya_script_folder, name))
            self.menu.addAction(RunAction)
        if installed and outdated:
            installAction = QtWidgets.QAction("Update", self)
            installAction.triggered.connect(lambda: self.update_local(selected_path, maya_script_folder, name))
            self.menu.addAction(installAction)
        if installed:
            UninstallAction = QtWidgets.QAction("Uninstall", self)
            UninstallAction.triggered.connect(lambda: self.uninstall_local(selected_path))
            self.menu.addAction(UninstallAction)
        else:
            UninstallAction = QtWidgets.QAction("Install", self)
            UninstallAction.triggered.connect(lambda: self.install_local(selected_path, maya_script_folder, name))
            self.menu.addAction(UninstallAction)
        self.menu.popup(QtGui.QCursor.pos())

    def update_local(self, selected_path, maya_script_folder, name):
        self.uninstall_local(selected_path)
        self.install_local(selected_path, maya_script_folder, name)
        self.update_tree()

    def check_if_installed(self):
        """
        checks if scripts in db are installed in current scripts folder
        Returns: True if installed
        """
        db_folder = self.get_selected_path()
        maya_script_folder = self.get_maya_scripts_folder()
        db_folder_split = str(db_folder).split("/")
        last_folder = db_folder_split[-1]

        target_folder = maya_script_folder + "/" + last_folder
        if os.path.exists(target_folder):
            return True
        else:
            return False

    @staticmethod
    def get_maya_scripts_folder():
        """
        Get path of maya scripts folder
        Returns:path to maya scripts folder
        """
        maya_script_folder = os.path.dirname(os.path.realpath(__file__))
        maya_script_folder = maya_script_folder.replace("\\", "/")
        return maya_script_folder

    def get_update_status(self):
        """
        Get status of current item (true if outdated)
        Returns: True if outdated
        """
        selected_items = self.treeWidget.selectedItems()
        selected_item = selected_items[0].data(0,34)  # 34 = true if outdated
        return selected_item

    def check_if_script_item(self):
        """
        Check if list item is a script item and not a category
        Returns: True if script item
        """
        b = self.treeWidget.selectedItems()
        sel_item = b[0].data(0,35) # true if script item (not a category)
        return sel_item

    def get_selected_path(self):
        """
        Get name of selected item
        Returns: the selected item
        """
        b = self.treeWidget.selectedItems()
        sel_path = b[0].data(0,32)
        self.my_selected_path = sel_path
        return sel_path

    def get_version(self, script_path):
        """
        Compare versions of local and source script
        Args:
            script_path: path to local script
        Returns: True if outdated
        """
        whl = str(script_path).split(".")
        if whl[-1] == "whl":
            return
        version_outdated = False
        maya_folder = self.get_maya_scripts_folder()
        script_folder_name = str(script_path).split("/")
        final_folder = maya_folder + "/" + script_folder_name[-1]
        # append version file path
        version_file_local = final_folder + "/_version.py"
        version_file_db = script_path + "/_version.py"

        bar = imp.load_source('module.name', version_file_db)
        db_version = str(bar.__version__)
        local_version = ""
        try:
            foo = imp.load_source('module.name', version_file_local)
            local_version = str(foo.__version__)
            if LooseVersion(db_version) > LooseVersion(local_version):
                self.log_message("The following script is outdated:  " + final_folder + " - db: " + db_version + " local: " + local_version)
                version_outdated = True
        except Exception as e:
            self.log_message("could not find version number in " + version_file_local + " " + str(e))

        return local_version, db_version, version_outdated

    def launch_script(self, maya_scripts_folder, name):
        """
        Get top_level.txt - run __init__.py file in folder that is specified
        Args:
            maya_scripts_folder: path to maya scripts folder
            name: name of the script
        """
        name_underscore = name.replace("-", "_")
        for n in glob.glob(maya_scripts_folder + "/*"):
            n = n.replace("\\", "/")
            if n.endswith(".dist-info"):
                last_folder = n.split("/")
                if last_folder[-1].startswith(name_underscore):  # TODO check also if top level folder exists
                    with open(n + "/top_level.txt") as f:
                        x = f.readline().rstrip("\r\n")
                        print x
                        imp.load_source('module.name', maya_scripts_folder + "/" + x + "/__init__.py")

    @staticmethod
    def create_brushes():
        """
        Create color brushes for text fields
        Returns: brushes as an array
        """
        # white brush
        brushes = []
        brush_white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush_white.setStyle(QtCore.Qt.NoBrush)
        brushes.append(brush_white)
        # gray brush
        brush_gray = QtGui.QBrush(QtGui.QColor(128, 128, 128))
        brush_gray.setStyle(QtCore.Qt.NoBrush)
        brushes.append(brush_gray)
        # green brush
        brush_green = QtGui.QBrush(QtGui.QColor(156, 255, 39))
        brush_green.setStyle(QtCore.Qt.NoBrush)
        brushes.append(brush_green)

        return brushes

    @staticmethod
    def create_fonts():
        """
        bold/normal font
        Returns: fonts as an array
        """
        # bold font
        fonts = []
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        fonts.append(font_bold)
        # regular font
        font_normal = QtGui.QFont()
        font_normal.setBold(True)
        fonts.append(font_normal)

        return fonts

    @staticmethod
    def log_message(message):
        """
        Print log message to console, log textbox and file
        Args:
            message: log message
        """
        print message
        # TODO add log tab & file

    def popup_message(self, title, message):
        """
        A popup message
        Args:
            title: Title of the popup message
            message: Body of the popup message
        """
        QtWidgets.QMessageBox.information(self, title, message)
        self.log_message(title + ", " + message)

    def message_query(self, title, message):
        """
        Popup to ask user input
        Args:
            title: Title of the popup
            message: Message of the popup
        Returns: True / False for the user's answer
        """
        result = QtWidgets.QMessageBox.question(self, title, message,
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            answer = True
        else:
            answer = False
        self.log_message(title + ", " + message + ", " + str(answer))
        return answer


class Database():
    """
    Logic class for script loader TODO: move more stuff here
    """
    con = sqlite3.connect(script_loader_config.database_path)  # path to database

    def get_database(self):
        """
        Get all tables
        Returns: all tables as arrays
        """
        with self.con:
            cur = self.con.cursor()
            cur.execute("SELECT name from sqlite_master where type= \"table\"")
            rows = cur.fetchall()
            all_tables = []
            for row in rows:
                cur.execute("SELECT * FROM " + row[0])
                all_tables.append(cur.fetchall())
            return all_tables

    def get_folder_contents(self):
        """
        Gets the whl files from the database folder paths
        Returns: whl paths
        """
        whl_files = {}
        db = self.get_database()
        for table in db:
            for row in table:
                category = row[3]
                path = row[2]

                files = []
                # r=root, d=directories, f = files
                for r, d, f in os.walk(path):
                    for file in f:
                        if '.whl' in file:
                            whl_files.update({path + "/" + file: category}) # TODO this will break if there are other files?
        return whl_files


    @staticmethod
    def get_categories(db_table_array):
        """
        Get all the categories
        Returns: all the categories in an array
        """
        categories = []
        for entry in db_table_array:
            for item in entry:
                categories.append(item[3])  # get all categories
        categories = list(dict.fromkeys(categories))  # remove duplicates
        return categories


exportUi = ScriptLoaderUI()
exportUi.setup_ui()
exportUi.show()
