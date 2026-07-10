import sys
import os
import json
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem,
                             QMessageBox, QHeaderView, QFileDialog)
from PyQt6.QtCore import (Qt, QSettings)
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from ui_design import Ui_main_window
import csv
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_product_data = None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base_dir, 'data')

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.db_path = os.path.join(self.data_dir, 'calories.db')

        self._init_db()
        self._setup_ui()
        self.settings = QSettings("MyCompany", "AppCalculator")
        self.current_theme = self.settings.value("theme", "light")
        self.apply_theme()
        self._load_products_to_list()
        self._bind_signals()
        self.shortcut_theme = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_theme.activated.connect(self.toggle_theme)
        self.shortcut_clear = QShortcut(QKeySequence("Ctrl+Del"), self)
        self.shortcut_clear.activated.connect(self.clear_table)
        self.on_product_select(self.ui.input_name.currentText())
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                kcal REAL,
                protein REAL,
                fat REAL,
                carbs REAL
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            json_path = os.path.join(self.data_dir, 'products.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        name = item['name']
                        kcal = item['kcal']
                        prot = item['protein']
                        fat = item['fat']
                        carb = item['carbs']
                        cursor.execute("INSERT INTO products (name, kcal, protein, fat, carbs) VALUES (?, ?, ?, ?, ?)",
                                       (name, kcal, prot, fat, carb))
                    conn.commit()
        conn.close()

    def _setup_ui(self):
        self.ui = Ui_main_window()
        self.ui.setupUi(self)
        self.ui.btn_export.clicked.connect(self.export_data)
        self.ui.btn_import.clicked.connect(self.import_data)

        header = self.ui.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
          
    def export_data(self):
        if self.ui.table.rowCount() == 0:
            QMessageBox.warning(self, "Ошибка", "Таблица пустая!")
            return
        path, filter_type = QFileDialog.getSaveFileName(self, "Сохранить данные", "", "JSON Files (*.json);;CSV Files (*.csv)")
        if not path:
            return
        data = []
        headers = [self.ui.table.horizontalHeaderItem(i).text() for i in range(self.ui.table.columnCount())]
        for row in range(self.ui.table.rowCount()):
            row_data = {}
            for col in range(self.ui.table.columnCount()):
                item = self.ui.table.item(row, col)
                row_data[headers[col]] = item.text() if item else ""
            data.append(row_data)

        try:
            if path.endswith('.json'):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            elif path.endswith('.csv'):
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(data)
            QMessageBox.information(self, "Успех", "Данные успешно экспортированы!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить данные", "", "JSON Files (*.json);;CSV Files (*.csv)")
        if not path:
            return
        try:
            data = []
            if path.endswith('.json'):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif path.endswith('.csv'):
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data.append(row)

            self.ui.table.setRowCount(0)

            for row_idx, row_data in enumerate(data):
                self.ui.table.insertRow(row_idx)
                for col_idx, key in enumerate(row_data.keys()):
                    self.ui.table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data[key])))
            self.calculate_totals()
            QMessageBox.information(self, "Успех", "Данные успешно загружены!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {e}")

    def apply_theme(self):
        if self.current_theme == "dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: #ffffff; }
                QTableWidget { background-color: #3b3b3b; color: #ffffff; gridline-color: #555555; }
                QHeaderView::section { background-color: #4b4b4b; color: #ffffff; }
                QPushButton { background-color: #4b4b4b; color: #ffffff; border-radius: 5px; padding: 5px; }
                QPushButton:hover { background-color: #5b5b5b; }
            """)
        else:
            self.setStyleSheet("")

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.settings.setValue("theme", self.current_theme)
        self.apply_theme()

    def _load_products_to_list(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products ORDER BY name")
        rows = cursor.fetchall()
        for row in rows:
            product_name = row[0]
            self.ui.input_name.addItem(product_name)
        conn.close()

    def _bind_signals(self):
        self.ui.btn_add.clicked.connect(self.add_to_table)
        self.ui.btn_clear.clicked.connect(self.clear_table)
        self.ui.btn_load_photo.clicked.connect(self.load_photo)
        self.ui.spin_persons.valueChanged.connect(self.calculate_totals)

        self.ui.input_name.currentTextChanged.connect(self.on_product_select)
        self.ui.input_weight.valueChanged.connect(self.calculate_nutrients)

    def on_product_select(self, name_of_product):
        if not name_of_product: return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT kcal, protein, fat, carbs FROM products WHERE name = ?", (name_of_product,))
        self.current_product_data = cursor.fetchone()
        conn.close()
        self.calculate_nutrients()

    def calculate_nutrients(self):
        if not self.current_product_data: return
        weight = self.ui.input_weight.value()
        factor = weight / 100

        kcal = self.current_product_data[0] * factor
        protein = self.current_product_data[1] * factor
        fat = self.current_product_data[2] * factor
        carbs = self.current_product_data[3] * factor

        self.ui.input_kcal.blockSignals(True)
        self.ui.input_protein.blockSignals(True)
        self.ui.input_fat.blockSignals(True)
        self.ui.input_carbs.blockSignals(True)

        self.ui.input_kcal.setValue(kcal)
        self.ui.input_protein.setValue(protein)
        self.ui.input_fat.setValue(fat)
        self.ui.input_carbs.setValue(carbs)

        self.ui.input_kcal.blockSignals(False)
        self.ui.input_protein.blockSignals(False)
        self.ui.input_fat.blockSignals(False)
        self.ui.input_carbs.blockSignals(False)
    def load_photo(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Выберите фото")
        if path:
            pix = QPixmap(path)
            self.ui.lbl_photo.setPixmap(pix.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))

    def add_to_table(self):
        if self.ui.input_weight.value() <= 0: return

        row = self.ui.table.rowCount()
        self.ui.table.insertRow(row)

        self.ui.table.setItem(row, 0, QTableWidgetItem(self.ui.input_name.currentText()))
        self.ui.table.setItem(row, 1, QTableWidgetItem(str(self.ui.input_weight.value())))
        self.ui.table.setItem(row, 2, QTableWidgetItem(str(self.ui.input_kcal.value())))
        self.ui.table.setItem(row, 3, QTableWidgetItem(str(self.ui.input_protein.value())))
        self.ui.table.setItem(row, 4, QTableWidgetItem(str(self.ui.input_fat.value())))
        self.ui.table.setItem(row, 5, QTableWidgetItem(str(self.ui.input_carbs.value())))
        self.calculate_totals()

    def calculate_totals(self):
        total_kcal = 0
        for i in range(self.ui.table.rowCount()):
            val = float(self.ui.table.item(i, 2).text())
            total_kcal += val
        persons = self.ui.spin_persons.value()
        self.ui.lbl_total_kcal.setText(f"Итого: {total_kcal:.1f} ккал")
        if persons > 0:
            self.ui.lbl_portion_kcal.setText(f"На порцию: {total_kcal / persons:.1f} ккал")

    def clear_table(self):
        self.ui.table.setRowCount(0)
        self.calculate_totals()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Выход", "Вы уверены что хотите выйти?,\n все несохранённые данные в таблице будут удалены", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
           event.accept()
        elif reply == QMessageBox.StandardButton.No:
           event.ignore()
 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

    
      

        
