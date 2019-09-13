'''
Load database
load ui

import script_loader
import script_loader_ui
reload(script_loader_ui)
reload(script_loader)


TODO: insert sentry
TODO: add Non Editable ? checkboxes
TODO: Add pip_test contents to installation def
    * figure out how to run "main" function..?

'''

import os, shutil, imp, sys, pkg_resources, sqlite3
from PySide2 import QtWidgets, QtCore, QtGui
from distutils.version import LooseVersion
from script_loader_ui import Ui_Form
import excepthook_override

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
        self.treeWidget.itemDoubleClicked.connect(lambda: self.launch_script(self.get_selected_item(), self.check_if_installed()))  # run on double click

        # for right clicking tree widget items
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(lambda: self.contextMenuEvent(self.check_if_installed(),
                                                                                         self.get_selected_update_status(),
                                                                                         self.check_if_selected_is_script_item()))

        form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)  # Window always on top

        # expand tree on start
        self.treeWidget.expandToDepth(0)
        self.update_tree()  # update tree on launch

    def create_brushes(self):
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
        # orange brush
        brush_orange = QtGui.QBrush(QtGui.QColor(255, 200, 94))
        brush_orange.setStyle(QtCore.Qt.NoBrush)
        brushes.append(brush_orange)

        return brushes

    def create_fonts(self):
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

    def contextMenuEvent(self, installed, outdated, is_script_item):
        """
        Context menu for treewidget items
        Args:
            installed: is script installed?
            outdated: is script outdated?
            is_script_item: is is a script item?
        """
        self.menu = QtWidgets.QMenu(self)
        if not is_script_item: # skip category items
            return
        if installed:
            RunAction = QtWidgets.QAction("Run", self)
            RunAction.triggered.connect(lambda: self.launch_script(self.get_selected_item(), self.check_if_installed()))
            self.menu.addAction(RunAction)
        if installed and outdated:
            installAction = QtWidgets.QAction("Update", self)
            installAction.triggered.connect(lambda: self.install_local(self.get_selected_item()))
            self.menu.addAction(installAction)
        if installed:
            UninstallAction = QtWidgets.QAction("Uninstall", self)
            UninstallAction.triggered.connect(lambda: self.uninstall_local(self.get_selected_item()))
            self.menu.addAction(UninstallAction)
        else:
            UninstallAction = QtWidgets.QAction("Install", self)
            UninstallAction.triggered.connect(lambda: self.install_local(self.get_selected_item()))
            self.menu.addAction(UninstallAction)
        self.menu.popup(QtGui.QCursor.pos())

    def check_if_installed(self):
        """
        checks if scripts in db are installed in current scripts folder
        Returns: True if installed
        """
        db_folder = self.get_selected_item()
        maya_script_folder = self.get_maya_scripts_folder()
        db_folder_split = str(db_folder).split("/")
        last_folder = db_folder_split[-1]

        target_folder = maya_script_folder + "/" + last_folder
        if os.path.exists(target_folder):
            return True
        else:
            return False

    def get_maya_scripts_folder(self):
        """
        Get path of maya scripts folder
        Returns:path to maya scripts folder
        """
        maya_script_folder = os.path.dirname(os.path.realpath(__file__))
        maya_script_folder = maya_script_folder.replace("\\", "/")
        return maya_script_folder

    def install_local(self, selected_item):
        """
        Copy the script to the local maya scripts folder.
        Args:
            selected_item: the selected item in the treewidget menu
        """

        maya_script_folder = self.get_maya_scripts_folder()
        last_folder = ""
        try:
            last_folder = str(selected_item).split("/")
            last_folder = last_folder[-1]
            new_folder = maya_script_folder + "/" + last_folder
            # copy the folder
            shutil.copytree(selected_item, new_folder)
            # change text color to be white
            self.treeWidget.selectedItems()[0].setForeground(0, self.create_brushes()[0])
            self.treeWidget.selectedItems()[0].setFont(0, self.create_fonts()[0])
            print "Installed " + last_folder + " success!"
            # check dependencies:
            requirements_file = new_folder + "/requirements.txt"
            if not os.path.isfile(requirements_file):  # check that file exists
                print "requirements.txt not found."
                return
            dependencies = [line.rstrip('\r\n') for line in open(new_folder + "/requirements.txt")]
            # Throw exception if dependencies are not met
            print "Dependencies: " + str(dependencies)
            try:
                pkg_resources.require(dependencies)
                print "Dependencies are OK."
            except:
                if not self.message_query("Missing dependencies", "Install the following dependencies?: " + str(dependencies)):
                    print "user canceled"
                    return
                # do some stuff to get the correct paths
                maya_exe = sys.executable
                maya_exe = maya_exe.split(".")
                maya_exe = maya_exe[0] + "py.exe"
                maya_exe = maya_exe.replace("\\","/")
                dependencies_script = "script_loader_install_dependencies.py"
                # install dependencies
                command = "\"" + str(maya_exe) + "\" " + maya_script_folder + "/" + dependencies_script + " \"" + new_folder + "\""
                os.system('"' + command + "& pause" + '"')
                print "Installed missing dependencies."

        except:
            print "Failed to install " + last_folder

    def uninstall_local(self, selected_item):
        """
        Delete folder where script is
        Args:
            selected_item: selected item in treewidget menu
        """
        maya_scripts_folder = self.get_maya_scripts_folder()
        last_folder = str(selected_item).split("/")
        last_folder = last_folder[-1]
        if len(last_folder) > 2:
            target_folder = maya_scripts_folder + "/" + last_folder
            print "Uninstalling " + target_folder
            shutil.rmtree(target_folder)
        self.treeWidget.selectedItems()[0].setForeground(0, self.create_brushes()[1])
        self.treeWidget.selectedItems()[0].setFont(0, self.create_fonts()[1])

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
        self.write_to_log(title + " | " + message + " | " + str(answer))
        return answer

    def get_selected_update_status(self):
        """
        Get name of selected item
        Returns: the selected item
        """
        b = self.treeWidget.selectedItems()
        sel_item = b[0].data(0,34)  # 34 = true if outdated
        return sel_item

    def check_if_selected_is_script_item(self):
        """
        Get name of selected item
        Returns: the selected item
        """
        b = self.treeWidget.selectedItems()
        sel_item = b[0].data(0,35)
        return sel_item

    def get_selected_item(self):
        """
        Get name of selected item
        Returns: the selected item
        """
        b = self.treeWidget.selectedItems()
        sel_item = b[0].data(0,32)
        return sel_item

    def check_version(self, script_path):
        """
        Compare versions of local and source script
        Args:
            script_path: path to local script
        Returns: True if outdated
        """
        version_outdated = False
        maya_folder = self.get_maya_scripts_folder()
        script_folder_name = str(script_path).split("/")
        final_folder = maya_folder + "/" + script_folder_name[-1]

        version_file_local = final_folder + "/_version.py"
        version_file_db = script_path + "/_version.py"

        try:
            foo = imp.load_source('module.name', version_file_local)
            local_version = str(foo.__version__)
            bar = imp.load_source('module.name', version_file_db)
            db_version = str(bar.__version__)

            if LooseVersion(db_version) > LooseVersion(local_version):
                print "script is outdated: "
                print "Version for " + final_folder + " - db: " + db_version + " local: " + local_version
                version_outdated = True
            else:
                version_outdated = False
        except Exception as e:
            print "could not find version number in " + version_file_local + " " + str(e)

        return version_outdated

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
            cat_item.setData(0, 35, False)  # script item
            # add entries to categories
            for entry in entries:
                for item in entry:
                        if item[3] == category:
                            script_item = QtWidgets.QTreeWidgetItem(cat_item)
                            script_item.setText(0, item[1] + " / " + str(item[3]))
                            script_item.setData(0,32, item[2])  # path
                            script_item.setData(0, 33, item[3])  # version
                            script_item.setData(0, 35, True)  # script item
                            script_item.setForeground(0, self.create_brushes()[1])

                            # Check if file already exists
                            maya_script_folder = self.get_maya_scripts_folder()
                            split_string = str(item[2]).split("/")
                            script_name = split_string[-1]

                            target_folder = maya_script_folder + "/" + script_name
                            # if folder exists
                            if os.path.exists(target_folder):
                                # get versions
                                if self.check_version(item[2]): # if version is outdated
                                    # set text color orange
                                    script_item.setForeground(0, self.create_brushes()[2])
                                    script_item.setData(0,34,True) # set true if outdated

                                else:
                                    # set text color white + bold
                                    script_item.setData(0, 34, False)
                                    script_item.setForeground(0, self.create_brushes()[0])
                                    script_item.setFont(0, self.create_fonts()[0])

        self.treeWidget.expandToDepth(0)

    def launch_script(self, script_path, installed):
        """
        Launch script in maya
        Args:
            script_path: path to the script
        """
        if not os.path.isdir(script_path) or not installed:
            print "not installed."
            return
        maya_folder = self.get_maya_scripts_folder()
        script_folder_name = str(script_path).split("/")
        final_folder = maya_folder + "/" + script_folder_name[-1]
        print "Running init file in folder: " + final_folder
        imp.load_source('module.name', final_folder + "/__init__.py")


class ScriptLoaderLogic():
    """
    Logic class for script loader TODO: move more stuff here
    """
    con = sqlite3.connect('C:/my_projects/script_loader/scripts.db')  # path to database

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
                categories.append(item[3])  # get all categories
        categories = list(dict.fromkeys(categories))  # remove duplicates
        return categories


exportUi = ScriptLoaderUI()
exportUi.setup_ui()
exportUi.show()
