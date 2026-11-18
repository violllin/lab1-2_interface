import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QComboBox,
                             QMessageBox, QFormLayout, QDoubleSpinBox, QSpinBox,
                             QListWidget, QStackedWidget, QGridLayout, QScrollArea,
                             QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIntValidator, QPalette
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models import Lab1Model, Lab2Model
from data_loader import load_dataset_from_txt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моделирование диалоговых систем")
        self.resize(1300, 850)

        self.lab1_model = Lab1Model()
        self.lab2_model = Lab2Model(self.lab1_model)

        self.setStyleSheet("""
            QMainWindow, QWidget, QDialog, QMessageBox, QScrollArea {
                background-color: #ffffff;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
            }
            QMessageBox QLabel {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QGroupBox {
                border: 2px solid #dcdde1;
                border-radius: 8px;
                margin-top: 15px;
                background-color: #ffffff;
                padding-top: 20px;
                font-weight: bold;
                color: #8e44ad;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background-color: #ffffff;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                padding: 5px;
                border-radius: 4px;
                color: #2c3e50;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 2px solid #8e44ad;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #2c3e50;
                selection-background-color: #f4ecf7;
                selection-color: #8e44ad;
            }
            QPushButton {
                background-color: #8e44ad;
                color: #ffffff;
                border: none;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #9b59b6; }
            QPushButton:pressed { background-color: #732d91; }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                gridline-color: #f1f2f6;
                border-radius: 4px;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 2px solid #bdc3c7;
                font-weight: bold;
                padding: 6px;
                color: #34495e;
            }
            QListWidget {
                background-color: #ffffff;
                border: none;
                border-right: 2px solid #dcdde1;
                outline: 0;
            }
            QListWidget::item {
                padding: 15px 10px;
                border-bottom: 1px solid #f1f2f6;
                color: #7f8c8d;
                font-weight: bold;
                background-color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #f4ecf7;
                color: #8e44ad;
                border-left: 4px solid #8e44ad;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItems(["Исходные данные", "ЛР1: Временные хар.", "ЛР2: Эффективность"])

        self.stack = QStackedWidget()
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        self.page_data = QWidget()
        self.page_hist = QWidget()
        self.page_sim = QWidget()

        self.stack.addWidget(self.page_data)
        self.stack.addWidget(self.page_hist)
        self.stack.addWidget(self.page_sim)

        self.init_data_page()
        self.init_hist_page()
        self.init_sim_page()

        self.auto_load_initial_files()
        self.sidebar.setCurrentRow(0)

    # ----------------------------- DATA PAGE -----------------------------
    def init_data_page(self):
        layout = QVBoxLayout(self.page_data)
        layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #ffffff; }")

        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)

        self.route_inputs = {"Регулирование": [], "Восстановление": []}
        self.route_weight_inputs = {"Регулирование": [], "Восстановление": []}
        self.error_inputs = {"Регулирование": [], "Восстановление": []}
        self.step_inputs = {"Регулирование": [], "Восстановление": []}
        self.path_inputs = {}

        # Вероятности выбора подтем
        prob_group = QGroupBox("Вероятности выбора подтем")
        prob_layout = QHBoxLayout()
        prob_layout.setContentsMargins(5, 5, 5, 5)
        prob_layout.addWidget(QLabel("P(Регулирование):"))
        self.subtopic_prob_inputs = [QLineEdit("0.5"), QLineEdit("0.5")]
        for le in self.subtopic_prob_inputs:
            le.setFixedWidth(70)
            le.setFixedHeight(28)
            le.setAlignment(Qt.AlignCenter)
        prob_layout.addWidget(self.subtopic_prob_inputs[0])
        prob_layout.addSpacing(20)
        prob_layout.addWidget(QLabel("P(Восстановление):"))
        prob_layout.addWidget(self.subtopic_prob_inputs[1])
        prob_layout.addStretch()
        prob_group.setLayout(prob_layout)
        container_layout.addWidget(prob_group)

        def create_set_section(title, subtopic_name):
            group = QGroupBox(title)
            vbox = QVBoxLayout()
            vbox.setSpacing(5)
            vbox.setContentsMargins(5, 5, 5, 5)

            file_layout = QHBoxLayout()
            file_layout.addWidget(QLabel("Файл:"))
            default_path = "подтема1.txt" if subtopic_name == 'Регулирование' else "подтема2.txt"
            le_path = QLineEdit(default_path)
            le_path.setFixedHeight(28)
            self.path_inputs[subtopic_name] = le_path
            file_layout.addWidget(le_path, 1)

            btn_load = QPushButton("Загрузить")
            btn_load.clicked.connect(lambda _, s=subtopic_name: self.load_file_to_gui(s))
            file_layout.addWidget(btn_load)

            btn_save = QPushButton("Сохранить")
            btn_save.clicked.connect(lambda _, s=subtopic_name: self.save_file_from_gui(s))
            file_layout.addWidget(btn_save)

            vbox.addLayout(file_layout)
            vbox.addSpacing(5)

            columns_layout = QHBoxLayout()
            columns_layout.setSpacing(10)

            # 1. Колонка: P ошибки на шаге
            err_group = QGroupBox("P ошибки на шаге")
            err_layout = QVBoxLayout()
            err_layout.setSpacing(4)
            err_layout.setContentsMargins(10, 0, 10, 5)

            # Заглушка под высоту заголовка центральной колонки
            dummy_h = QLabel(" ")
            dummy_h.setFixedHeight(28)
            err_layout.addWidget(dummy_h)

            self.error_inputs[subtopic_name] = []
            for i in range(10):
                h = QHBoxLayout()
                h.setSpacing(6)
                lbl = QLabel(f"ш{i + 1}")
                lbl.setFixedWidth(25)
                lbl.setFixedHeight(28)
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                h.addWidget(lbl)

                le = QLineEdit("0.1")
                le.setFixedWidth(45)
                le.setFixedHeight(28)
                le.setAlignment(Qt.AlignCenter)
                h.addWidget(le)
                err_layout.addLayout(h)
                self.error_inputs[subtopic_name].append(le)

            err_group.setLayout(err_layout)
            err_group.setFixedWidth(130) # <--- Увеличили ширину, чтобы влезло название
            columns_layout.addWidget(err_group)

            # 2. Колонка: Маршруты + вес
            routes_group = QGroupBox("Маршруты (шаги; 0 = конец) + вес")
            routes_vbox = QVBoxLayout(routes_group)
            routes_vbox.setContentsMargins(5, 0, 5, 5)

            grid_container = QHBoxLayout()
            grid_container.setContentsMargins(0, 0, 0, 0)
            routes_grid = QGridLayout()
            routes_grid.setSpacing(4)

            hdr = QLabel("")
            hdr.setFixedWidth(30)
            hdr.setFixedHeight(28)
            routes_grid.addWidget(hdr, 0, 0)

            for c in range(10):
                lbl = QLabel(f"ш{c + 1}")
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("font-weight: bold; color: #8e44ad; font-size: 9pt;")
                lbl.setFixedWidth(40)
                lbl.setFixedHeight(28)
                routes_grid.addWidget(lbl, 0, c + 1)

            lbl_w = QLabel("вес")
            lbl_w.setAlignment(Qt.AlignCenter)
            lbl_w.setStyleSheet("font-weight: bold; color: #8e44ad; font-size: 9pt;")
            lbl_w.setFixedWidth(50)
            lbl_w.setFixedHeight(28)
            routes_grid.addWidget(lbl_w, 0, 11)

            self.route_inputs[subtopic_name] = []
            self.route_weight_inputs[subtopic_name] = []

            for row_idx in range(10):
                lbl = QLabel(f"М{row_idx + 1}")
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                lbl.setFixedWidth(30)
                lbl.setFixedHeight(28)
                routes_grid.addWidget(lbl, row_idx + 1, 0)

                row_boxes = []
                for col_idx in range(10):
                    le = QLineEdit("0")
                    le.setFixedWidth(40)
                    le.setFixedHeight(28)
                    le.setAlignment(Qt.AlignCenter)
                    le.setValidator(QIntValidator(0, 99))
                    routes_grid.addWidget(le, row_idx + 1, col_idx + 1)
                    row_boxes.append(le)
                self.route_inputs[subtopic_name].append(row_boxes)

                w_le = QLineEdit("1.0")
                w_le.setFixedWidth(50)
                w_le.setFixedHeight(28)
                w_le.setAlignment(Qt.AlignCenter)
                routes_grid.addWidget(w_le, row_idx + 1, 11)
                self.route_weight_inputs[subtopic_name].append(w_le)

            grid_container.addLayout(routes_grid)
            grid_container.addStretch()
            routes_vbox.addLayout(grid_container)
            routes_vbox.addStretch()

            columns_layout.addWidget(routes_group, 1)

            # 3. Колонка: Таблица шагов
            steps_group = QGroupBox("Таблица шагов (конст. | μ)")
            steps_layout = QVBoxLayout()
            steps_layout.setSpacing(4)
            steps_layout.setContentsMargins(10, 0, 10, 5)

            dummy_h2 = QLabel(" ")
            dummy_h2.setFixedHeight(28)
            steps_layout.addWidget(dummy_h2)

            self.step_inputs[subtopic_name] = []

            for i in range(10):
                h = QHBoxLayout()
                h.setSpacing(4)

                lbl = QLabel(f"ш{i + 1}")
                lbl.setFixedWidth(25)
                lbl.setFixedHeight(28)
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                h.addWidget(lbl)

                le1 = QLineEdit("0.0")
                le2 = QLineEdit("5.0")
                le1.setFixedWidth(45)
                le2.setFixedWidth(45)
                le1.setFixedHeight(28)
                le2.setFixedHeight(28)
                le1.setAlignment(Qt.AlignCenter)
                le2.setAlignment(Qt.AlignCenter)
                h.addWidget(le1)
                h.addWidget(le2)
                steps_layout.addLayout(h)
                self.step_inputs[subtopic_name].append((le1, le2))

            steps_group.setLayout(steps_layout)
            steps_group.setFixedWidth(190)
            columns_layout.addWidget(steps_group)

            vbox.addLayout(columns_layout)
            group.setLayout(vbox)
            return group

        container_layout.addWidget(create_set_section("Подтема 1 (Регулирование)", "Регулирование"))
        container_layout.addWidget(create_set_section("Подтема 2 (Восстановление)", "Восстановление"))

        scroll.setWidget(container_widget)
        layout.addWidget(scroll)

    def auto_load_initial_files(self):
        for subtopic_name in ["Регулирование", "Восстановление"]:
            self.load_file_to_gui(subtopic_name, silent=True)

    def load_file_to_gui(self, subtopic_name, silent=False):
        path_le = self.path_inputs[subtopic_name]
        filepath = path_le.text().strip()

        if not silent and not filepath:
            options = QFileDialog.Options()
            filepath, _ = QFileDialog.getOpenFileName(
                self, f"Выберите txt файл для {subtopic_name}", "",
                "Text Files (*.txt);;All Files (*)", options=options
            )
            if filepath:
                path_le.setText(filepath)

        if not filepath:
            return

        data = load_dataset_from_txt(filepath)
        if not data:
            if not silent:
                QMessageBox.warning(self, "Ошибка", f"Файл {filepath} пуст или не найден.")
            return

        # 1. Маршруты
        boxes = self.route_inputs[subtopic_name]
        for r in range(len(boxes)):
            for c in range(len(boxes[r])):
                boxes[r][c].setText("0")
        for r, route in enumerate(data["cells"]):
            if r >= len(boxes):
                break
            for c, val in enumerate(route):
                if c >= len(boxes[r]):
                    break
                boxes[r][c].setText(str(val))

        # 2. Веса маршрутов
        if "route_probs" in data:
            for i, w in enumerate(data["route_probs"]):
                if i < len(self.route_weight_inputs[subtopic_name]):
                    self.route_weight_inputs[subtopic_name][i].setText(str(w))

        # 3. P_m_i
        for i, p_val in enumerate(data["P_m_i"]):
            if i < len(self.error_inputs[subtopic_name]):
                self.error_inputs[subtopic_name][i].setText(str(p_val))

        # 4. Таблица шагов
        step_boxes = self.step_inputs[subtopic_name]
        consts = data["t_step"][0]
        mus = data["t_step"][1]
        for i in range(len(step_boxes)):
            if i < len(consts):
                step_boxes[i][0].setText(str(consts[i]))
            if i < len(mus):
                step_boxes[i][1].setText(str(mus[i]))

        self.sync_ui_to_models()
        if not silent:
            QMessageBox.information(self, "Успех",
                                    f"Данные для {subtopic_name} успешно загружены из {filepath}!")

    def save_file_from_gui(self, subtopic_name):
        path_le = self.path_inputs[subtopic_name]
        filepath = path_le.text().strip()
        if not filepath:
            return
        try:
            self.sync_ui_to_models()
            sub_data = self.lab1_model.subtopics[subtopic_name]

            # Все 10 строк матрицы маршрутов (как ввели)
            matrix_rows = []
            for r in range(10):
                row = []
                for le in self.route_inputs[subtopic_name][r]:
                    val = le.text().strip()
                    try:
                        row.append(int(val) if val else 0)
                    except ValueError:
                        row.append(0)
                matrix_rows.append(row)

            # Все 10 весов
            weights_all = []
            for le in self.route_weight_inputs[subtopic_name]:
                try:
                    weights_all.append(float(le.text().replace(',', '.')))
                except ValueError:
                    weights_all.append(1.0)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Маршруты {subtopic_name} (10x10)\n")
                for row in matrix_rows:
                    f.write(" ".join(map(str, row)) + "\n")

                f.write("\n# Вероятности ошибочного перехода P_m_i\n")
                f.write(" ".join(map(str, sub_data["P_m_i"])) + "\n")

                f.write("\n# Таблица шагов: константа  μ\n")
                for c, mu in zip(sub_data["t_step"][0], sub_data["t_step"][1]):
                    f.write(f"{c} {mu}\n")

                f.write("\n# Веса маршрутов (по строкам матрицы)\n")
                f.write(" ".join(map(str, weights_all)) + "\n")

            QMessageBox.information(self, "Успех", f"Данные успешно сохранены в {filepath}!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def sync_ui_to_models(self):
        # P_m_i + t_step
        for subtopic_name in ["Регулирование", "Восстановление"]:
            errs = []
            for le in self.error_inputs[subtopic_name]:
                try:
                    errs.append(float(le.text().replace(',', '.')))
                except ValueError:
                    errs.append(0.1)
            self.lab1_model.subtopics[subtopic_name]["P_m_i"] = errs

            consts, mus = [], []
            for le1, le2 in self.step_inputs[subtopic_name]:
                try:
                    consts.append(float(le1.text().replace(',', '.')))
                except ValueError:
                    consts.append(0.0)
                try:
                    mus.append(float(le2.text().replace(',', '.')))
                except ValueError:
                    mus.append(0.0)
            self.lab1_model.subtopics[subtopic_name]["t_step"] = [consts, mus]

        # Вероятности подтем
        try:
            p1 = max(0.0, float(self.subtopic_prob_inputs[0].text().replace(',', '.')))
            p2 = max(0.0, float(self.subtopic_prob_inputs[1].text().replace(',', '.')))
            if p1 + p2 <= 0:
                p1, p2 = 0.5, 0.5
            self.lab1_model.subtopic_probs = [p1, p2]
        except ValueError:
            pass

    def get_routes_data(self):
        """Возвращает {подтема: [(route, weight), ...]}."""
        routes = {"Регулирование": [], "Восстановление": []}
        for sub_name in routes:
            weights_le = self.route_weight_inputs[sub_name]
            for i, row_boxes in enumerate(self.route_inputs[sub_name]):
                route = []
                for le in row_boxes:
                    val = le.text().strip()
                    if val:
                        try:
                            step = int(val)
                            if step == 0:
                                break
                            route.append(step)
                        except ValueError:
                            pass
                if route:
                    try:
                        w = max(0.0, float(weights_le[i].text().replace(',', '.')))
                    except ValueError:
                        w = 1.0
                    routes[sub_name].append((route, w))
        return routes

    def _compute_mean_theory(self, routes_with_weights, subtopic_name, p_override):
        if not routes_with_weights:
            return 0.0
        total_w = sum(w for _, w in routes_with_weights)
        use_uniform = total_w <= 0
        if use_uniform:
            total_w = len(routes_with_weights)

        m = 0.0
        for route, w in routes_with_weights:
            r_mean = 0.0
            for step in route:
                step_idx = (step - 1) % len(self.lab1_model.subtopics[subtopic_name]["P_m_i"])
                st = self.lab1_model.subtopics[subtopic_name]["t_step"]
                const_val = st[0][step_idx]
                mu_val = st[1][step_idx]
                step_m = const_val if const_val != 0.0 else mu_val
                p_err = (p_override if p_override is not None
                         else self.lab1_model.subtopics[subtopic_name]["P_m_i"][step_idx])
                r_mean += step_m * (1.0 + p_err)
            ww = 1.0 if use_uniform else w
            m += r_mean * (ww / total_w)
        return m

    # ----------------------------- HIST PAGE -----------------------------
    def init_hist_page(self):
        layout = QHBoxLayout(self.page_hist)
        control_panel = QVBoxLayout()

        group_params = QGroupBox("Параметры ЛР1 (Моделирование времени)")
        form_layout = QFormLayout()

        self.set_combo = QComboBox()
        self.set_combo.addItems([
            "Подтема 1 (Регулирование)",
            "Подтема 2 (Восстановление)",
            "Обе подтемы (общее время темы)"
        ])

        self.spin_n = QSpinBox()
        self.spin_n.setRange(100, 10000000)
        self.spin_n.setValue(1000)
        self.spin_n.setSingleStep(1000)

        self.spin_bins = QSpinBox()
        self.spin_bins.setRange(0, 200)
        self.spin_bins.setValue(0)
        self.spin_bins.setSpecialValueText("Авто (по формуле)")

        self.spin_sigma = QDoubleSpinBox()
        self.spin_sigma.setDecimals(3)
        self.spin_sigma.setRange(0.0, 10.0)
        self.spin_sigma.setValue(0.1)
        self.spin_sigma.setSingleStep(0.05)

        # Пресеты Pi по методичке
        self.combo_pi = QComboBox()
        self.combo_pi.addItems(["Из полей ввода", "Pi = 0.0", "Pi = 0.3", "Pi = 0.6", "Pi = 0.9"])

        form_layout.addRow("Подтема:", self.set_combo)
        form_layout.addRow("Выборка (N):", self.spin_n)
        form_layout.addRow("Интервалы (K):", self.spin_bins)
        form_layout.addRow("σ/μ норм. шагов:", self.spin_sigma)
        form_layout.addRow("Переопределение Pi:", self.combo_pi)

        self.btn_run_lab1 = QPushButton("Построить гистограмму")
        self.btn_run_lab1.clicked.connect(self.run_lab1)
        form_layout.addRow(self.btn_run_lab1)

        group_params.setLayout(form_layout)
        control_panel.addWidget(group_params)

        group_stats = QGroupBox("Статистические оценки")
        stats_layout = QVBoxLayout()
        self.lbl_mean = QLabel("t_ср: -")
        self.lbl_mean_theory = QLabel("t_ср теор.: -")
        self.lbl_t_sum = QLabel("t_sum: -")
        self.lbl_sd = QLabel("СКО: -")
        self.lbl_min = QLabel("Мин: -")
        self.lbl_max = QLabel("Макс: -")

        stats_layout.addWidget(self.lbl_mean)
        stats_layout.addWidget(self.lbl_mean_theory)
        stats_layout.addWidget(self.lbl_t_sum)
        stats_layout.addWidget(self.lbl_sd)
        stats_layout.addWidget(self.lbl_min)
        stats_layout.addWidget(self.lbl_max)

        group_stats.setLayout(stats_layout)
        control_panel.addWidget(group_stats)

        control_panel.addStretch()
        layout.addLayout(control_panel, 1)

        graph_panel = QVBoxLayout()
        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.figure.patch.set_facecolor('#ffffff')
        self.canvas = FigureCanvas(self.figure)
        graph_panel.addWidget(self.canvas)
        layout.addLayout(graph_panel, 3)

    # ----------------------------- SIM PAGE -----------------------------
    def init_sim_page(self):
        layout = QHBoxLayout(self.page_sim)

        left_panel = QVBoxLayout()
        group_sys = QGroupBox("Параметры ЛР2 (Эффективность СМ)")
        form_layout = QFormLayout()

        self.spin_rho1 = QDoubleSpinBox()
        self.spin_rho1.setDecimals(3)
        self.spin_rho1.setRange(0.0, 10000.0)
        self.spin_rho1.setValue(1.0)

        self.spin_rho2 = QDoubleSpinBox()
        self.spin_rho2.setDecimals(3)
        self.spin_rho2.setRange(0.0, 10000.0)
        self.spin_rho2.setValue(1.0)

        self.spin_lambda1 = QDoubleSpinBox()
        self.spin_lambda1.setDecimals(5)
        self.spin_lambda1.setRange(0.00001, 100.0)
        self.spin_lambda1.setSingleStep(0.001)
        self.spin_lambda1.setValue(0.01)

        self.spin_lambda2 = QDoubleSpinBox()
        self.spin_lambda2.setDecimals(5)
        self.spin_lambda2.setRange(0.00001, 100.0)
        self.spin_lambda2.setSingleStep(0.001)
        self.spin_lambda2.setValue(0.001)

        self.spin_iter = QSpinBox()
        self.spin_iter.setRange(10, 1000000)
        self.spin_iter.setValue(1000)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Регул + восст", "Регул", "Восстановление"])

        form_layout.addRow("ρ1 регул (удельные потери):", self.spin_rho1)
        form_layout.addRow("ρ2 восст (удельные потери):", self.spin_rho2)
        form_layout.addRow("λ1 заявок (интенсивность):", self.spin_lambda1)
        form_layout.addRow("λ2 отказов (интенсивность):", self.spin_lambda2)
        form_layout.addRow("Циклов N:", self.spin_iter)
        form_layout.addRow("Режим F:", self.combo_mode)

        self.btn_run_lab2 = QPushButton("Рассчитать эффективность")
        self.btn_run_lab2.clicked.connect(self.run_lab2)
        form_layout.addRow(self.btn_run_lab2)

        group_sys.setLayout(form_layout)
        left_panel.addWidget(group_sys)

        self.lbl_f_val = QLabel("F = -")
        self.lbl_f_val.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #8e44ad; padding: 10px; "
            "background-color: #ffffff; border-radius: 5px; border: 1px solid #dcdde1;")
        self.lbl_f_val.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.lbl_f_val)
        left_panel.addStretch()

        layout.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>Таблица результатов ЛР2 (Функционирование системы):</b>"))
        self.table_results = QTableWidget(0, 7)
        self.table_results.setHorizontalHeaderLabels(
            ["№", "T_отказа", "пришло", "обраб.", "аннул.", "Σ t_пр", "τ_вос"])
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_panel.addWidget(self.table_results)

        layout.addLayout(right_panel, 3)

    # ----------------------------- RUN LAB1 -----------------------------
    def run_lab1(self):
        try:
            self.sync_ui_to_models()
            self.lab1_model.sigma_coef = self.spin_sigma.value()

            n = self.spin_n.value()
            routes_data = self.get_routes_data()
            sub_idx = self.set_combo.currentIndex()

            # Pi-пресет
            pi_choice = self.combo_pi.currentIndex()
            p_override = None
            if pi_choice > 0:
                p_override = [0.0, 0.3, 0.6, 0.9][pi_choice - 1]

            if sub_idx == 0:
                label = "Регулирование"
                result_key = "Регулирование"
                if not routes_data["Регулирование"]:
                    QMessageBox.warning(self, "Внимание",
                                        "Не заданы маршруты для подтемы «Регулирование».")
                    return
            elif sub_idx == 1:
                label = "Восстановление"
                result_key = "Восстановление"
                if not routes_data["Восстановление"]:
                    QMessageBox.warning(self, "Внимание",
                                        "Не заданы маршруты для подтемы «Восстановление».")
                    return
            else:
                label = "Общее (обе подтемы)"
                result_key = "Общее"
                if not routes_data["Регулирование"] or not routes_data["Восстановление"]:
                    QMessageBox.warning(self, "Внимание",
                                        "Задайте маршруты для обеих подтем.")
                    return

            results = self.lab1_model.simulate_lab1(
                n, p_error_override=p_override, routes_data=routes_data)
            data = np.array(results[result_key])

            if len(data) == 0:
                QMessageBox.warning(self, "Внимание", "Нет данных для симуляции.")
                return

            mean_val = np.mean(data)
            sd_val = np.std(data, ddof=1) if len(data) > 1 else 0.0
            min_val = np.min(data)
            max_val = np.max(data)
            t_sum = np.sum(data)

            # Теоретическое среднее
            if sub_idx in (0, 1):
                sn = "Регулирование" if sub_idx == 0 else "Восстановление"
                mean_theory = self._compute_mean_theory(
                    routes_data[sn], sn, p_override)
            else:
                m1 = self._compute_mean_theory(
                    routes_data["Регулирование"], "Регулирование", p_override)
                m2 = self._compute_mean_theory(
                    routes_data["Восстановление"], "Восстановление", p_override)
                p1, p2 = self.lab1_model.subtopic_probs
                tot = p1 + p2
                if tot <= 0:
                    tot = 1.0
                mean_theory = (m1 * p1 + m2 * p2) / tot

            self.lbl_mean.setText(f"t_ср: {mean_val:.3f}")
            self.lbl_mean_theory.setText(f"t_ср теор.: {mean_theory:.3f}")
            self.lbl_t_sum.setText(f"t_sum: {t_sum:.3f}")
            self.lbl_sd.setText(f"СКО: {sd_val:.3f}")
            self.lbl_min.setText(f"Мин: {min_val:.3f}")
            self.lbl_max.setText(f"Макс: {max_val:.3f}")

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_facecolor('#ffffff')

            manual_k = self.spin_bins.value()
            k = manual_k if manual_k > 0 else int(1 + 3.22 * np.log10(n))
            k = max(1, k)

            n_bins, bins, patches = ax.hist(data, bins=k, color='#8e44ad',
                                            edgecolor='#ffffff', alpha=0.9)
            if len(n_bins) > 0:
                max_idx = np.argmax(n_bins)
                patches[max_idx].set_facecolor('#bb8fce')

            title = f"Гистограмма: {label}"
            if p_override is not None:
                title += f" (Pi = {p_override})"
            ax.set_title(title, fontsize=12, color='#2c3e50')
            ax.set_xlabel("Время диалога", color='#34495e')
            ax.set_ylabel("Частота", color='#34495e')
            ax.grid(axis='y', linestyle='--', alpha=0.4, color='#bdc3c7')

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете: {e}")

    # ----------------------------- RUN LAB2 -----------------------------
    def run_lab2(self):
        try:
            self.sync_ui_to_models()
            routes_data = self.get_routes_data()
            if not routes_data["Регулирование"] or not routes_data["Восстановление"]:
                QMessageBox.warning(self, "Ошибка", "Заполните маршруты для обоих наборов!")
                return

            cycles, total_loss, t_reg, t_rest = self.lab2_model.run_simulation(
                self.spin_lambda1.value(),
                self.spin_lambda2.value(),
                1.0,
                1.0,
                self.spin_iter.value(),
                routes_data,
                rho_1=self.spin_rho1.value(),
                rho_2=self.spin_rho2.value(),
                lr2_mode=self.combo_mode.currentIndex()
            )

            self.lbl_f_val.setText(f"F = {total_loss:.6f}")

            self.table_results.setRowCount(0)
            for row_idx, c in enumerate(cycles[:1000]):
                self.table_results.insertRow(row_idx)
                self.table_results.setItem(row_idx, 0, QTableWidgetItem(str(c['id'])))
                self.table_results.setItem(row_idx, 1, QTableWidgetItem(f"{c['t_fail']:.3f}"))
                self.table_results.setItem(row_idx, 2, QTableWidgetItem(str(c['arrival'])))
                self.table_results.setItem(row_idx, 3, QTableWidgetItem(str(c['processed'])))
                self.table_results.setItem(row_idx, 4,
                                           QTableWidgetItem(str(c['arrival'] - c['processed'])))
                self.table_results.setItem(row_idx, 5, QTableWidgetItem(f"{c['t_proc']:.3f}"))
                self.table_results.setItem(row_idx, 6, QTableWidgetItem(f"{c['t_rec']:.3f}"))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#ffffff"))
    palette.setColor(QPalette.WindowText, QColor("#2c3e50"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#ffffff"))
    palette.setColor(QPalette.Text, QColor("#2c3e50"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#2c3e50"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())