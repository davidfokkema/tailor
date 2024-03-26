# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'create_plot_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_CreatePlotDialog(object):
    def setupUi(self, CreatePlotDialog):
        if not CreatePlotDialog.objectName():
            CreatePlotDialog.setObjectName(u"CreatePlotDialog")
        CreatePlotDialog.resize(400, 236)
        self.verticalLayout = QVBoxLayout(CreatePlotDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.xAxisLabel = QLabel(CreatePlotDialog)
        self.xAxisLabel.setObjectName(u"xAxisLabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.xAxisLabel)

        self.x_axis_box = QComboBox(CreatePlotDialog)
        self.x_axis_box.setObjectName(u"x_axis_box")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.x_axis_box)

        self.uncertaintyXLabel = QLabel(CreatePlotDialog)
        self.uncertaintyXLabel.setObjectName(u"uncertaintyXLabel")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.uncertaintyXLabel)

        self.x_err_box = QComboBox(CreatePlotDialog)
        self.x_err_box.setObjectName(u"x_err_box")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.x_err_box)

        self.yAxisLabel = QLabel(CreatePlotDialog)
        self.yAxisLabel.setObjectName(u"yAxisLabel")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.yAxisLabel)

        self.y_axis_box = QComboBox(CreatePlotDialog)
        self.y_axis_box.setObjectName(u"y_axis_box")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.y_axis_box)

        self.uncertaintyYLabel = QLabel(CreatePlotDialog)
        self.uncertaintyYLabel.setObjectName(u"uncertaintyYLabel")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.uncertaintyYLabel)

        self.y_err_box = QComboBox(CreatePlotDialog)
        self.y_err_box.setObjectName(u"y_err_box")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.y_err_box)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(CreatePlotDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.x_axis_box, self.x_err_box)
        QWidget.setTabOrder(self.x_err_box, self.y_axis_box)
        QWidget.setTabOrder(self.y_axis_box, self.y_err_box)

        self.retranslateUi(CreatePlotDialog)
        self.buttonBox.accepted.connect(CreatePlotDialog.accept)
        self.buttonBox.rejected.connect(CreatePlotDialog.reject)

        QMetaObject.connectSlotsByName(CreatePlotDialog)
    # setupUi

    def retranslateUi(self, CreatePlotDialog):
        CreatePlotDialog.setWindowTitle(QCoreApplication.translate("CreatePlotDialog", u"Dialog", None))
        self.xAxisLabel.setText(QCoreApplication.translate("CreatePlotDialog", u"X-axis:", None))
        self.uncertaintyXLabel.setText(QCoreApplication.translate("CreatePlotDialog", u"Uncertainty X:", None))
        self.yAxisLabel.setText(QCoreApplication.translate("CreatePlotDialog", u"Y-axis:", None))
        self.uncertaintyYLabel.setText(QCoreApplication.translate("CreatePlotDialog", u"Uncertainty Y:", None))
    # retranslateUi

