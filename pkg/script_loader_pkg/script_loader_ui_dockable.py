from PySide2 import QtCore, QtWidgets
from PySide2 import QtGui

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import script_loader as script_loader

class MainWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)\

        # Main widget
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()

        self.update_btn = QtWidgets.QPushButton(main_widget)
        self.update_btn.setGeometry(QtCore.QRect(10, 410, 291, 28))
        self.update_btn.setObjectName("pushButton_2")
        self.treeWidget = QtWidgets.QTreeWidget(main_widget)
        self.treeWidget.setGeometry(QtCore.QRect(10, 10, 291, 391))
        self.treeWidget.setRootIsDecorated(True)
        self.treeWidget.setUniformRowHeights(False)
        self.treeWidget.setItemsExpandable(True)
        self.treeWidget.setAnimated(False)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setObjectName("treeWidget")
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        brush = QtGui.QBrush(QtGui.QColor(0, 255, 8))
        brush.setStyle(QtCore.Qt.NoBrush)
        item_1.setForeground(0, brush)
        item_1.setFlags(
            QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsTristate)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        # end of copy from old ui file

        main_layout.addWidget(self.treeWidget)
        main_layout.addWidget(self.update_btn)


        # Set main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.retranslateUi(main_widget)
        QtCore.QMetaObject.connectSlotsByName(main_widget)

        self.update_btn.clicked.connect(self.hello)  # self.update_tree)  # connect update button

    def hello(self):
        ui = script_loader.ScriptLoaderUI()
        ui.update_tree()

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Script Loader", None, -1))
        self.update_btn.setText(QtWidgets.QApplication.translate("Form", "Reload database", None, -1))
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.headerItem().setText(0, QtWidgets.QApplication.translate("Form", "Tools", None,  -1))
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.topLevelItem(0).setText(0, QtWidgets.QApplication.translate("Form", "Misc", None, -1))
        self.treeWidget.topLevelItem(0).child(0).setText(0, QtWidgets.QApplication.translate("Form", "Hello World", None,  -1))
        self.treeWidget.setSortingEnabled(__sortingEnabled)


    def on_test_btn_click(self):
        print 'Test button was clicked'

def main():
    w = MainWindow()
    w.show(dockable=True, floating=False, area='left')