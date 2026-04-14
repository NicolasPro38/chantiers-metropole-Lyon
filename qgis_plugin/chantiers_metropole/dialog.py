from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QFormLayout,
    QMessageBox, QTextEdit
)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsDataSourceUri,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsFillSymbol
)
from qgis.gui import QgsMapToolIdentifyFeature

DB_HOST = "localhost"
DB_NAME = "chantiers"
DB_USER = "user_chantiers"
DB_PASSWORD = "chantiers2026"
DB_PORT = "5432"

class ChantiersDialog(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.layer = None
        self.identify_tool = None
        self.prev_tool = None
        self.setWindowTitle("Chantiers – Métropole de Lyon")
        self.setMinimumWidth(420)
        self.setup_ui()
        self.charger_communes()

    def setup_ui(self):
        layout = QVBoxLayout()

        titre = QLabel("🚧 Chargement des chantiers")
        titre.setStyleSheet("font-size:14px; font-weight:bold; color:#C8102E; padding:8px 0;")
        layout.addWidget(titre)

        group = QGroupBox("Filtres")
        form = QFormLayout()

        self.combo_commune = QComboBox()
        self.combo_commune.addItem("Toutes les communes", "")
        form.addRow("Commune :", self.combo_commune)

        self.combo_etat = QComboBox()
        self.combo_etat.addItem("Tous les états", "")
        self.combo_etat.addItem("Ouvert", "Ouvert")
        self.combo_etat.addItem("Validé", "Validé")
        self.combo_etat.addItem("Terminé", "Terminé")
        form.addRow("État :", self.combo_etat)

        group.setLayout(form)
        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        self.btn_charger = QPushButton("Charger la couche")
        self.btn_charger.setStyleSheet(
            "background:#C8102E; color:white; font-weight:bold; padding:8px; border-radius:4px;"
        )
        self.btn_charger.clicked.connect(self.charger_couche)

        self.btn_identifier = QPushButton("🖱 Identifier un chantier")
        self.btn_identifier.setStyleSheet(
            "background:#E87722; color:white; font-weight:bold; padding:8px; border-radius:4px;"
        )
        self.btn_identifier.clicked.connect(self.activer_identification)
        self.btn_identifier.setEnabled(False)

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.clicked.connect(self.close)

        btn_layout.addWidget(self.btn_charger)
        btn_layout.addWidget(self.btn_identifier)
        btn_layout.addWidget(self.btn_fermer)
        layout.addLayout(btn_layout)

        # Zone d'affichage des attributs
        self.info_box = QGroupBox("Détail du chantier")
        info_layout = QVBoxLayout()
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(180)
        self.detail_text.setStyleSheet("font-size:12px; font-family: monospace;")
        self.detail_text.setPlaceholderText("Cliquez sur un chantier sur la carte pour voir ses détails...")
        info_layout.addWidget(self.detail_text)
        self.info_box.setLayout(info_layout)
        layout.addWidget(self.info_box)

        self.label_info = QLabel("")
        self.label_info.setStyleSheet("color:#666; font-size:11px; padding:4px 0;")
        self.label_info.setWordWrap(True)
        layout.addWidget(self.label_info)

        self.setLayout(layout)

    def charger_communes(self):
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=DB_HOST, dbname=DB_NAME,
                user=DB_USER, password=DB_PASSWORD, port=DB_PORT
            )
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT commune FROM chantiers WHERE commune IS NOT NULL ORDER BY commune;")
            for row in cur.fetchall():
                self.combo_commune.addItem(row[0], row[0])
            conn.close()
        except Exception as e:
            self.label_info.setText(f"Erreur connexion PostGIS : {e}")

    def charger_couche(self):
        commune = self.combo_commune.currentData()
        etat = self.combo_etat.currentData()

        conditions = []
        if commune:
            conditions.append(f"commune = $${commune}$$")
        if etat:
            conditions.append(f"etat = $${etat}$$")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"(SELECT * FROM chantiers WHERE {where})"

        uri = QgsDataSourceUri()
        uri.setConnection(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
        uri.setDataSource("", sql, "geom", "", "gid")

        layer_name = "Chantiers"
        if commune:
            layer_name += f" – {commune}"
        if etat:
            layer_name += f" ({etat})"

        self.layer = QgsVectorLayer(uri.uri(False), layer_name, "postgres")

        if not self.layer.isValid():
            QMessageBox.critical(self, "Erreur", "Impossible de charger la couche PostGIS.\nVérifiez que le serveur est démarré.")
            return

        styles = {
            "Ouvert":  ("#E87722", 0.6),
            "Validé":  ("#C8102E", 0.6),
            "Terminé": ("#888888", 0.4),
        }
        categories = []
        for val, (couleur, opacite) in styles.items():
            symbol = QgsFillSymbol.createSimple({
                "color": couleur,
                "outline_color": "#ffffff",
                "outline_width": "0.3"
            })
            symbol.setOpacity(opacite)
            categories.append(QgsRendererCategory(val, symbol, val))

        self.layer.setRenderer(QgsCategorizedSymbolRenderer("etat", categories))
        QgsProject.instance().addMapLayer(self.layer)
        self.iface.mapCanvas().setExtent(self.layer.extent())
        self.iface.mapCanvas().refresh()

        nb = self.layer.featureCount()
        self.label_info.setText(f"✅ {nb} chantiers chargés.")
        self.btn_identifier.setEnabled(True)

    def activer_identification(self):
        if not self.layer:
            return

        self.prev_tool = self.iface.mapCanvas().mapTool()
        self.identify_tool = QgsMapToolIdentifyFeature(self.iface.mapCanvas(), self.layer)
        self.identify_tool.featureIdentified.connect(self.afficher_detail)
        self.iface.mapCanvas().setMapTool(self.identify_tool)
        self.label_info.setText("🖱 Cliquez sur un chantier sur la carte...")
        self.showMinimized()

    def afficher_detail(self, feature):
        self.showNormal()
        self.raise_()

        attrs = {
            "N° dossier":      feature["numero"],
            "Intervenant":     feature["intervenant"],
            "Nature chantier": feature["nature_chantier"],
            "Nature travaux":  feature["nature_travaux"],
            "État":            feature["etat"],
            "Adresse":         feature["adresse"],
            "Commune":         feature["commune"],
            "Début":           str(feature["date_debut"]) if feature["date_debut"] else "–",
            "Fin prévue":      str(feature["date_fin"]) if feature["date_fin"] else "–",
            "Mesures police":  feature["mesures_police"] or "–",
            "Contact":         feature["contact_url"] or "–",
        }

        texte = ""
        for key, val in attrs.items():
            texte += f"{'─' * 35}\n{key.upper()}\n  {val}\n"

        self.detail_text.setPlainText(texte)
        self.label_info.setText("✅ Chantier identifié.")

        # Remettre l'outil précédent
        if self.prev_tool:
            self.iface.mapCanvas().setMapTool(self.prev_tool)

    def closeEvent(self, event):
        if self.prev_tool:
            self.iface.mapCanvas().setMapTool(self.prev_tool)
        super().closeEvent(event)
