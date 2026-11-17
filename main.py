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
from PyQt5.QtGui import QColor, QIntValidator
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models import Lab1Model, Lab2Model
from data_loader import load_matrix_from_txt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моделирование диалоговых систем")
        self.resize(1200, 800)

        self.lab1_model = Lab1Model()
        self.lab2_model = Lab2Model(self.lab1_model)

        self.setStyleSheet("""
            QMainWindow { background-color: #f4f6f9; }
            QWidget { color: #2c3e50; font-family: 'Segoe UI', Arial; font-size: 10pt; }
            QGroupBox { border: 2px solid #dcdde1; border-radius: 8px; margin-top: 15px; background: #ffffff; padding-top: 20px; font-weight: bold; color: #8e44ad; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #ffffff; border: 1px solid #bdc3c7; padding: 5px; border-radius: 4px; color: #2c3e50; }
            QLineEdit:focus, QSpinBox:focus { border: 2px solid #8e44ad; }
            QPushButton { background: #8e44ad; color: white; border: none; padding: 10px 15px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background: #9b59b6; }
            QPushButton:pressed { background: #732d91; }
            QTableWidget { background-color: #ffffff; border: 1px solid #dcdde1; gridline-color: #f1f2f6; border-radius: 4px; }
            QHeaderView::section { background-color: #f8f9fa; border: none; border-bottom: 2px solid #bdc3c7; font-weight: bold; padding: 6px; color: #34495e; }
            QListWidget { background: #ffffff; border: none; border-right: 2px solid #dcdde1; outline: 0; }
            QListWidget::item { padding: 15px 10px; border-bottom: 1px solid #f1f2f6; color: #7f8c8d; font-weight: bold; }
            QListWidget::item:selected { background: #f4ecf7; color: #8e44ad; border-left: 4px solid #8e44ad; }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.addItems(["1. Ввод данных", "2. Статистика", "3. Эффективность"])

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

        self.sidebar.setCurrentRow(0)

    def init_data_page(self):
        layout = QVBoxLayout(self.page_data)

        load_panel = QHBoxLayout()
        btn_load_1 = QPushButton("Загрузить файл для Подтемы 1")
        btn_load_1.clicked.connect(lambda: self.load_file_to_gui("Регулирование"))
        btn_load_2 = QPushButton("Загрузить файл для Подтемы 2")
        btn_load_2.clicked.connect(lambda: self.load_file_to_gui("Восстановление"))

        load_panel.addWidget(btn_load_1)
        load_panel.addWidget(btn_load_2)
        load_panel.addStretch()
        layout.addLayout(load_panel)

        group_routes = QGroupBox("Матрица маршрутов диалога (0 = конец маршрута)")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        routes_widget = QWidget()
        routes_layout = QHBoxLayout(routes_widget)
        routes_layout.setContentsMargins(0, 0, 0, 0)

        self.route_inputs = {"Регулирование": [], "Восстановление": []}

        def create_subtopic_block(title, subtopic_name):
            vbox = QVBoxLayout()
            vbox.addWidget(QLabel(f"<b>{title}</b>"))

            grid = QGridLayout()
            grid.setSpacing(5)
            grid.setColumnStretch(11, 1)

            for row_idx in range(10):
                lbl = QLabel(f"М{row_idx + 1}")
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                grid.addWidget(lbl, row_idx, 0)

                row_boxes = []
                for col_idx in range(10):
                    le = QLineEdit()
                    le.setFixedWidth(35)
                    le.setAlignment(Qt.AlignCenter)
                    le.setValidator(QIntValidator(0, 99))
                    le.setText("0")

                    grid.addWidget(le, row_idx, col_idx + 1)
                    row_boxes.append(le)

                self.route_inputs[subtopic_name].append(row_boxes)

            vbox.addLayout(grid)
            vbox.addStretch()
            return vbox

        routes_layout.addLayout(create_subtopic_block("Подтема 1 (Регулирование)", "Регулирование"))
        routes_layout.addLayout(create_subtopic_block("Подтема 2 (Восстановление)", "Восстановление"))

        scroll.setWidget(routes_widget)
        group_layout = QVBoxLayout()
        group_layout.addWidget(scroll)
        group_routes.setLayout(group_layout)
        layout.addWidget(group_routes, 3)

        bottom_layout = QHBoxLayout()

        group_probs = QGroupBox("Вероятности подтем")
        prob_layout = QFormLayout()
        self.spin_sub_prob1 = QDoubleSpinBox()
        self.spin_sub_prob1.setRange(0, 1)
        self.spin_sub_prob1.setSingleStep(0.1)
        self.spin_sub_prob1.setValue(0.5)

        self.spin_sub_prob2 = QDoubleSpinBox()
        self.spin_sub_prob2.setRange(0, 1)
        self.spin_sub_prob2.setSingleStep(0.1)
        self.spin_sub_prob2.setValue(0.5)

        prob_layout.addRow("P(Регулирование):", self.spin_sub_prob1)
        prob_layout.addRow("P(Восстановление):", self.spin_sub_prob2)
        group_probs.setLayout(prob_layout)
        bottom_layout.addWidget(group_probs, 1)

        group_steps = QGroupBox("Характеристики шагов (Время / P ошибки)")
        steps_layout = QVBoxLayout()
        self.table_steps = QTableWidget(4, 2)
        self.table_steps.setHorizontalHeaderLabels(["Время (с)", "P ошибки"])
        self.table_steps.verticalHeader().setVisible(True)
        self.table_steps.setVerticalHeaderLabels(["Шаг 1", "Шаг 2", "Шаг 3", "Шаг 4"])

        default_times = [2, 5, 0, 0]
        default_errors = [0.25, 0.05, 0.17, 0.12]
        for i in range(4):
            self.table_steps.setItem(i, 0, QTableWidgetItem(str(default_times[i])))
            self.table_steps.setItem(i, 1, QTableWidgetItem(str(default_errors[i])))

        self.table_steps.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        steps_layout.addWidget(self.table_steps)
        group_steps.setLayout(steps_layout)
        bottom_layout.addWidget(group_steps, 2)
        layout.addLayout(bottom_layout, 2)

    def load_file_to_gui(self, subtopic_name):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getOpenFileName(
            self, f"Выберите txt файл для {subtopic_name}", "", "Text Files (*.txt);;All Files (*)", options=options
        )

        if filepath:
            matrix = load_matrix_from_txt(filepath)
            if not matrix:
                QMessageBox.warning(self, "Ошибка", "Файл пуст или имеет неверный формат.")
                return

            boxes = self.route_inputs[subtopic_name]

            for r in range(len(boxes)):
                for c in range(len(boxes[r])):
                    boxes[r][c].setText("0")

            for r, route in enumerate(matrix):
                if r >= len(boxes): break
                for c, val in enumerate(route):
                    if c >= len(boxes[r]): break
                    boxes[r][c].setText(str(val))

            QMessageBox.information(self, "Успех", f"Данные для {subtopic_name} успешно загружены!")

    def init_hist_page(self):
        layout = QHBoxLayout(self.page_hist)
        control_panel = QVBoxLayout()

        group_params = QGroupBox("Параметры симуляции")
        form_layout = QFormLayout()

        self.spin_n = QSpinBox()
        self.spin_n.setRange(100, 1000000)
        self.spin_n.setValue(10000)
        self.spin_n.setSingleStep(1000)

        self.combo_pi = QComboBox()
        self.combo_pi.addItems(["0.0", "0.3", "0.6", "0.9", "Из таблицы"])

        # ДОБАВЛЕНО: Поле для ручного ввода количества интервалов
        self.spin_bins = QSpinBox()
        self.spin_bins.setRange(0, 100)
        self.spin_bins.setValue(0)
        self.spin_bins.setSpecialValueText("Авто (по формуле)")

        form_layout.addRow("Выборка (N):", self.spin_n)
        form_layout.addRow("Вер. ошибки (Pi):", self.combo_pi)
        form_layout.addRow("Интервалы (K):", self.spin_bins)  # ДОБАВЛЕНО

        self.btn_run_lab1 = QPushButton("Построить гистограмму")
        self.btn_run_lab1.clicked.connect(self.run_lab1)
        form_layout.addRow(self.btn_run_lab1)

        group_params.setLayout(form_layout)
        control_panel.addWidget(group_params)

        group_stats = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        # ДОБАВЛЕНО: Отдельные метрики для подтем
        self.lbl_mean_reg = QLabel("Ср. время (Регулирование): -")
        self.lbl_mean_rest = QLabel("Ср. время (Восстановление): -")
        self.lbl_mean_total = QLabel("Ср. время (Тема всего): -")
        self.lbl_std = QLabel("Отклонение: -")

        self.lbl_mean_reg.setStyleSheet("color: #2c3e50; font-size: 10pt;")
        self.lbl_mean_rest.setStyleSheet("color: #2c3e50; font-size: 10pt;")
        self.lbl_mean_total.setStyleSheet("color: #8e44ad; font-weight: bold; font-size: 11pt;")

        stats_layout.addWidget(self.lbl_mean_reg)
        stats_layout.addWidget(self.lbl_mean_rest)
        stats_layout.addWidget(self.lbl_mean_total)
        stats_layout.addWidget(self.lbl_std)

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

    def init_sim_page(self):
        layout = QHBoxLayout(self.page_sim)

        left_panel = QVBoxLayout()
        group_sys = QGroupBox("Параметры потоков")
        form_layout = QFormLayout()

        self.spin_lambda1 = QDoubleSpinBox()
        self.spin_lambda1.setRange(0.1, 100.0)
        self.spin_lambda1.setValue(15.0)

        self.spin_lambda2 = QDoubleSpinBox()
        self.spin_lambda2.setRange(0.001, 100.0)
        self.spin_lambda2.setValue(0.02)

        self.spin_r1 = QDoubleSpinBox()
        self.spin_r1.setRange(1, 10000)
        self.spin_r1.setValue(10)

        self.spin_r2 = QDoubleSpinBox()
        self.spin_r2.setRange(1, 10000)
        self.spin_r2.setValue(100)

        self.spin_iter = QSpinBox()
        self.spin_iter.setRange(10, 10000)
        self.spin_iter.setValue(50)

        form_layout.addRow("Запросы (λ1):", self.spin_lambda1)
        form_layout.addRow("Отказы (λ2):", self.spin_lambda2)
        form_layout.addRow("Потери R1:", self.spin_r1)
        form_layout.addRow("Потери R2:", self.spin_r2)
        form_layout.addRow("Итераций:", self.spin_iter)

        self.btn_run_lab2 = QPushButton("Запустить симуляцию")
        self.btn_run_lab2.clicked.connect(self.run_lab2)
        form_layout.addRow(self.btn_run_lab2)

        group_sys.setLayout(form_layout)
        left_panel.addWidget(group_sys)

        self.lbl_total_loss = QLabel("Общие потери: -")
        self.lbl_total_loss.setStyleSheet(
            "font-size: 12pt; font-weight: bold; color: #c0392b; padding: 10px; background: #fff; border-radius: 5px; border: 1px solid #dcdde1;")
        self.lbl_total_loss.setAlignment(Qt.AlignCenter)

        # ДОБАВЛЕНО: Средние потери на запрос
        self.lbl_avg_loss = QLabel("Ср. потери на запрос: -")
        self.lbl_avg_loss.setStyleSheet(
            "font-size: 10pt; font-weight: bold; color: #e67e22; padding: 5px;")
        self.lbl_avg_loss.setAlignment(Qt.AlignCenter)

        left_panel.addWidget(self.lbl_total_loss)
        left_panel.addWidget(self.lbl_avg_loss)  # ДОБАВЛЕНО
        left_panel.addStretch()

        layout.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>Журнал событий:</b>"))
        self.table_results = QTableWidget(0, 5)
        self.table_results.setHorizontalHeaderLabels(["№", "Приход", "Конец", "Статус", "Потери"])
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_panel.addWidget(self.table_results)

        layout.addLayout(right_panel, 3)

    def get_routes_data(self):
        routes = {"Регулирование": [], "Восстановление": []}
        for sub_name in routes:
            for row_boxes in self.route_inputs[sub_name]:
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
                    routes[sub_name].append(route)
        return routes

    def run_lab1(self):
        try:
            n = self.spin_n.value()
            pi_text = self.combo_pi.currentText()
            self.lab1_model.subtopic_probs = [self.spin_sub_prob1.value(), self.spin_sub_prob2.value()]

            p_override = None if pi_text == "Из таблицы" else float(pi_text)
            routes_data = self.get_routes_data()

            results = self.lab1_model.simulate_lab1(n, p_override, routes_data)

            if not results["Общее"]:
                QMessageBox.warning(self, "Внимание", "Нет данных для симуляции. Проверьте маршруты.")
                return

            data = np.array(results["Общее"])
            data_reg = np.array(results["Регулирование"])
            data_rest = np.array(results["Восстановление"])

            # Вывод статистики (обновлено)
            mean_reg = np.mean(data_reg) if len(data_reg) > 0 else 0
            mean_rest = np.mean(data_rest) if len(data_rest) > 0 else 0

            self.lbl_mean_reg.setText(f"Ср. время (Регулирование): {mean_reg:.2f} с")
            self.lbl_mean_rest.setText(f"Ср. время (Восстановление): {mean_rest:.2f} с")
            self.lbl_mean_total.setText(f"Ср. время (Тема всего): {np.mean(data):.2f} с")
            self.lbl_std.setText(f"Отклонение: {np.std(data):.2f} с")

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_facecolor('#ffffff')

            # Расчет количества интервалов
            manual_k = self.spin_bins.value()
            if manual_k > 0:
                k = manual_k
            else:
                k = int(1 + 3.22 * np.log10(n))
                if k < 5: k = 5

            n_bins, bins, patches = ax.hist(data, bins=k, color='#9b59b6', edgecolor='#ffffff', alpha=0.9)

            max_idx = np.argmax(n_bins)
            patches[max_idx].set_facecolor('#ff69b4')

            ax.set_title("Распределение времени", fontsize=12, color='#2c3e50')
            ax.set_xlabel("Время, сек", color='#34495e')
            ax.set_ylabel("Частота", color='#34495e')
            ax.grid(axis='y', linestyle='--', alpha=0.4, color='#bdc3c7')
            for spine in ax.spines.values():
                spine.set_color('#bdc3c7')

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете: {e}")

    def run_lab2(self):
        try:
            routes_data = self.get_routes_data()
            if not routes_data["Регулирование"] or not routes_data["Восстановление"]:
                QMessageBox.warning(self, "Ошибка", "Заполните маршруты для обеих подтем!")
                return

            logs, total_loss, t_reg, t_rest = self.lab2_model.run_simulation(
                self.spin_lambda1.value(),
                self.spin_lambda2.value(),
                self.spin_r1.value(),
                self.spin_r2.value(),
                self.spin_iter.value(),
                routes_data
            )

            # Вывод метрик
            self.lbl_total_loss.setText(f"Общие потери: {total_loss:.2f}")

            # ДОБАВЛЕНО: Расчет средних потерь на запрос
            avg_loss = total_loss / len(logs) if logs else 0
            self.lbl_avg_loss.setText(f"Ср. потери на запрос: {avg_loss:.2f}")

            self.lbl_total_loss.setToolTip(
                f"Ср. время регулирования: {t_reg:.2f} с\nСр. время восстановления: {t_rest:.2f} с")

            self.table_results.setRowCount(0)
            for row_idx, log in enumerate(logs):
                self.table_results.insertRow(row_idx)

                self.table_results.setItem(row_idx, 0, QTableWidgetItem(str(log['id'])))
                self.table_results.setItem(row_idx, 1, QTableWidgetItem(f"{log['arrival']:.3f}"))
                self.table_results.setItem(row_idx, 2, QTableWidgetItem(f"{log['end']:.3f}"))

                status_item = QTableWidgetItem(log['status'])
                if log['status'] == "выполнена":
                    status_item.setForeground(QColor("#27ae60"))
                else:
                    status_item.setForeground(QColor("#c0392b"))
                self.table_results.setItem(row_idx, 3, status_item)

                self.table_results.setItem(row_idx, 4, QTableWidgetItem(f"{log['loss']:.2f}"))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())