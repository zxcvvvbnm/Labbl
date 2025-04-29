import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QMessageBox, QFileDialog, QInputDialog
)
from datetime import datetime
import re  # Для проверки формата даты


class Measurement:
    """Базовый класс для измерений температуры."""

    def __init__(self, status, date, location, value):
        self.status = status  # Статус измерения (например, "Нормальное измерение")
        self.date = date  # Дата измерения в строковом формате
        self.location = location  # Место измерения
        self.value = float(value)  # Значение температуры, приведенное к float

    def to_table_row(self):
        """Преобразует поля объекта в список для отображения в таблице."""
        return [self.status, self.date, self.location, f"{self.value:.2f}"]


class NormalMeasurement(Measurement):
    """Представляет нормальное измерение температуры."""

    def __init__(self, date, location, value, sensor_type):
        super().__init__("Нормальное измерение", date, location, value)  # Вызов конструктора базового класса
        self.sensor_type = sensor_type  # Тип датчика

    def to_table_row(self):
        return super().to_table_row() + [self.sensor_type]  # Добавление типа датчика в таблицу


class AbnormalMeasurement(Measurement):
    """Представляет аномальное измерение температуры."""

    def __init__(self, date, location, value, reason):
        super().__init__("Аномальное измерение", date, location, value)  # Установка статуса как аномального
        self.reason = reason  # Причина аномалии

    def to_table_row(self):
        return super().to_table_row() + [self.reason]  # Добавление причины в таблицу


class MeasurementParser:
    """Класс для парсинга данных измерений из файла."""

    @staticmethod
    def validate_date(date_str):
        """Проверяет, соответствует ли строка формату dd.mm.yyyy."""
        pattern = r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$"
        if not re.match(pattern, date_str):
            raise ValueError("Неверный формат даты. Ожидается формат dd.mm.yyyy.")
        return True

    @staticmethod
    def parse_line(line):
        fields = line.strip().split(";")  # Разделение строки по символу ';'
        if len(fields) < 5:
            raise ValueError("Недостаточно данных в строке.")

        # Проверка и преобразование даты
        MeasurementParser.validate_date(fields[1])
        date = datetime.strptime(fields[1], "%d.%m.%Y").strftime("%d-%m-%Y")

        location = fields[2]  # Место измерения
        value = float(fields[3])  # Значение температуры

        if fields[0] == "Нормальное измерение":
            return NormalMeasurement(date, location, value, fields[4])  # Создание нормального измерения
        elif fields[0] == "Аномальное измерение":
            return AbnormalMeasurement(date, location, value, fields[4])  # Создание аномального измерения
        else:
            raise ValueError("Неизвестный тип измерения.")

    @staticmethod
    def load_measurements_from_file(path):
        measurements = []
        with open(path, "r", encoding="cp1251") as file:  # Открытие файла в кодировке Windows-1251
            for line in file:
                measurement = MeasurementParser.parse_line(line)  # Парсинг каждой строки
                measurements.append(measurement)  # Добавление объекта в список
        return measurements


class MainWindow(QWidget):
    """Главное окно графического интерфейса приложения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Измерения температуры")  # Заголовок окна
        self.setGeometry(200, 200, 800, 400)  # Размер и позиция окна

        self.measurements = []  # Список всех загруженных измерений

        self.table = QTableWidget()  # Таблица для отображения данных
        self.table.setColumnCount(5)  # Установка количества колонок
        self.table.setHorizontalHeaderLabels([
            "Тип", "Дата", "Место", "Значение", "Детали"
        ])

        self.load_button = QPushButton("Загрузить файл")
        self.load_button.clicked.connect(self.load_file)  # Обработчик кнопки загрузки

        self.add_button = QPushButton("Добавить измерение")
        self.add_button.clicked.connect(self.add_measurement)  # Обработчик кнопки добавления

        self.delete_button = QPushButton("Удалить выделенное")
        self.delete_button.clicked.connect(self.delete_selected)  # Обработчик кнопки удаления

        button_layout = QHBoxLayout()  # Горизонтальная компоновка кнопок
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)

        layout = QVBoxLayout()  # Главная вертикальная компоновка
        layout.addLayout(button_layout)
        layout.addWidget(self.table)

        self.setLayout(layout)  # Установка главного layout

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть CSV файл", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.measurements = MeasurementParser.load_measurements_from_file(file_path)  # Загрузка измерений
                self.update_table()  # Обновление таблицы
            except Exception as e:
                self.show_error(f"Ошибка при загрузке: {e}")  # Обработка ошибки загрузки

    def update_table(self):
        self.table.setRowCount(0)  # Очистка таблицы
        for measurement in self.measurements:
            row_position = self.table.rowCount()  # Позиция новой строки
            self.table.insertRow(row_position)  # Добавление строки
            for col, value in enumerate(measurement.to_table_row()):
                self.table.setItem(row_position, col, QTableWidgetItem(value))  # Заполнение ячеек

    def add_measurement(self):
        types = ["Нормальное", "Аномальное"]
        type_choice, ok = QInputDialog.getItem(self, "Тип измерения", "Выберите тип:", types, 0, False)
        if not ok:
            return

        date, ok1 = QInputDialog.getText(self, "Дата", "Введите дату (дд.мм.гггг):")
        location, ok2 = QInputDialog.getText(self, "Место", "Введите место измерения:")
        value, ok3 = QInputDialog.getDouble(self, "Значение", "Введите значение температуры:")

        if not (ok1 and ok2 and ok3):
            return

        detail_label = "Тип датчика" if type_choice == "Нормальное" else "Причина"
        detail, ok4 = QInputDialog.getText(self, detail_label, f"Введите {detail_label.lower()}:")

        if not ok4:
            return

        try:
            # Проверка даты
            MeasurementParser.validate_date(date)
            formatted_date = datetime.strptime(date, "%d.%m.%Y").strftime("%d-%m-%Y")  # Форматирование даты

            if type_choice == "Нормальное":
                measurement = NormalMeasurement(formatted_date, location, value, detail)  # Создание нормального измерения
            else:
                measurement = AbnormalMeasurement(formatted_date, location, value, detail)  # Создание аномального измерения

            self.measurements.append(measurement)  # Добавление в список
            self.update_table()  # Обновление таблицы
        except Exception as e:
            self.show_error(f"Ошибка при добавлении: {e}")  # Обработка ошибки

    def delete_selected(self):
        selected_row = self.table.currentRow()  # Получение текущей строки
        if selected_row >= 0:
            self.measurements.pop(selected_row)  # Удаление из списка
            self.update_table()  # Обновление таблицы

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)  # Показ сообщения об ошибке


def main():
    app = QApplication(sys.argv)  # Создание приложения Qt
    window = MainWindow()  # Создание основного окна
    window.show()  # Отображение окна
    sys.exit(app.exec())  # Запуск цикла обработки событий


if __name__ == "__main__":
    main()  # Точка входа в программу
