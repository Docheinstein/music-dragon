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
        PreferencesWindow.resize(474, 642)
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
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 438, 533))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setSpacing(12)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.directoryWidget = ClickableWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.directoryWidget.sizePolicy().hasHeightForWidth())
        self.directoryWidget.setSizePolicy(sizePolicy)
        self.directoryWidget.setMinimumSize(QtCore.QSize(0, 60))
        self.directoryWidget.setMaximumSize(QtCore.QSize(16777215, 60))
        self.directoryWidget.setObjectName("directoryWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.directoryWidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtWidgets.QLabel(self.directoryWidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.directory = QtWidgets.QLabel(self.directoryWidget)
        self.directory.setObjectName("directory")
        self.verticalLayout_3.addWidget(self.directory)
        self.verticalLayout_4.addWidget(self.directoryWidget)
        self.widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.widget.setObjectName("widget")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_2 = QtWidgets.QLabel(self.widget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_5.addWidget(self.label_2)
        self.coverSize = QtWidgets.QComboBox(self.widget)
        self.coverSize.setObjectName("coverSize")
        self.coverSize.addItem("")
        self.coverSize.addItem("")
        self.coverSize.addItem("")
        self.coverSize.addItem("")
        self.verticalLayout_5.addWidget(self.coverSize)
        self.verticalLayout_4.addWidget(self.widget)
        self.widget_2 = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.widget_2.setObjectName("widget_2")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.widget_2)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_3 = QtWidgets.QLabel(self.widget_2)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_6.addWidget(self.label_3)
        self.outputFormat = QtWidgets.QLineEdit(self.widget_2)
        self.outputFormat.setObjectName("outputFormat")
        self.verticalLayout_6.addWidget(self.outputFormat)
        self.label_4 = QtWidgets.QLabel(self.widget_2)
        self.label_4.setWordWrap(True)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_6.addWidget(self.label_4)
        self.verticalLayout_4.addWidget(self.widget_2)
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
        PreferencesWindow.setWindowTitle(_translate("PreferencesWindow", "Preferences"))
        self.label.setText(_translate("PreferencesWindow", "Directory"))
        self.directory.setText(_translate("PreferencesWindow", "~/MusicDragon"))
        self.label_2.setText(_translate("PreferencesWindow", "Cover size"))
        self.coverSize.setItemText(0, _translate("PreferencesWindow", "Small (250)"))
        self.coverSize.setItemText(1, _translate("PreferencesWindow", "Medium (500)"))
        self.coverSize.setItemText(2, _translate("PreferencesWindow", "Large (1200)"))
        self.coverSize.setItemText(3, _translate("PreferencesWindow", "Largest"))
        self.label_3.setText(_translate("PreferencesWindow", "Output format"))
        self.label_4.setText(_translate("PreferencesWindow", "<html><head/><body><p><span style=\" font-size:10pt;\">{artist}: </span><span style=\" font-size:10pt; font-style:italic;\">artist name</span><span style=\" font-size:10pt;\"><br/>{album}: </span><span style=\" font-size:10pt; font-style:italic;\">album title</span><span style=\" font-size:10pt;\"><br/>{song}: </span><span style=\" font-size:10pt; font-style:italic;\">song name</span><span style=\" font-size:10pt;\"><br/>{ext}: </span><span style=\" font-size:10pt; font-style:italic;\">extension</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("PreferencesWindow", "General"))
from clickablewidget import ClickableWidget
