'''
Script loader for maya -
Loads scripts using a database from a remote location and installs scripts w/ dependencies to local maya install.

By Laura K - laurakoekoek91@gmail.com - www.laurakart.fi

import script_loader
import script_loader_ui
import excepthook_override
reload(excepthook_override)
reload(script_loader_ui)
reload(script_loader)

TODO: add Non Editable ? checkboxes
TODO: Add pip_test contents to installation def
    * figure out how to run "main" function..?'

TODO: add user popups + log tab
TODO: make UI Dockable and Scalable
'''

import os
import shutil
import imp
import sys
import pkg_resources
import sqlite3
import zipfile
import glob
import re
from PySide2 import QtWidgets, QtCore, QtGui
from distutils.version import LooseVersion
from script_loader_ui import Ui_Form
import excepthook_override
import script_loader_config

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
        """
        Action by right clicking the tree menu item.
        """
        path = self.get_selected_path()
        script_item = self.check_if_script_item()
        maya_script_folder = self.get_maya_scripts_folder()
        # open the context menu
        self.contextMenuEvent(path, script_item, maya_script_folder)

    def double_click(self):
        """
        Action by double clicking the tree menu item.
        """
        maya_script_folder = self.get_maya_scripts_folder()
        b = self.treeWidget.selectedItems()
        name = b[0].data(0, 40)
        # launch the script.
        self.launch_script(maya_script_folder, name)

    def get_metadata(self):
        pass

    def update_tree(self):
        """
        Update the treewidget list
        db column info:
            0=ID
            1=name
            2=path
            3=category
        widget item data:
            32=path
            33=version
            34=True if outdated
            35=True if script item
            36 = version
            40 = name
        """
        self.treeWidget.clear()  # clear the tree
        db_entries = self.database.get_database()  # get the database
        maya_scripts_folder = self.get_maya_scripts_folder()  # get the maya scripts folder
        categories = self.database.get_categories(db_entries)  # get database categories
        whl_paths = self.database.get_folder_contents()  # get a list of the whl paths

        for category in categories:
            cat_item = QtWidgets.QTreeWidgetItem(self.treeWidget)  # create root items for categories
            cat_item.setText(0, category)
            cat_item.setData(0, 35, False)  # mark as not a script item
            for path, cat in whl_paths.items():  # for each whl path
                if cat == category:
                    script_item = QtWidgets.QTreeWidgetItem(cat_item)  # add path whl to list
                    archive = zipfile.ZipFile(path, 'r')  # open whl archive

                    # parse the path name to get METADATA file
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
                    script_item.setText(0, name + " - " + version)
                    # set additional data to tree item
                    script_item.setData(0, 32, path)  # path
                    script_item.setData(0, 33, cat)  # category
                    script_item.setData(0, 35, True)  # script item
                    script_item.setData(0, 36, version)  # version
                    script_item.setData(0,40, name)  # name
                    # check if current version is already installed ( if folder with dist_info exists )
                    installed = False
                    installed_version = ""
                    name_underscore = name.replace("-", "_")
                    for n in glob.glob(maya_scripts_folder + "/*"):
                        n = n.replace("\\", "/")
                        if n.endswith(".dist-info"):
                            last_folder = n.split("/")
                            if last_folder[-1].startswith(name_underscore):  #TODO check also if top level folder exists
                                installed = True
                                script_item.setFont(0, self.create_fonts()[0])  # set text to bold
                                script_item.setForeground(0,self.create_brushes()[2])  # set text color to green
                                with open(n + "/METADATA") as f:
                                    for x in f.readlines():
                                        if str(x).startswith("Version:"):
                                            installed_version = str(x).split(": ")[-1].rstrip("\n\r")

                    script_item.setData(0, 37, installed)  # mark whether it is installed
                    # check if version is oudated
                    outdated = False
                    if installed:
                        if LooseVersion(installed_version) < LooseVersion(version):
                            script_item.setData(0, 34, True)  # set outdated status to true
                            script_item.setForeground(0, self.create_brushes()[3])  # set text color yellow
                            script_item.setText(0, name + " - New version: " + version)
                            outdated = True

                    script_item.setData(0, 38, outdated)  # mark if installed
        self.treeWidget.expandToDepth(0)  # expand the tree

    def install_local(self, selected_path, maya_script_folder, selected_name):
        """
        Copy the script to the local maya scripts folder.
        Args:
            selected_path: the selected item in the treewidget menu
            maya_script_folder: path to local maya script folder
            selected_name: name of the selected item
        """
        print selected_path
        whl = str(selected_path).split(".")
        whl = whl[-1]
        print whl
        if whl == "whl":  # check if file is a whl
            print "Installing " + str(selected_name) + "..."
            archive = zipfile.ZipFile(selected_path)  # get whl archive
            for file in archive.namelist():
                archive.extract(file, maya_script_folder)  # get all files

        # find dependency list
        name_underscore = selected_name.replace("-", "_")
        dependencies = []
        for n in glob.glob(maya_script_folder + "/*"):
            n = n.replace("\\", "/")
            if n.endswith(".dist-info"):
                last_folder = n.split("/")
                if last_folder[-1].startswith(name_underscore):  # TODO do some additional checks
                    with open(n + "/METADATA") as f:  # TODO move metadata to its own function..
                        for x in f.readlines():
                            if str(x).startswith("Requires-Dist: "):
                                dependency = str(x).split(": ")[-1].rstrip("\n\r")
                                dependency = re.sub('[ ()]', '', dependency)
                                ignore_pkgs = ("PySide2", "maya", "setuptools")
                                if dependency != "setuptools" and dependency != "maya" and dependency != "PySide2":
                                    dependencies.append(dependency)

        try:  # try running dependencies
            for d in dependencies:
                pkg_resources.require(d)
                print "Dependencies " + str(d) + " OK."
        except Exception as e:  # install missing dependencies
            print "Some of these dependencies are not installed: " + str(d) + ". Installing.. " + str(e)
            # do some wonky stuff to get the correct path to python executable..
            maya_exe = sys.executable.split(".")[0] + "py.exe"
            maya_exe = maya_exe.replace("\\", "/")
            dependencies_script = "script_loader_install_dependencies.py"
            dependencies_string  = ""
            for d in dependencies:
                dependencies_string += d + " "
            # instal dependencies command
            command = "\"" + str(maya_exe) + "\" " + maya_script_folder + "/" + dependencies_script + " \""\
                      + dependencies_string + "\""
            os.system('"' + command + '"')
        self.update_tree()  # update the tree view

    def uninstall_local(self, maya_scripts_folder, name):
        """
        Delete folder where script is
        Args:
            maya_scripts_folder: path to maya scripts folder
            name: name of the selected item
        """
        # find the actual script folder from top_level.txt
        name_underscore = name.replace("-", "_")
        for n in glob.glob(maya_scripts_folder + "/*"):
            n = n.replace("\\", "/")
            if n.endswith(".dist-info"):
                last_folder = n.split("/")
                if last_folder[-1].startswith(name_underscore):  # TODO check also if top level folder exists
                    fo = open(n + "/top_level.txt")
                    with fo as f:
                        script_folder = f.readline().rstrip("\r\n")
                    fo.close()

                    shutil.rmtree(maya_scripts_folder + "/" + script_folder)  # remove the script folder
                    shutil.rmtree(n)  # remove the dist_info folder
        self.update_tree()   # update the tree view

    def contextMenuEvent(self, selected_path, is_script_item, maya_script_folder):
        """
        Context menu for treewidget items
        Args:
            selected_path: the path of the selected item
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
            run_action = QtWidgets.QAction("Run", self)
            run_action.triggered.connect(lambda: self.launch_script(maya_script_folder, name))
            self.menu.addAction(run_action)

        if installed and outdated:
            install_action = QtWidgets.QAction("Update", self)
            install_action.triggered.connect(lambda: self.update_local(selected_path, maya_script_folder, name))
            self.menu.addAction(install_action)

        if installed:
            uninstall_action = QtWidgets.QAction("Uninstall", self)
            uninstall_action.triggered.connect(lambda: self.uninstall_local(maya_script_folder, name))
            self.menu.addAction(uninstall_action)
        else:
            install_action = QtWidgets.QAction("Install", self)
            install_action.triggered.connect(lambda: self.install_local(selected_path, maya_script_folder, name))
            self.menu.addAction(install_action)
        self.menu.popup(QtGui.QCursor.pos())
        self.update_tree()

    def update_local(self, selected_path, maya_script_folder, name):
        self.uninstall_local(maya_script_folder, name)
        self.install_local(selected_path, maya_script_folder, name)
        self.update_tree()

    @staticmethod
    def get_maya_scripts_folder():
        """
        Get path of maya scripts folder
        Returns:path to maya scripts folder
        """
        maya_script_folder = os.path.dirname(os.path.realpath(__file__))
        maya_script_folder = maya_script_folder.replace("\\", "/")
        return maya_script_folder

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

    @staticmethod
    def launch_script(maya_scripts_folder, name):
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
        # yellow brush
        brush_green = QtGui.QBrush(QtGui.QColor(244, 166, 81))
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
        print message  # TODO add log tab & file

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
