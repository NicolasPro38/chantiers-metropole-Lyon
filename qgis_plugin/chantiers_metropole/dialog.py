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

        # Filtres
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

        # Boutons chargement
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

        # Boutons édition
        group_edit = QGroupBox("Édition PostGIS")
        edit_layout = QHBoxLayout()

        self.btn_editer = QPushButton("✏️ Activer l'édition")
        self.btn_editer.setStyleSheet(
            "background:#E87722; color:white; font-weight:bold; padding:8px; border-radius:4px;"
        )
        self.btn_editer.clicked.connect(self.activer_edition)
        self.btn_editer.setEnabled(False)

        self.btn_sauvegarder = QPushButton("💾 Sauvegarder")
        self.btn_sauvegarder.setStyleSheet(
            "background:#2e7d32; color:white; font-weight:bold; padding:8px; border-radius:4px;"
        )
        self.btn_sauvegarder.clicked.connect(self.sauvegarder)
        self.btn_sauvegarder.setEnabled(False)

        self.btn_annuler_edit = QPushButton("↩️ Annuler")
        self.btn_annuler_edit.setStyleSheet(
            "background:#666; color:white; font-weight:bold; padding:8px; border-radius:4px;"
        )
        self.btn_annuler_edit.clicked.connect(self.annuler_edition)
        self.btn_annuler_edit.setEnabled(False)

        edit_layout.addWidget(self.btn_editer)
        edit_layout.addWidget(self.btn_sauvegarder)
        edit_layout.addWidget(self.btn_annuler_edit)
        group_edit.setLayout(edit_layout)
        layout.addWidget(group_edit)

        # Info
        self.label_info = QLabel("")
        self.label_info.setStyleSheet("color:#666; font-size:11px; padding:4px 0;")
        self.label_info.setWordWrap(True)
        layout.addWidget(self.label_info)

        hint = QLabel("💡 Utilisez l'outil Identifier (touche I) pour cliquer sur un chantier. En mode édition, double-cliquez sur un attribut dans la table pour le modifier.")
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
        self.layer.setDisplayExpression(
            "concat('🚧 ', \"nature_chantier\", ' – ', \"commune\")"
        )

        QgsProject.instance().addMapLayer(self.layer)
        self.iface.mapCanvas().setExtent(self.layer.extent())
        self.iface.mapCanvas().refresh()
        self.iface.actionIdentify().trigger()

        nb = self.layer.featureCount()
        self.label_info.setText(f"✅ {nb} chantiers chargés.")
        self.btn_editer.setEnabled(True)

    def activer_edition(self):
        if not self.layer:
            return
        self.layer.startEditing()
        self.btn_editer.setEnabled(False)
        self.btn_sauvegarder.setEnabled(True)
        self.btn_annuler_edit.setEnabled(True)
        self.label_info.setText("✏️ Mode édition activé. Modifiez les attributs via la table attributaire (F6).")
        # Ouvrir la table attributaire
        self.iface.showAttributeTable(self.layer)

    def sauvegarder(self):
        if not self.layer:
            return
        if self.layer.isEditable():
            if self.layer.commitChanges():
                self.label_info.setText("💾 Modifications sauvegardées dans PostGIS.")
                QMessageBox.information(self, "Succès", "Les modifications ont été sauvegardées dans PostGIS.")
            else:
                errors = self.layer.commitErrors()
                self.label_info.setText(f"❌ Erreur : {', '.join(errors)}")
                QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder :\n{chr(10).join(errors)}")
        self.btn_editer.setEnabled(True)
        self.btn_sauvegarder.setEnabled(False)
        self.btn_annuler_edit.setEnabled(False)

    def annuler_edition(self):
        if not self.layer:
            return
        self.layer.rollBack()
        self.label_info.setText("↩️ Modifications annulées.")
        self.btn_editer.setEnabled(True)
        self.btn_sauvegarder.setEnabled(False)
        self.btn_annuler_edit.setEnabled(False)
