# coding: utf-8

from __future__ import annotations

import sys

from gui import QApplication, App


if __name__ == '__main__':
    app: QApplication = QApplication(sys.argv)
    window: App = App()
    window.show()
    app.exec()
