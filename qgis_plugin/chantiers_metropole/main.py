from qgis.PyQt.QtWidgets import QAction
from .dialog import ChantiersDialog

class ChantiersMetropole:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        self.action = QAction("🚧 Chantiers Métropole de Lyon", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("Métropole de Lyon", self.action)

    def unload(self):
        self.iface.removePluginMenu("Métropole de Lyon", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        dialog = ChantiersDialog(self.iface)
        dialog.show()
        dialog.exec_()
