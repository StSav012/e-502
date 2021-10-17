# coding: utf-8

from __future__ import annotations

import os
import sys
from typing import Set

from gui.app import App
from gui.pg_qt import *


def execute() -> int:
    # https://www.reddit.com/r/learnpython/comments/4kjie3/how_to_include_gui_images_with_pyinstaller/d3gjmom
    def resource_path(relative_path: str) -> str:
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(getattr(sys, '_MEIPASS'), relative_path)
        return os.path.join(os.path.abspath('.'), relative_path)

    application: QApplication = QApplication(sys.argv)

    languages: Set[str] = set(QLocale().uiLanguages() + [QLocale().bcp47Name(), QLocale().name()])
    language: str
    qt_translator: QTranslator = QTranslator()
    for language in languages:
        if qt_translator.load('qt_' + language,
                              QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            application.installTranslator(qt_translator)
            break
    qtbase_translator: QTranslator = QTranslator()
    for language in languages:
        if qtbase_translator.load('qtbase_' + language,
                                  QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            application.installTranslator(qtbase_translator)
            break
    my_translator: QTranslator = QTranslator()
    if my_translator.load(QLocale.system().name(), resource_path('translations')):
        application.installTranslator(my_translator)

    import re
    from pyqtgraph import functions as fn

    fn.SI_PREFIXES = QApplication.translate('si prefixes', 'y,z,a,f,p,n,µ,m, ,k,M,G,T,P,E,Z,Y').split(',')
    fn.SI_PREFIXES_ASCII = fn.SI_PREFIXES
    fn.SI_PREFIX_EXPONENTS.update(dict([(s, (i - 8) * 3) for i, s in enumerate(fn.SI_PREFIXES)]))
    if QApplication.translate('si prefix alternative micro', 'u'):
        fn.SI_PREFIX_EXPONENTS[QApplication.translate('si prefix alternative micro', 'u')] = -6
    fn.FLOAT_REGEX = re.compile(
        r'(?P<number>[+-]?((((\d+(\.\d*)?)|(\d*\.\d+))([eE][+-]?\d+)?)'
        r'|(nan|NaN|NAN|inf|Inf|INF)))\s*'
        r'((?P<siPrefix>[u(' + '|'.join(fn.SI_PREFIXES) + r')]?)(?P<suffix>\w.*))?$')
    fn.INT_REGEX = re.compile(r'(?P<number>[+-]?\d+)\s*'
                              r'(?P<siPrefix>[u(' + '|'.join(fn.SI_PREFIXES) + r')]?)(?P<suffix>.*)$')

    window: App = App()
    window.show()
    return application.exec()
