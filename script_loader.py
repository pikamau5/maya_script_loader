'''
Load database
load ui

import script_loader
import script_loader_ui
reload(script_loader_ui)
reload(script_loader)


TODO: make unique names for list objects (and put in dictionary)
TODO: make unique context menus for items depending on installed state etc
TODO: insert sentry
TODO: add Non Editable ? checkboxes
TODO: Add pip_test contents to installation def
    * require requirements.txt?
    * change install to copy FOLDER
    * update folder paths to db
    * figure out how to run "main" function..?
'''

from script_loader_ui import Ui_Form
import sqlite3 as lite
import imp
from PySide2 import QtWidgets, QtCore, QtGui
import os
import shutil
import pip
from distutils.dir_util import copy_tree
import imp
from distutils.version import LooseVersion

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
        self.sll = ScriptLoaderLogic() # load logic class

    def setup_ui(self):
        """
        PyQt window and function connection setup. inherits from the UI file.
        """
        form = self
        # get setupui method from generated pyqt file
        super(ScriptLoaderUI, self).setupUi(form)

        self.update_btn.clicked.connect(self.update_tree)  # connect update button
        self.treeWidget.itemClicked.connect(self.get_selected_item)  # get selected item
        self.treeWidget.itemDoubleClicked.connect(lambda: self.launch_script(self.get_selected_item()))  # run on double click

        # for right clicking tree widget items
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.contextMenuEvent)
        #self.treeWidget.items(0)

        form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)  # Window always on top

        # expand tree on start
        self.treeWidget.expandToDepth(0)
        self.update_tree()  # update tree on launch

    def create_brushes(self):
        # color brushes for text colors
        brushes = []
        brush_white = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush_white.setStyle(QtCore.Qt.NoBrush)
        brushes.append(brush_white)

        brush_gray = QtGui.QBrush(QtGui.QColor(99, 99, 99))
        brush_gray.setStyle(QtCore.Qt.NoBrush)
        brushes.append(brush_gray)

        return brushes

    def create_fonts(self):
        fonts = []
        font_bold = QtGui.QFont()
        font_bold.setBold(True)
        fonts.append(font_bold)

        font_normal = QtGui.QFont()
        font_normal.setBold(True)
        fonts.append(font_normal)

        return fonts

    def contextMenuEvent(self, event):
        """
        Context menu for treewidget items
        Args:
            event: context menu event
        """
        self.menu = QtWidgets.QMenu(self)
        installAction = QtWidgets.QAction("Install", self)
        installAction.triggered.connect(lambda: self.install_local(self.get_selected_item()))
        self.menu.addAction(installAction)
        UninstallAction = QtWidgets.QAction("Uninstall", self)
        UninstallAction.triggered.connect(lambda: self.uninstall_local())
        self.menu.addAction(UninstallAction)
        self.menu.popup(QtGui.QCursor.pos())

    def contextMenuEvent2(self, event):
        """
        Context menu for treewidget items
        Args:
            event: context menu event
        """
        UninstallAction = QtWidgets.QAction("Uninstall", self)
        UninstallAction.triggered.connect(lambda: self.uninstall_local())
        self.menu.addAction(UninstallAction)
        self.menu.popup(QtGui.QCursor.pos())

    def check_if_installed(self, selected_item):
        """
        checks if scripts in db are installed in current scripts folder
        """


    def get_maya_scripts_folder(self):
        maya_script_folder = os.path.dirname(os.path.realpath(__file__))
        maya_script_folder = maya_script_folder.replace("\\", "/")

        return maya_script_folder

    def copytree(src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    def install_local(self, selected_item):
        """
        Copy the script to the local maya scripts folder.
        """

        maya_script_folder = self.get_maya_scripts_folder()
        try:
            last_folder = str(selected_item).split("/")
            last_folder = last_folder[-1]
            copy_tree(selected_item, maya_script_folder + "/" + last_folder)
            # TODO change color to white
            self.treeWidget.selectedItems()[0].setForeground(0, self.create_brushes()[0])
            self.treeWidget.selectedItems()[0].setFont(0, self.create_fonts()[0])
            print "Installed " + last_folder + " success!"
        except:
            print "Failed to install " + last_folder

    def uninstall_local(self):
        print "Uninstalling"
        self.treeWidget.selectedItems()[0].setForeground(0, self.create_brushes()[1])
        self.treeWidget.selectedItems()[0].setFont(0, self.create_fonts()[1])

    def retranslateUi(self, Form):
        form = self
        super(ScriptLoaderUI, self).retranslateUi(form)


    def get_selected_item(self):
        """
        Get name of selected item
        Returns: the selected item
        """
        b = self.treeWidget.selectedItems()
        sel_item = b[0].data(0,32)
        return sel_item

    def compare_version(self, script_path):
        maya_folder = self.get_maya_scripts_folder()
        script_folder_name = str(script_path).split("/")
        final_folder = maya_folder + "/" + script_folder_name[-1]

        version_file_local = final_folder + "/_version.py"
        version_file_db = script_path + "/_version.py"
        print version_file_local
        print version_file_db

        try:
            foo = imp.load_source('module.name', version_file_local)
            bar = imp.load_source('module.name', version_file_db)

            local_version = str(foo.__version__)
            db_version = str(bar.__version__)

            print "Version for " + final_folder + " - db: " + db_version + " local: " + local_version
            if LooseVersion(db_version) > LooseVersion(local_version):
                print "script is outdated!"

        except:
            print "could not find version number in " + version_file_local






    def update_tree(self):
        """
        Update the treewidget list
        """
        self.treeWidget.clear()

        # get db here
        entries = self.sll.get_database()
        categories = self.sll.get_categories()

        # create root items for categories
        for category in categories:
            cat_item = QtWidgets.QTreeWidgetItem(self.treeWidget)
            cat_item.setText(0, category)

            # add entries to categories
            for entry in entries:
                for item in entry:
                        if item[4] == category:
                            script_item = QtWidgets.QTreeWidgetItem(cat_item)
                            script_item.setText(0, item[1])
                            script_item.setData(0,32, item[2])  # path
                            script_item.setData(0, 33, item[3])  # version
                            script_item.setForeground(0, self.create_brushes()[1])

                            # Check if file already exists
                            maya_script_folder = self.get_maya_scripts_folder()
                            split_string = str(item[2]).split("/")
                            script_name = split_string[-1]

                            target_folder = maya_script_folder + "/" + script_name
                            # if folder exists
                            if os.path.exists(target_folder):
                                # get versions
                                self.compare_version(item[2])
                                # update brushes
                                script_item.setForeground(0, self.create_brushes()[0])
                                script_item.setFont(0, self.create_fonts()[0])

        self.treeWidget.expandToDepth(0)

    def launch_script(self, script_path):
        """
        Launch script in maya
        Args:
            script_path: path to the script
        """
        maya_folder = self.get_maya_scripts_folder()
        script_folder_name = str(script_path).split("/")
        final_folder = maya_folder + "/" + script_folder_name[-1]
        print "Running init file in folder: " + final_folder
        imp.load_source('module.name', final_folder + "/__init__.py")


class ScriptLoaderLogic():

    con = lite.connect('C:/my_projects/script_loader/scripts.db')  # path to database

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

    def get_categories(self):
        """
        Get all the categories
        Returns: all the categories in an array
        """
        entries = self.get_database()
        categories = []
        for entry in entries:
            for item in entry:
                categories.append(item[4])  # get all categories
        categories = list(dict.fromkeys(categories))  # remove duplicates
        return categories


exportUi = ScriptLoaderUI()
exportUi.setup_ui()
exportUi.show()