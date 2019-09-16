# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\lkoekoek\Documents\maya\2019\scripts\rsExportUi.ui',
# licensing of 'C:\Users\lkoekoek\Documents\maya\2019\scripts\rsExportUi.ui' applies.
#
# Created: Mon Sep  2 23:03:26 2019
#      by: pyside2-uic  running on PySide2 5.13.0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets


class Ui_Form(object):

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(332, 490)
        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setGeometry(QtCore.QRect(10, 10, 311, 471))
        self.tabWidget.setObjectName("tabWidget")
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.update_btn = QtWidgets.QPushButton(self.tab_1)
        self.update_btn.setGeometry(QtCore.QRect(10, 410, 291, 28))
        self.update_btn.setObjectName("pushButton_2")
        self.treeWidget = QtWidgets.QTreeWidget(self.tab_1)
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
        self.tabWidget.addTab(self.tab_1, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.plainTextEdit = QtWidgets.QLabel(self.tab_2)
        self.plainTextEdit.setGeometry(QtCore.QRect(10, 10, 291, 391))
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.plainTextEdit.setAlignment(QtCore.Qt.AlignTop)
        self.tabWidget.addTab(self.tab_2, "")

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), QtWidgets.QApplication.translate("Form", "Script loader", None,  -1))
        self.plainTextEdit.setText(QtWidgets.QApplication.translate("Form", "Script Loader\n"
                                                                         "\n"
                                                                         "Loads scripts with dependencies from network.\n"
                                                                         "\n"
                                                                         "By Laura K - www.laurakart.fi"
                                                                         , None,  -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtWidgets.QApplication.translate("Form", "Info", None, -1))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
