from PyQt5.QtWidgets import (
    QApplication, QWidget, QFrame, QLineEdit, QComboBox, QLabel, QPushButton,
    QGridLayout, QDesktopWidget, QScrollArea, QVBoxLayout, QFormLayout,
    QDialog, QDialogButtonBox, QPlainTextEdit
)
from PyQt5.QtCore import Qt

from core import StructureParser, send_request
from structure import Request, RequestParam


class MainWindow(QWidget):
    def __init__(self, exit_callback):
        super().__init__()
        self.exit_callback = exit_callback
        self.config = StructureParser()
        self.init_ui()
        self._center()

    def init_ui(self):
        self.setWindowTitle("Universal QA helper")
        requests_frame = RequestsFrame(self, self.config.structure.http_requests)
        main_grid = QGridLayout(self)
        main_grid.addWidget(requests_frame, 0, 0)
        self.setLayout(main_grid)
        self.show()

    def _center(self):
        width = QDesktopWidget().availableGeometry().size().width() // 100 * 75
        height = QDesktopWidget().availableGeometry().size().height() // 100 * 75
        self.setGeometry(0, 0, width, height)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class RequestsFrame(QFrame):
    """Frame with all HTTP requests."""
    def __init__(self, parent, http_requests: dict[str, Request]):
        super().__init__(parent)
        self.http_requests = http_requests
        self.init_ui()

    def init_ui(self):
        form_layout = QFormLayout()
        for item in self.http_requests.values():
            form_layout.addRow(item.name, HTTPRequestFrame(self, item))

        group_box = QFrame()
        group_box.setLayout(form_layout)
        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setWidget(group_box)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)


class HTTPRequestFrame(QFrame):
    """HTTP request configure area."""
    def __init__(self, parent, http_request_data: Request):
        super().__init__(parent)
        self.http_request_data = http_request_data
        # Container for graphical objects of corresponding request params:
        self.url_parts_list = []
        self.query_params_mapping = dict.fromkeys(self.http_request_data.parsed_query_params)
        self.body_mapping = dict.fromkeys(self.http_request_data.parsed_body)
        self.headers_mapping = dict.fromkeys(self.http_request_data.parsed_headers)
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.Panel)
        title = QLabel(self.http_request_data.name, self)

        url_title = QLabel("URL:", self)
        url_value = QLineEdit(self)
        url_value.setText(self.http_request_data.url)
        url_value.setReadOnly(True)

        url_frame = QFrame(self)
        url_frame_layout = QGridLayout()
        url_frame_layout.addWidget(url_title, 0, 0)
        url_frame_layout.addWidget(url_value, 0, 1)
        url_frame.setLayout(url_frame_layout)

        send_button = QPushButton("Send", self)
        send_button.clicked.connect(self.send)

        grid = QGridLayout(self)
        grid.addWidget(title, 0, 0)
        grid.addWidget(send_button, 0, 1, alignment=Qt.AlignRight)
        grid.addWidget(url_frame, 1, 0, 1, 2)
        start = 2
        for number, param in enumerate(self.http_request_data.parsed_url_parts, start=start):
            self.url_parts_list.append(ParamRow(self, f"URL adjustable part {number - start + 1}", param))
            grid.addWidget(self.url_parts_list[number - start], number, 0, 1, 2)
        start = len(self.url_parts_list) + start
        for number, param in enumerate(self.http_request_data.parsed_query_params.items(), start=start+1):
            self.query_params_mapping[param[0]] = ParamRow(self, *param)
            grid.addWidget(self.query_params_mapping[param[0]], number, 0, 1, 2)
            start = number
        for number, param in enumerate(self.http_request_data.parsed_headers.items(), start=start+1):
            self.headers_mapping[param[0]] = ParamRow(self, *param)
            grid.addWidget(self.headers_mapping[param[0]], number, 0, 1, 2)
            start = number
        for number, param in enumerate(self.http_request_data.parsed_body.items(), start=start+1):
            self.body_mapping[param[0]] = ParamRow(self, *param)
            grid.addWidget(self.body_mapping[param[0]], number, 0, 1, 2)
        self.setLayout(grid)

    def send(self):
        for number, param in enumerate(self.http_request_data.parsed_url_parts):
            param.current_value = self.url_parts_list[number].value
        for key, param in self.http_request_data.parsed_query_params.items():
            param.current_value = self.query_params_mapping[key].value
        for key, param in self.http_request_data.parsed_headers.items():
            param.current_value = self.headers_mapping[key].value
        for key, param in self.http_request_data.parsed_body.items():
            param.current_value = self.body_mapping[key].value
        self.show_result(send_request(self.http_request_data))

    def show_result(self, data: str):
        result_dialogue = QDialog(self)
        result_dialogue.setWindowTitle(f'Response for "{self.http_request_data.name}"')

        text_area = QPlainTextEdit(result_dialogue)
        text_area.setReadOnly(True)
        text_area.setPlainText(data)

        buttons = QDialogButtonBox.Ok
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(result_dialogue.accept)

        layout = QVBoxLayout()
        layout.addWidget(text_area)
        layout.addWidget(button_box)
        result_dialogue.setLayout(layout)

        center_dialogue_window(result_dialogue, self)
        result_dialogue.show()


class ParamRow(QFrame):
    """HTTP request parameter value area."""
    def __init__(self, parent, request_param_name: str, request_param: RequestParam):
        super().__init__(parent)
        self.request_param_name = request_param_name
        self.request_param = request_param
        self._area = None
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.Box)
        grid = QGridLayout(self)
        self.setFrameShape(QFrame.NoFrame)

        name = QLabel(self.request_param_name, self)
        name.setFrameShape(QFrame.Box)

        if self.request_param.text:
            self._area = QLineEdit(self)
            self._area.setText(self.request_param.text)
        else:
            self._area = QComboBox(self)
            self._area.addItems(map(str, self.request_param.choices))

        grid.addWidget(name, 0, 0, alignment=Qt.AlignLeft)
        grid.addWidget(self._area, 0, 1)
        descr_title = QLabel("Description:", self)
        descr_value = QLineEdit(self)
        descr_value.setText(self.request_param.description)
        descr_value.setDisabled(True)
        grid.addWidget(descr_title, 1, 0, alignment=Qt.AlignLeft)
        grid.addWidget(descr_value, 1, 1)

        self.setLayout(grid)

    @property
    def value(self):
        """Returns adjustable parameter's value"""
        if isinstance(self._area, QLineEdit):
            return self._area.text()
        elif isinstance(self._area, QComboBox):
            return self.request_param.choices[self._area.currentIndex()]


def center_dialogue_window(widget, source_widget):
    pos_x = source_widget.frameGeometry().x()
    pos_y = source_widget.frameGeometry().y()
    width = source_widget.frameGeometry().width() // 100 * 50
    height = source_widget.frameGeometry().height() // 100 * 50
    widget.setGeometry(pos_x, pos_y, width, height)
    widget.move(pos_x + 50, pos_y + 50)


if __name__ == "__main__":
    app = QApplication([])
    gui = MainWindow(app.exit)
    app.exec()

