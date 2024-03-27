# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plot_tab.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from pyqtgraph import (PlotWidget, SpinBox)

class Ui_PlotTab(object):
    def setupUi(self, PlotTab):
        if not PlotTab.objectName():
            PlotTab.setObjectName(u"PlotTab")
        PlotTab.resize(1000, 600)
        self.horizontalLayout = QHBoxLayout(PlotTab)
#ifndef Q_OS_MAC
        self.horizontalLayout.setSpacing(-1)
#endif
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_5 = QVBoxLayout()
#ifndef Q_OS_MAC
        self.verticalLayout_5.setSpacing(-1)
#endif
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.plot_widget = PlotWidget(PlotTab)
        self.plot_widget.setObjectName(u"plot_widget")

        self.verticalLayout_5.addWidget(self.plot_widget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.groupBox_2 = QGroupBox(PlotTab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(4, 4, 4, 4)
        self.x_max = QLineEdit(self.groupBox_2)
        self.x_max.setObjectName(u"x_max")
        self.x_max.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.x_max, 0, 5, 1, 1)

        self.ylabel = QLineEdit(self.groupBox_2)
        self.ylabel.setObjectName(u"ylabel")

        self.gridLayout.addWidget(self.ylabel, 1, 1, 1, 1)

        self.xlabel = QLineEdit(self.groupBox_2)
        self.xlabel.setObjectName(u"xlabel")

        self.gridLayout.addWidget(self.xlabel, 0, 1, 1, 1)

        self.x_min = QLineEdit(self.groupBox_2)
        self.x_min.setObjectName(u"x_min")
        self.x_min.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.x_min, 0, 3, 1, 1)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 4, 1, 1)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 2, 1, 1)

        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 1, 4, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.y_max = QLineEdit(self.groupBox_2)
        self.y_max.setObjectName(u"y_max")
        self.y_max.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.y_max, 1, 5, 1, 1)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 1, 2, 1, 1)

        self.y_min = QLineEdit(self.groupBox_2)
        self.y_min.setObjectName(u"y_min")
        self.y_min.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.y_min, 1, 3, 1, 1)


        self.horizontalLayout_2.addWidget(self.groupBox_2)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.fit_button = QPushButton(PlotTab)
        self.fit_button.setObjectName(u"fit_button")

        self.verticalLayout_6.addWidget(self.fit_button)

        self.set_limits_button = QPushButton(PlotTab)
        self.set_limits_button.setObjectName(u"set_limits_button")

        self.verticalLayout_6.addWidget(self.set_limits_button)


        self.horizontalLayout_2.addLayout(self.verticalLayout_6)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)


        self.horizontalLayout.addLayout(self.verticalLayout_5)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.groupBox = QGroupBox(PlotTab)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(400, 0))
        self.formLayout_4 = QFormLayout(self.groupBox)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.formLayout_4.setContentsMargins(4, 4, 4, 4)
        self.model_func_label = QLabel(self.groupBox)
        self.model_func_label.setObjectName(u"model_func_label")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.model_func_label)

        self.show_initial_fit = QCheckBox(self.groupBox)
        self.show_initial_fit.setObjectName(u"show_initial_fit")
        self.show_initial_fit.setChecked(True)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.show_initial_fit)

        self.model_func = QPlainTextEdit(self.groupBox)
        self.model_func.setObjectName(u"model_func")
        self.model_func.setLineWrapMode(QPlainTextEdit.WidgetWidth)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.model_func)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.groupBox_4 = QGroupBox(PlotTab)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_7 = QLabel(self.groupBox_4)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_3.addWidget(self.label_7)

        self.fit_start_box = SpinBox(self.groupBox_4)
        self.fit_start_box.setObjectName(u"fit_start_box")
        self.fit_start_box.setMinimumSize(QSize(75, 0))

        self.horizontalLayout_3.addWidget(self.fit_start_box)

        self.horizontalSpacer_3 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.label_8 = QLabel(self.groupBox_4)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_3.addWidget(self.label_8)

        self.fit_end_box = SpinBox(self.groupBox_4)
        self.fit_end_box.setObjectName(u"fit_end_box")
        self.fit_end_box.setMinimumSize(QSize(75, 0))

        self.horizontalLayout_3.addWidget(self.fit_end_box)

        self.horizontalSpacer_2 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.use_fit_domain = QCheckBox(self.groupBox_4)
        self.use_fit_domain.setObjectName(u"use_fit_domain")

        self.horizontalLayout_3.addWidget(self.use_fit_domain)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_9 = QLabel(self.groupBox_4)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_4.addWidget(self.label_9)

        self.draw_curve_option = QComboBox(self.groupBox_4)
        self.draw_curve_option.setObjectName(u"draw_curve_option")

        self.horizontalLayout_4.addWidget(self.draw_curve_option)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.verticalLayout_3.addLayout(self.horizontalLayout_4)


        self.verticalLayout_2.addWidget(self.groupBox_4)

        self.parameter_box = QGroupBox(PlotTab)
        self.parameter_box.setObjectName(u"parameter_box")
        self.verticalLayout_4 = QVBoxLayout(self.parameter_box)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(4, 4, 4, 4)
        self.scrollArea = QScrollArea(self.parameter_box)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.parameter_list = QWidget()
        self.parameter_list.setObjectName(u"parameter_list")
        self.parameter_list.setGeometry(QRect(0, 0, 384, 90))
        self.scrollArea.setWidget(self.parameter_list)

        self.verticalLayout_4.addWidget(self.scrollArea)


        self.verticalLayout_2.addWidget(self.parameter_box)

        self.groupBox_3 = QGroupBox(PlotTab)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout = QVBoxLayout(self.groupBox_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.result_box = QPlainTextEdit(self.groupBox_3)
        self.result_box.setObjectName(u"result_box")
        font = QFont()
        font.setFamilies([u"Courier New"])
        self.result_box.setFont(font)
        self.result_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.result_box.setReadOnly(True)

        self.verticalLayout.addWidget(self.result_box)


        self.verticalLayout_2.addWidget(self.groupBox_3)

        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(2, 1)
        self.verticalLayout_2.setStretch(3, 2)

        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.horizontalLayout.setStretch(0, 1)
        QWidget.setTabOrder(self.show_initial_fit, self.fit_start_box)
        QWidget.setTabOrder(self.fit_start_box, self.fit_end_box)
        QWidget.setTabOrder(self.fit_end_box, self.use_fit_domain)
        QWidget.setTabOrder(self.use_fit_domain, self.draw_curve_option)
        QWidget.setTabOrder(self.draw_curve_option, self.result_box)
        QWidget.setTabOrder(self.result_box, self.xlabel)
        QWidget.setTabOrder(self.xlabel, self.x_min)
        QWidget.setTabOrder(self.x_min, self.x_max)
        QWidget.setTabOrder(self.x_max, self.ylabel)
        QWidget.setTabOrder(self.ylabel, self.y_min)
        QWidget.setTabOrder(self.y_min, self.y_max)

        self.retranslateUi(PlotTab)

        QMetaObject.connectSlotsByName(PlotTab)
    # setupUi

    def retranslateUi(self, PlotTab):
        PlotTab.setWindowTitle(QCoreApplication.translate("PlotTab", u"Plot Tab", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("PlotTab", u"Axis settings", None))
        self.label_5.setText(QCoreApplication.translate("PlotTab", u"Max:", None))
        self.label_2.setText(QCoreApplication.translate("PlotTab", u"Y \u2014", None))
        self.label_3.setText(QCoreApplication.translate("PlotTab", u"Min:", None))
        self.label_6.setText(QCoreApplication.translate("PlotTab", u"Max:", None))
        self.label.setText(QCoreApplication.translate("PlotTab", u"X \u2014", None))
        self.label_4.setText(QCoreApplication.translate("PlotTab", u"Min:", None))
        self.fit_button.setText(QCoreApplication.translate("PlotTab", u"(Re)Fit model", None))
        self.set_limits_button.setText(QCoreApplication.translate("PlotTab", u"(Re)Set plot limits", None))
        self.groupBox.setTitle(QCoreApplication.translate("PlotTab", u"Model", None))
        self.model_func_label.setText(QCoreApplication.translate("PlotTab", u"Placeholder:", None))
        self.show_initial_fit.setText(QCoreApplication.translate("PlotTab", u"Show initial fit", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("PlotTab", u"Fit options", None))
        self.label_7.setText(QCoreApplication.translate("PlotTab", u"Start:", None))
        self.label_8.setText(QCoreApplication.translate("PlotTab", u"End:", None))
        self.use_fit_domain.setText(QCoreApplication.translate("PlotTab", u"Use domain", None))
        self.label_9.setText(QCoreApplication.translate("PlotTab", u"Draw curve:", None))
        self.parameter_box.setTitle(QCoreApplication.translate("PlotTab", u"Starting values and parameter bounds", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("PlotTab", u"Information", None))
    # retranslateUi

