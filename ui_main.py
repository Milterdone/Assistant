from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QDialog, QInputDialog
)

import config_manager
from dialogs import AddEditCommandDialog, SettingsDialog, ShowCommandsDialog
from voice_assistant import VoiceAssistantThread
import subprocess
import os
import sounddevice as sd
import wave
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant App")
        self.resize(900,600)

        self.config = config_manager.load_config()

        # Start voice thread
        self.voice_thread = VoiceAssistantThread()
        self.voice_thread.log_signal.connect(self.append_log)
        self.voice_thread.start()

        main_widget = QWidget()
        main_layout = QHBoxLayout()

        left = QWidget()
        left_layout = QVBoxLayout()

        self.add_cmd_button = QPushButton("Add New Command")
        self.add_cmd_button.clicked.connect(self.add_command)
        self.edit_cmd_button = QPushButton("Edit Selected Command")
        self.edit_cmd_button.clicked.connect(self.edit_command)
        self.delete_cmd_button = QPushButton("Delete Selected Command")
        self.delete_cmd_button.clicked.connect(self.delete_command)
        self.select_browser_button = QPushButton("Select Browser as Main")
        self.select_browser_button.clicked.connect(self.select_browser)
        self.show_commands_button = QPushButton("Show Viable Commands")
        self.show_commands_button.clicked.connect(self.show_commands)
        self.play_last_button = QPushButton("Play Last Recording")
        self.play_last_button.clicked.connect(self.play_last_recording)
        self.enroll_button = QPushButton("Enroll Speaker")
        self.enroll_button.clicked.connect(self.enroll_speaker)
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        self.manual_record_button = QPushButton("Manual Record (Debug)")
        self.manual_record_button.clicked.connect(self.manual_record)

        for w in [
            self.add_cmd_button, self.edit_cmd_button,
            self.delete_cmd_button, self.select_browser_button,
            self.show_commands_button, self.play_last_button,
            self.enroll_button, self.settings_button,
            self.manual_record_button
        ]:
            left_layout.addWidget(w)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        left_layout.addWidget(self.log_console)
        left.setLayout(left_layout)

        right = QWidget()
        right_layout = QVBoxLayout()
        self.cmd_table = QTableWidget(0,4)
        self.cmd_table.setHorizontalHeaderLabels(["Title","Keyword","Type","Data"])
        self.cmd_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.refresh_cmd_table()
        right_layout.addWidget(self.cmd_table)
        right.setLayout(right_layout)

        main_layout.addWidget(left,1)
        main_layout.addWidget(right,2)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def append_log(self, msg):
        self.log_console.append(msg)

    def refresh_cmd_table(self):
        cfg = config_manager.load_config()
        cmds = cfg.get("commands",[])
        self.cmd_table.setRowCount(len(cmds))
        for i,cmd in enumerate(cmds):
            self.cmd_table.setItem(i,0,QTableWidgetItem(cmd.get("title","")))
            self.cmd_table.setItem(i,1,QTableWidgetItem(cmd.get("keyword","")))
            self.cmd_table.setItem(i,2,QTableWidgetItem(cmd.get("type","")))
            self.cmd_table.setItem(i,3,QTableWidgetItem(cmd.get("data","")))

    def add_command(self):
        dlg = AddEditCommandDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            title,kw,tp,data = dlg.get_data()
            if not kw:
                QMessageBox.warning(self,"Error","Keyword is required.")
                return
            if not title:
                title="untitled"
            entry={"title":title,"keyword":kw,"type":tp,"data":data}
            try:
                config_manager.add_command_entry(entry)
                self.append_log(f"Added command: {title}")
                self.refresh_cmd_table()
            except ValueError as e:
                QMessageBox.warning(self,"Error",str(e))

    def edit_command(self):
        row = self.cmd_table.currentRow()
        if row<0:
            QMessageBox.warning(self,"Error","No command selected.")
            return
        cfg = config_manager.load_config()
        entry = cfg.get("commands",[])[row]
        dlg = AddEditCommandDialog(
            self,
            title=entry.get("title",""),
            keyword=entry.get("keyword",""),
            cmd_type=entry.get("type","app"),
            data=entry.get("data","")
        )
        if dlg.exec_()==QDialog.Accepted:
            title,kw,tp,data = dlg.get_data()
            if not kw:
                QMessageBox.warning(self,"Error","Keyword is required.")
                return
            try:
                config_manager.update_command_entry(row,{"title":title,"keyword":kw,"type":tp,"data":data})
                self.append_log(f"Updated command: {title}")
                self.refresh_cmd_table()
            except ValueError as e:
                QMessageBox.warning(self,"Error",str(e))

    def delete_command(self):
        row = self.cmd_table.currentRow()
        if row<0:
            QMessageBox.warning(self,"Error","No command selected.")
            return
        if QMessageBox.Yes == QMessageBox.question(self,"Confirm Delete","Delete selected command?"):
            try:
                config_manager.delete_command_entry(row)
                self.append_log("Deleted command.")
                self.refresh_cmd_table()
            except Exception as e:
                QMessageBox.warning(self,"Error",str(e))

    def select_browser(self):
        path, _ = QFileDialog.getOpenFileName(self,"Select Browser Executable","","*.exe;;All Files (*)")
        if path:
            config_manager.set_main_browser(path)
            self.append_log("Browser set to: "+path)

    def show_commands(self):
        ShowCommandsDialog(self).exec_()

    def play_last_recording(self):
        if os.path.exists("last_recording.wav"):
            try:
                if os.name=='nt': os.startfile("last_recording.wav")
                else: subprocess.Popen(["xdg-open","last_recording.wav"])
                self.append_log("Playing last recording.")
            except Exception as e:
                QMessageBox.warning(self,"Error","Cannot play: "+str(e))
        else:
            QMessageBox.warning(self,"Error","No recording found.")

    def enroll_speaker(self):
        name, ok = QInputDialog.getText(self,"Speaker Enrollment","Enter speaker name:")
        if not ok or not name.strip(): return
        name=name.strip()
        duration=20
        self.append_log(f"Recording enrollment '{name}' ({duration}s)...")
        try:
            audio = sd.rec(int(44100*duration),samplerate=44100,channels=1)
            sd.wait()
            path=f"enroll_{name}.wav"
            with wave.open(path,"wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes((audio*32767).astype(np.int16).tobytes())
            config_manager.add_enrollment(name,path)
            config_manager.set_active_enrollment(name)
            self.voice_thread.update_speaker_settings(True,path)
            self.append_log(f"Enrollment saved: {path}")
        except Exception as e:
            self.append_log("Enrollment error: "+str(e))

    def open_settings(self):
        cfg = config_manager.load_config()
        dlg = SettingsDialog(
            self,
            current_trigger_key=cfg.get("trigger_key","]"),
            speaker_enabled=cfg.get("speaker_recognition_enabled",False),
            enrollments=cfg.get("enrollments",{}),
            active_enrollment=cfg.get("active_enrollment","")
        )
        if dlg.exec_() == QDialog.Accepted:
            s=dlg.get_settings()
            if s["trigger_key"]:
                config_manager.set_trigger_key(s["trigger_key"])
                self.voice_thread.update_trigger_key(s["trigger_key"])
            config_manager.set_speaker_recognition_enabled(s["speaker_enabled"])
            config_manager.set_active_enrollment(s["active_enrollment"])
            path = config_manager.load_config().get("enrollments",{}).get(s["active_enrollment"],"")
            self.voice_thread.update_speaker_settings(s["speaker_enabled"],path)
            self.append_log("Settings updated.")

    def manual_record(self):
        self.append_log("Manual record (5s)...")
        try:
            audio = sd.rec(int(44100*5),samplerate=44100,channels=1)
            sd.wait()
            with wave.open("manual_recording.wav","wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes((audio*32767).astype(np.int16).tobytes())
            self.append_log("Saved manual_recording.wav")
        except Exception as e:
            self.append_log("Manual record error: "+str(e))
