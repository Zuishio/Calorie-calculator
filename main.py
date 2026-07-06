import sys
import os
import json
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem,
                             QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ui_design import Ui_main_window

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
        self._load_products_to_list()
        self._bind_signals()

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

        header = self.ui.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

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
