# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'rename_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.5.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QLineEdit, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_RenameDialog(object):
    def setupUi(self, RenameDialog):
        if not RenameDialog.objectName():
            RenameDialog.setObjectName(u"RenameDialog")
        RenameDialog.resize(400, 87)
        self.verticalLayout = QVBoxLayout(RenameDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.dataSourceLabel = QLabel(RenameDialog)
        self.dataSourceLabel.setObjectName(u"dataSourceLabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.dataSourceLabel)

        self.name_box = QLineEdit(RenameDialog)
        self.name_box.setObjectName(u"name_box")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.name_box)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(RenameDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(RenameDialog)
        self.buttonBox.accepted.connect(RenameDialog.accept)
        self.buttonBox.rejected.connect(RenameDialog.reject)

        QMetaObject.connectSlotsByName(RenameDialog)
    # setupUi

    def retranslateUi(self, RenameDialog):
        RenameDialog.setWindowTitle(QCoreApplication.translate("RenameDialog", u"Dialog", None))
        self.dataSourceLabel.setText(QCoreApplication.translate("RenameDialog", u"Name:", None))
    # retranslateUi

