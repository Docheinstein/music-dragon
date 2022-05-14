# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './res/ui/preferenceswindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PreferencesWindow(object):
    def setupUi(self, PreferencesWindow):
        PreferencesWindow.setObjectName("PreferencesWindow")
        PreferencesWindow.resize(445, 351)
        self.verticalLayout = QtWidgets.QVBoxLayout(PreferencesWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(PreferencesWindow)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.scrollArea = QtWidgets.QScrollArea(self.tab)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 409, 242))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.downloadDirectoryWidget = ClickableWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.downloadDirectoryWidget.sizePolicy().hasHeightForWidth())
        self.downloadDirectoryWidget.setSizePolicy(sizePolicy)
        self.downloadDirectoryWidget.setMinimumSize(QtCore.QSize(0, 60))
        self.downloadDirectoryWidget.setMaximumSize(QtCore.QSize(16777215, 60))
        self.downloadDirectoryWidget.setObjectName("downloadDirectoryWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.downloadDirectoryWidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtWidgets.QLabel(self.downloadDirectoryWidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.downloadDirectory = QtWidgets.QLabel(self.downloadDirectoryWidget)
        self.downloadDirectory.setObjectName("downloadDirectory")
        self.verticalLayout_3.addWidget(self.downloadDirectory)
        self.verticalLayout_4.addWidget(self.downloadDirectoryWidget)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
        self.tabWidget.addTab(self.tab, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(PreferencesWindow)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(PreferencesWindow)
        self.tabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(PreferencesWindow.accept) # type: ignore
        self.buttonBox.rejected.connect(PreferencesWindow.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(PreferencesWindow)

    def retranslateUi(self, PreferencesWindow):
        _translate = QtCore.QCoreApplication.translate
        PreferencesWindow.setWindowTitle(_translate("PreferencesWindow", "Dialog"))
        self.label.setText(_translate("PreferencesWindow", "Download Directory"))
        self.downloadDirectory.setText(_translate("PreferencesWindow", "~/MusicDragon"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("PreferencesWindow", "Output"))
from clickablewidget import ClickableWidget
