# coding: utf-8

""" a convenient import of all Qt classes used """

from pyqtgraph import Qt

if Qt.QT_LIB == Qt.PYSIDE6:
    from PySide6.QtCore import QTimer, QSettings, Qt, Signal, QRect, QByteArray, QPoint, QModelIndex, \
        QLocale, QLibraryInfo, QTranslator
    from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget, QDialogButtonBox, QListWidgetItem
    from PySide6.QtGui import QColor, QCloseEvent, QValidator, QPalette, QPaintEvent
elif Qt.QT_LIB == Qt.PYQT5:
    from PyQt5.QtCore import QTimer, QSettings, Qt, pyqtSignal as Signal, QRect, QByteArray, QPoint, QModelIndex, \
        QLocale, QLibraryInfo, QTranslator
    from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget, QDialogButtonBox, QListWidgetItem
    from PyQt5.QtGui import QCloseEvent, QColor, QPaintEvent, QPalette, QValidator

    QLibraryInfo.LibraryPath = QLibraryInfo.LibraryLocation
    QLibraryInfo.path = QLibraryInfo.location
elif Qt.QT_LIB == Qt.PYQT6:
    from PyQt6.QtCore import QTimer, QSettings, Qt, pyqtSignal as Signal, QRect, QByteArray, QPoint, QModelIndex, \
        QLocale, QLibraryInfo, QTranslator
    from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget, QDialogButtonBox, QListWidgetItem
    from PyQt6.QtGui import QCloseEvent, QColor, QPaintEvent, QPalette, QValidator
elif Qt.QT_LIB == Qt.PYSIDE2:
    from PySide2.QtCore import QTimer, Qt, QSettings, Signal, QRect, QByteArray, QPoint, QModelIndex, \
        QLocale, QLibraryInfo, QTranslator
    from PySide2.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget, QDialogButtonBox, QListWidgetItem
    from PySide2.QtGui import QCloseEvent, QColor, QPaintEvent, QPalette, QValidator

    QLibraryInfo.LibraryPath = QLibraryInfo.LibraryLocation
    QLibraryInfo.path = QLibraryInfo.location
    QApplication.exec = QApplication.exec_
    QDialog.exec = QDialog.exec_
    QFileDialog.exec = QFileDialog.exec_
else:
    raise ImportError('PySide6 or PyQt5 is preferred. '
                      'PySide2 does localisation inconsistently. '
                      'PyQt6 support is not guaranteed. '
                      f'{Qt.QT_LIB} is not supported at all.')  # in case pg add support for another framework

__all__ = [
    'Qt',
    'QByteArray',
    'QLibraryInfo',
    'QLocale',
    'QModelIndex',
    'QPoint',
    'QRect',
    'QSettings',
    'QTimer',
    'QTranslator',
    'Signal',

    'QSizePolicy', 'QStyle',
    'QWidget',
    'QTabWidget',
    'QFormLayout', 'QHBoxLayout', 'QVBoxLayout',
    'QGroupBox',
    'QLabel', 'QCheckBox', 'QPushButton', 'QToolButton', 'QLineEdit', 'QSpinBox', 'QComboBox',
    'QListWidgetItem', 'QListWidget',
    'QDialogButtonBox', 'QDialog', 'QFileDialog',
    'QMainWindow',
    'QApplication',

    'QCloseEvent',
    'QColor',
    'QPaintEvent',
    'QPalette',
    'QValidator'
]
