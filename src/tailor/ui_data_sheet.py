# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'data_sheet.ui'
##
## Created by: Qt User Interface Compiler version 6.3.2
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QTableView, QVBoxLayout, QWidget)

class Ui_DataSheet(object):
    def setupUi(self, DataSheet):
        if not DataSheet.objectName():
            DataSheet.setObjectName(u"DataSheet")
        DataSheet.resize(1027, 646)
        self.horizontalLayout = QHBoxLayout(DataSheet)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.data_view = QTableView(DataSheet)
        self.data_view.setObjectName(u"data_view")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.data_view.sizePolicy().hasHeightForWidth())
        self.data_view.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.data_view)

        self.groupBox = QGroupBox(DataSheet)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setContentsMargins(4, 4, 4, 4)
        self.nameLabel = QLabel(self.groupBox)
        self.nameLabel.setObjectName(u"nameLabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.nameLabel)

        self.name_edit = QLineEdit(self.groupBox)
        self.name_edit.setObjectName(u"name_edit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.name_edit)

        self.formulaLabel = QLabel(self.groupBox)
        self.formulaLabel.setObjectName(u"formulaLabel")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.formulaLabel)

        self.formula_edit = QLineEdit(self.groupBox)
        self.formula_edit.setObjectName(u"formula_edit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.formula_edit)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.add_column_button = QPushButton(self.groupBox)
        self.add_column_button.setObjectName(u"add_column_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.add_column_button.sizePolicy().hasHeightForWidth())
        self.add_column_button.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.add_column_button)

        self.add_calculated_column_button = QPushButton(self.groupBox)
        self.add_calculated_column_button.setObjectName(u"add_calculated_column_button")

        self.horizontalLayout_2.addWidget(self.add_calculated_column_button)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.create_plot_button = QPushButton(self.groupBox)
        self.create_plot_button.setObjectName(u"create_plot_button")

        self.verticalLayout.addWidget(self.create_plot_button)

        self.verticalLayout.setStretch(0, 1)

        self.horizontalLayout.addWidget(self.groupBox)


        self.retranslateUi(DataSheet)

        QMetaObject.connectSlotsByName(DataSheet)
    # setupUi

    def retranslateUi(self, DataSheet):
        DataSheet.setWindowTitle(QCoreApplication.translate("DataSheet", u"Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("DataSheet", u"Column information", None))
        self.nameLabel.setText(QCoreApplication.translate("DataSheet", u"Name:", None))
        self.formulaLabel.setText(QCoreApplication.translate("DataSheet", u"Formula", None))
        self.add_column_button.setText(QCoreApplication.translate("DataSheet", u"Add column", None))
        self.add_calculated_column_button.setText(QCoreApplication.translate("DataSheet", u"Add calculated column", None))
        self.create_plot_button.setText(QCoreApplication.translate("DataSheet", u"Create plot", None))
    # retranslateUi

