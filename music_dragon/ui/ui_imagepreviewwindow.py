# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './res/ui/imagepreviewwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ImagePreviewWindow(object):
    def setupUi(self, ImagePreviewWindow):
        ImagePreviewWindow.setObjectName("ImagePreviewWindow")
        ImagePreviewWindow.resize(237, 281)
        self.verticalLayout = QtWidgets.QVBoxLayout(ImagePreviewWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.image = QtWidgets.QLabel(ImagePreviewWindow)
        self.image.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.image.setText("")
        self.image.setPixmap(QtGui.QPixmap(":/images/questionmark.png"))
        self.image.setScaledContents(False)
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        self.image.setObjectName("image")
        self.verticalLayout.addWidget(self.image)
        self.saveButton = QtWidgets.QPushButton(ImagePreviewWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/download.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.saveButton.setIcon(icon)
        self.saveButton.setIconSize(QtCore.QSize(20, 20))
        self.saveButton.setObjectName("saveButton")
        self.verticalLayout.addWidget(self.saveButton)

        self.retranslateUi(ImagePreviewWindow)
        QtCore.QMetaObject.connectSlotsByName(ImagePreviewWindow)

    def retranslateUi(self, ImagePreviewWindow):
        _translate = QtCore.QCoreApplication.translate
        ImagePreviewWindow.setWindowTitle(_translate("ImagePreviewWindow", "Image Preview"))
        self.saveButton.setText(_translate("ImagePreviewWindow", "Save"))
from . import res_rc
