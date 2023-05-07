#!/usr/bin/env python3

from PyQt5.QtWidgets import (
    QApplication, QWidget, QFrame, QLineEdit, QComboBox, QLabel, QPushButton,
    QGridLayout, QDesktopWidget, QScrollArea, QVBoxLayout, QFormLayout,
    QDialog, QDialogButtonBox, QPlainTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt

from libs.core import StructureParser, send_request
from libs.structure import Request, RequestParam


TITLE = "HTTP requests assistant"


class MainWindow(QWidget):
    def __init__(self, exit_callback):
        super().__init__()
        self.exit_callback = exit_callback
        self.structure = StructureParser().structure
        self.init_ui()
        self._center()

    def init_ui(self):
        self.setWindowTitle(TITLE)
        requests_frame = RequestsFrame(self, self.structure.http_requests)
        main_grid = QGridLayout(self)
        main_grid.addWidget(requests_frame, 0, 0)
        self.setLayout(main_grid)
        self.setMaximumWidth(QDesktopWidget().availableGeometry().size().width() - 10)
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
        form_layout.setRowWrapPolicy(form_layout.WrapAllRows)
        # form_layout.setVerticalSpacing(100)

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
        self.query_params_mapping = dict.fromkeys(self.http_request_data.query_params.parsed_keys)
        self.body_mapping = dict.fromkeys(self.http_request_data.body.parsed_keys)
        self.headers_mapping = dict.fromkeys(self.http_request_data.headers.parsed_keys)
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.Panel)
        self.setLineWidth(2)

        url_frame = QFrame(self)
        url_frame_layout = QGridLayout()
        url_title = QLabel("URL:", url_frame)
        url_value = QLineEdit(url_frame)
        url_value.setText(self.http_request_data.url)
        url_value.setReadOnly(True)
        url_frame_layout.addWidget(url_title, 0, 0)
        url_frame_layout.addWidget(url_value, 0, 1)
        url_frame.setFrameShape(QFrame.Panel)
        url_frame.setLineWidth(2)
        url_frame.setFrameShadow(QFrame.Raised)
        url_frame.setLayout(url_frame_layout)

        send_button_top = self._send_button()
        send_button_bottom = self._send_button()

        grid = QGridLayout(self)
        grid.addWidget(send_button_top, 0, 0, alignment=Qt.AlignLeft)
        grid.addWidget(url_frame, 1, 0, 1, 2)

        if self.http_request_data.parsed_url_parts:
            url_parts_frame, url_parts_frame_layout = self._create_ui_block("Adjustable URL parts (in curl braces {}):")
            for number, param in enumerate(self.http_request_data.parsed_url_parts):
                self.url_parts_list.append(ParamRow(self, f"URL part {number + 1}", param))
                url_parts_frame_layout.addWidget(self.url_parts_list[number], number + 1, 0, 1, 2)
            grid.addWidget(url_parts_frame, 2, 0, 1, 2)

        if self.http_request_data.query_params.parsed_keys:
            query_params_frame, query_params_frame_layout = self._create_ui_block("URL query params:")
            for number, param in enumerate(self.http_request_data.query_params.parsed_keys.items()):
                self.query_params_mapping[param[0]] = ParamRow(self, *param)
                query_params_frame_layout.addWidget(self.query_params_mapping[param[0]], number + 1, 0, 1, 2)
            grid.addWidget(query_params_frame, 3, 0, 1, 2)

        if self.http_request_data.headers.parsed_keys:
            headers_frame, headers_frame_layout = self._create_ui_block("Headers:")
            for number, param in enumerate(self.http_request_data.headers.parsed_keys.items()):
                self.headers_mapping[param[0]] = ParamRow(self, *param)
                headers_frame_layout.addWidget(self.headers_mapping[param[0]], number + 1, 0, 1, 2)
            grid.addWidget(headers_frame, 4, 0, 1, 2)

        if self.http_request_data.body.parsed_keys:
            body_frame, body_frame_layout = self._create_ui_block("Body params:")
            for number, param in enumerate(self.http_request_data.body.parsed_keys.items()):
                self.body_mapping[param[0]] = ParamRow(self, *param)
                body_frame_layout.addWidget(self.body_mapping[param[0]], number + 1, 0, 1, 2)
            grid.addWidget(body_frame, 5, 0, 1, 2)

        grid.addWidget(send_button_bottom, 6, 1, alignment=Qt.AlignRight)

        self.setLayout(grid)

    def _create_ui_block(self, title_text: str):
        frame = QFrame(self)
        layout = QGridLayout()
        layout.addWidget(QLabel(title_text, frame), 0, 0, 1, 2)
        frame.setFrameShape(QFrame.Panel)
        frame.setLineWidth(2)
        frame.setFrameShadow(QFrame.Sunken)
        frame.setLayout(layout)
        return frame, layout

    def _send_button(self):
        send_button = QPushButton("Send request", self)
        send_button.clicked.connect(self.send)
        font = send_button.font()
        font.setPointSize(font.pointSize() + 4)
        font.setBold(True)
        send_button.setFont(font)
        return send_button

    def send(self):
        for number, param in enumerate(self.http_request_data.parsed_url_parts):
            param.current_value = self.url_parts_list[number].value
        for key, param in self.http_request_data.query_params.parsed_keys.items():
            param.current_value = self.query_params_mapping[key].value
        for key, param in self.http_request_data.headers.parsed_keys.items():
            param.current_value = self.headers_mapping[key].value
        for key, param in self.http_request_data.body.parsed_keys.items():
            param.current_value = self.body_mapping[key].value

        try:
            result = send_request(self.http_request_data)
        except Exception as err:
            self.show_result(str(err))
        else:
            self.show_result(result)

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
        grid = QGridLayout(self)

        name = QLabel(self.request_param_name, self)
        name.setFrameShape(QFrame.Box)

        if self.request_param.text:
            self._area = QLineEdit(self)
            self._area.setText(self.request_param.text)
        else:
            self._area = QComboBox(self)
            self._area.addItems(map(str, self.request_param.choices))

        self._area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(name, 0, 0, alignment=Qt.AlignLeft)
        grid.addWidget(self._area, 0, 1)
        if self.request_param.description:
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

