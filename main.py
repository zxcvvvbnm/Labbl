import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QMessageBox, QFileDialog, QInputDialog
)
from datetime import datetime


class Measurement:
    """Base class for temperature measurements."""

    def __init__(self, status, date, location, value):
        self.status = status
        self.date = date
        self.location = location
        self.value = float(value)

    def to_table_row(self):
        """Convert object fields to a list for table display."""
        return [self.status, self.date, self.location, f"{self.value:.2f}"]


class NormalMeasurement(Measurement):
    """Represents a normal temperature measurement."""

    def __init__(self, date, location, value, sensor_type):
        super().__init__("Нормальное измерение", date, location, value)
        self.sensor_type = sensor_type

    def to_table_row(self):
        return super().to_table_row() + [self.sensor_type]


class AbnormalMeasurement(Measurement):
    """Represents an abnormal temperature measurement."""

    def __init__(self, date, location, value, reason):
        super().__init__("Аномальное измерение", date, location, value)
        self.reason = reason

    def to_table_row(self):
        return super().to_table_row() + [self.reason]


class MeasurementParser:
    """Parses measurement data from file."""

    @staticmethod
    def parse_line(line):
        fields = line.strip().split(";")
        if len(fields) < 5:
            raise ValueError("Недостаточно данных в строке.")

        date = datetime.strptime(fields[1], "%d.%m.%Y").strftime("%d-%m-%Y")
        location = fields[2]
        value = float(fields[3])

        if fields[0] == "Нормальное измерение":
            return NormalMeasurement(date, location, value, fields[4])
        elif fields[0] == "Аномальное измерение":
            return AbnormalMeasurement(date, location, value, fields[4])
        else:
            raise ValueError("Неизвестный тип измерения.")

    @staticmethod
    def load_measurements_from_file(path):
        measurements = []
        with open(path, "r", encoding="cp1251") as file:
            for line in file:
                measurement = MeasurementParser.parse_line(line)
                measurements.append(measurement)
        return measurements


class MainWindow(QWidget):
    """Main GUI window for the application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Измерения температуры")
        self.setGeometry(200, 200, 800, 400)

        self.measurements = []

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Тип", "Дата", "Место", "Значение", "Детали"
        ])

        self.load_button = QPushButton("Загрузить файл")
        self.load_button.clicked.connect(self.load_file)

        self.add_button = QPushButton("Добавить измерение")
        self.add_button.clicked.connect(self.add_measurement)

        self.delete_button = QPushButton("Удалить выделенное")
        self.delete_button.clicked.connect(self.delete_selected)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть CSV файл", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.measurements = MeasurementParser.load_measurements_from_file(file_path)
                self.update_table()
            except Exception as e:
                self.show_error(f"Ошибка при загрузке: {e}")

    def update_table(self):
        self.table.setRowCount(0)
        for measurement in self.measurements:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            for col, value in enumerate(measurement.to_table_row()):
                self.table.setItem(row_position, col, QTableWidgetItem(value))

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
            formatted_date = datetime.strptime(date, "%d.%m.%Y").strftime("%d-%m-%Y")
            if type_choice == "Нормальное":
                measurement = NormalMeasurement(formatted_date, location, value, detail)
            else:
                measurement = AbnormalMeasurement(formatted_date, location, value, detail)

            self.measurements.append(measurement)
            self.update_table()
        except Exception as e:
            self.show_error(f"Ошибка при добавлении: {e}")

    def delete_selected(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            self.measurements.pop(selected_row)
            self.update_table()

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
