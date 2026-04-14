from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QFormLayout, QMessageBox
)
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsDataSourceUri,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsFillSymbol
)

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

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.clicked.connect(self.close)

        btn_layout.addWidget(self.btn_charger)
        btn_layout.addWidget(self.btn_fermer)
        layout.addLayout(btn_layout)

        self.label_info = QLabel("")
        self.label_info.setStyleSheet("color:#666; font-size:11px; padding:4px 0;")
        self.label_info.setWordWrap(True)
        layout.addWidget(self.label_info)

        # Info utilisation
        hint = QLabel("💡 Après chargement, utilisez l'outil Identifier (touche I) pour cliquer sur un chantier.")
        hint.setStyleSheet("color:#888; font-size:11px; font-style:italic;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

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
            QMessageBox.critical(self, "Erreur", "Impossible de charger la couche PostGIS.")
            return

        # Style catégorisé par état
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

        # Expression d'affichage pour le panneau Identifier
        self.layer.setDisplayExpression(
            "concat('🚧 ', \"nature_chantier\", ' – ', \"commune\")"
        )

        QgsProject.instance().addMapLayer(self.layer)
        self.iface.mapCanvas().setExtent(self.layer.extent())
        self.iface.mapCanvas().refresh()

        # Activer l'outil Identifier automatiquement
        self.iface.actionIdentify().trigger()

        nb = self.layer.featureCount()
        self.label_info.setText(f"✅ {nb} chantiers chargés.")
