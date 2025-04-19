from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox,
    QComboBox, QCheckBox, QTextEdit
)
from PyQt5.QtCore import Qt

import config_manager

class AddEditCommandDialog(QDialog):
    def __init__(self, parent=None, title="", keyword="", cmd_type="app", data=""):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Command")

        self.title_edit = QLineEdit(title)
        self.keyword_edit = QLineEdit(keyword)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["app", "browser_search", "browser_control"])
        self.type_combo.setCurrentText(cmd_type)

        self.data_label = QLabel("Executable Path:")  # default for "app"
        self.data_edit = QLineEdit(data)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_data)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["open", "new_tab", "incognito"])
        self.action_combo.hide()

        self.type_combo.currentTextChanged.connect(self.on_type_change)
        self.on_type_change(self.type_combo.currentText())

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(self.title_edit)
        layout.addWidget(QLabel("Keyword (unique):"))
        layout.addWidget(self.keyword_edit)
        layout.addWidget(QLabel("Command Type:"))
        layout.addWidget(self.type_combo)
        layout.addWidget(self.data_label)
        layout.addWidget(self.data_edit)
        layout.addWidget(self.action_combo)
        layout.addWidget(self.browse_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def on_type_change(self, new_type):
        if new_type == "app":
            self.data_label.setText("Executable Path:")
            self.data_edit.show()
            self.browse_button.show()
            self.action_combo.hide()
        elif new_type == "browser_search":
            self.data_label.setText("URL Template (use {query}):")
            self.data_edit.show()
            self.browse_button.hide()
            self.action_combo.hide()
        elif new_type == "browser_control":
            self.data_label.setText("Action:")
            self.data_edit.hide()
            self.browse_button.hide()
            self.action_combo.show()

    def browse_data(self):
        if self.type_combo.currentText() == "app":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Executable", "", "Executable Files (*.exe);;All Files (*)"
            )
            if file_path:
                self.data_edit.setText(file_path)

    def get_data(self):
        title = self.title_edit.text().strip()
        keyword = self.keyword_edit.text().strip()
        cmd_type = self.type_combo.currentText()
        if cmd_type in ("app", "browser_search"):
            data = self.data_edit.text().strip()
        else:
            data = self.action_combo.currentText()
        return title, keyword, cmd_type, data


class SettingsDialog(QDialog):
    def __init__(self, parent=None,
                 current_trigger_key="]",
                 speaker_enabled=False,
                 enrollments=None,
                 active_enrollment=""):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        if enrollments is None:
            enrollments = {}

        # Trigger key
        self.trigger_key_edit = QLineEdit(current_trigger_key)

        # Speaker recognition toggle
        self.speaker_checkbox = QCheckBox("Enable Speaker Recognition")
        self.speaker_checkbox.setChecked(speaker_enabled)

        # Enrollment selector
        self.enrollment_combo = QComboBox()
        self.enrollment_combo.addItems(list(enrollments.keys()))
        if active_enrollment in enrollments:
            self.enrollment_combo.setCurrentText(active_enrollment)
        self.enrollment_combo.setEnabled(speaker_enabled)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Global Trigger Key (default is ']'):"))
        layout.addWidget(self.trigger_key_edit)
        layout.addWidget(self.speaker_checkbox)
        layout.addWidget(QLabel("Select Speaker Enrollment:"))
        layout.addWidget(self.enrollment_combo)

        self.speaker_checkbox.stateChanged.connect(self.on_speaker_toggle)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def on_speaker_toggle(self, state):
        self.enrollment_combo.setEnabled(state == Qt.Checked)

    def get_settings(self):
        return {
            "trigger_key": self.trigger_key_edit.text().strip(),
            "speaker_enabled": self.speaker_checkbox.isChecked(),
            "active_enrollment": self.enrollment_combo.currentText()
        }


class ShowCommandsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Viable Commands")
        layout = QVBoxLayout()
        commands_text = ""

        try:
            config = config_manager.load_config()
        except Exception:
            config = {}

        if config.get("main_browser"):
            default_commands = [
                {"title": "Search", "keyword": "search", "type": "browser_search",
                 "data": "https://www.google.com/search?q={query}"},
                {"title": "Wikipedia", "keyword": "wikipedia", "type": "browser_search",
                 "data": "https://en.wikipedia.org/wiki/{query}"},
                {"title": "Browser", "keyword": "browser", "type": "browser_control", "data": "open"},
                {"title": "New Tab", "keyword": "new tab", "type": "browser_control", "data": "new_tab"},
                {"title": "Incognito", "keyword": "incognito", "type": "browser_control", "data": "incognito"}
            ]
            for cmd in default_commands:
                commands_text += f"Type '{cmd['keyword']}' to {cmd['title']} (Default)\n"

        for cmd in config.get("commands", []):
            commands_text += f"Type '{cmd['keyword']}' to {cmd.get('title','')} (Custom)\n"

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(commands_text)
        layout.addWidget(text_edit)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        self.setLayout(layout)
