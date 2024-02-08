# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'data_source_dialog.ui'
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

class Ui_DataSourceDialog(object):
    def setupUi(self, DataSourceDialog):
        if not DataSourceDialog.objectName():
            DataSourceDialog.setObjectName(u"DataSourceDialog")
        DataSourceDialog.resize(400, 236)
        self.verticalLayout = QVBoxLayout(DataSourceDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.xAxisLabel = QLabel(DataSourceDialog)
        self.xAxisLabel.setObjectName(u"xAxisLabel")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.xAxisLabel)

        self.x_box = QComboBox(DataSourceDialog)
        self.x_box.setObjectName(u"x_box")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.x_box)

        self.uncertaintyXLabel = QLabel(DataSourceDialog)
        self.uncertaintyXLabel.setObjectName(u"uncertaintyXLabel")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.uncertaintyXLabel)

        self.x_err_box = QComboBox(DataSourceDialog)
        self.x_err_box.setObjectName(u"x_err_box")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.x_err_box)

        self.yAxisLabel = QLabel(DataSourceDialog)
        self.yAxisLabel.setObjectName(u"yAxisLabel")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.yAxisLabel)

        self.y_box = QComboBox(DataSourceDialog)
        self.y_box.setObjectName(u"y_box")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.y_box)

        self.uncertaintyYLabel = QLabel(DataSourceDialog)
        self.uncertaintyYLabel.setObjectName(u"uncertaintyYLabel")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.uncertaintyYLabel)

        self.y_err_box = QComboBox(DataSourceDialog)
        self.y_err_box.setObjectName(u"y_err_box")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.y_err_box)

        self.dataSourceLabel = QLabel(DataSourceDialog)
        self.dataSourceLabel.setObjectName(u"dataSourceLabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.dataSourceLabel)

        self.data_source_box = QComboBox(DataSourceDialog)
        self.data_source_box.setObjectName(u"data_source_box")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.data_source_box)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(DataSourceDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.x_box, self.x_err_box)
        QWidget.setTabOrder(self.x_err_box, self.y_box)
        QWidget.setTabOrder(self.y_box, self.y_err_box)

        self.retranslateUi(DataSourceDialog)
        self.buttonBox.accepted.connect(DataSourceDialog.accept)
        self.buttonBox.rejected.connect(DataSourceDialog.reject)

        QMetaObject.connectSlotsByName(DataSourceDialog)
    # setupUi

    def retranslateUi(self, DataSourceDialog):
        DataSourceDialog.setWindowTitle(QCoreApplication.translate("DataSourceDialog", u"Dialog", None))
        self.xAxisLabel.setText(QCoreApplication.translate("DataSourceDialog", u"X-axis:", None))
        self.uncertaintyXLabel.setText(QCoreApplication.translate("DataSourceDialog", u"Uncertainty X:", None))
        self.yAxisLabel.setText(QCoreApplication.translate("DataSourceDialog", u"Y-axis:", None))
        self.uncertaintyYLabel.setText(QCoreApplication.translate("DataSourceDialog", u"Uncertainty Y:", None))
        self.dataSourceLabel.setText(QCoreApplication.translate("DataSourceDialog", u"Data Source:", None))
    # retranslateUi

