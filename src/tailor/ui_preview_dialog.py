# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preview_dialog.ui'
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
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_PreviewDialog(object):
    def setupUi(self, PreviewDialog):
        if not PreviewDialog.objectName():
            PreviewDialog.setObjectName(u"PreviewDialog")
        PreviewDialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(PreviewDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(PreviewDialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.buttonBox = QDialogButtonBox(PreviewDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(PreviewDialog)
        self.buttonBox.accepted.connect(PreviewDialog.accept)
        self.buttonBox.rejected.connect(PreviewDialog.reject)

        QMetaObject.connectSlotsByName(PreviewDialog)
    # setupUi

    def retranslateUi(self, PreviewDialog):
        PreviewDialog.setWindowTitle(QCoreApplication.translate("PreviewDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("PreviewDialog", u"TextLabel", None))
    # retranslateUi

