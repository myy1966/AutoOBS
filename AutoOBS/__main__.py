import os
import sys
import time
import logging
import argparse

import toml
from PyQt5.QtCore import QSize, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QSystemTrayIcon,
    QAction,
    QMenu,
    QMessageBox
)

from worker import Counter, CountWorker, ListenWorker
from obs_thread import ObsWorker
from const import *
from resources import resources


app = None


class Window(QMainWindow):

    obs_connect_sig = pyqtSignal()
    obs_start_sig = pyqtSignal()
    obs_stop_sig = pyqtSignal()
    obs_resume_sig = pyqtSignal()
    obs_pause_sig = pyqtSignal()
    obs_resume_or_start_sig = pyqtSignal()
    obs_paused_then_stop_sig = pyqtSignal()

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__()

        self.obs = None
        self.logger = logger

        # load picture resoures
        pixmap_sz = QSize(STATUS_IMG_SZ, STATUS_IMG_SZ)
        # self.stopped_pixmap = QPixmap("images/stopped.png").scaled(pixmap_sz)
        # self.recording_pixmap = QPixmap("images/recording.png").scaled(pixmap_sz)
        # self.paused_pixmap = QPixmap("images/paused.png").scaled(pixmap_sz)
        self.stopped_pixmap = QPixmap(":icons/stopped.png").scaled(pixmap_sz)
        self.recording_pixmap = QPixmap(":icons/recording.png").scaled(pixmap_sz)
        self.paused_pixmap = QPixmap(":icons/paused.png").scaled(pixmap_sz)
        self.pixmaps = [self.stopped_pixmap, self.recording_pixmap, self.paused_pixmap]

        # self.stopped_icon = QIcon("images/stopped.png")
        # self.recording_icon = QIcon("images/recording.png")
        # self.paused_icon = QIcon("images/paused.png")
        self.stopped_icon = QIcon(":icons/stopped.png")
        self.recording_icon = QIcon(":icons/recording.png")
        self.paused_icon = QIcon(":icons/paused.png")
        self.icons = [self.stopped_icon, self.recording_icon, self.paused_icon]

        # set window
        self.resize(WIN_SZ_W, WIN_SZ_H)
        self.setWindowTitle("AutoOBS")
        self.setWindowIcon(self.stopped_icon)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # set layout
        outer_layout = QVBoxLayout()

        # set status layout
        status_layout = QHBoxLayout()

        # set an image to represent status
        self.status = QLabel(self)
        self.status.resize(STATUS_IMG_SZ, STATUS_IMG_SZ)

        # status images
        self.status.setPixmap(self.stopped_pixmap)

        status_layout.addStretch()
        status_layout.addWidget(self.status)
        status_layout.addStretch()

        # set option layout
        option_layout = QHBoxLayout()

        # button group 1: start and stop
        opt_ss_layout = QVBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.manual_start)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.manual_stop)
        opt_ss_layout.addWidget(self.start_btn)
        opt_ss_layout.addWidget(self.stop_btn)

        # button group 2: resume and pause
        opt_rp_layout = QVBoxLayout()
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.manual_resume)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.manual_pause)
        opt_rp_layout.addWidget(self.resume_btn)
        opt_rp_layout.addWidget(self.pause_btn)

        # button group 3: manual and auto
        opt_ma_layout = QVBoxLayout()
        self.auto_btn = QPushButton("Auto")
        self.auto_btn.clicked.connect(self.trigger_auto_mode)
        self.manual_btn = QPushButton("Manual")
        self.manual_btn.clicked.connect(self.trigger_manual_mode)
        opt_ma_layout.addWidget(self.auto_btn)
        opt_ma_layout.addWidget(self.manual_btn)
    
        option_layout.addLayout(opt_ss_layout)
        option_layout.addStretch()
        option_layout.addLayout(opt_rp_layout)
        option_layout.addStretch()
        option_layout.addLayout(opt_ma_layout)

        outer_layout.addLayout(status_layout)
        outer_layout.addLayout(option_layout)

        central_widget.setLayout(outer_layout)

        # set tray

        # set tray action
        self.start_action = QAction("Start", self)
        self.stop_action = QAction("Stop", self)
        self.resume_action = QAction("Resume", self)
        self.pause_action = QAction("Pause", self)
        self.auto_action = QAction("Auto", self)
        self.manual_action = QAction("Manual", self)
        self.exit_action = QAction("Exit", self)
        self.start_action.triggered.connect(self.manual_start)
        self.stop_action.triggered.connect(self.manual_stop)
        self.resume_action.triggered.connect(self.manual_resume)
        self.pause_action.triggered.connect(self.manual_pause)
        self.auto_action.triggered.connect(self.trigger_auto_mode)
        self.manual_action.triggered.connect(self.trigger_manual_mode)
        self.exit_action.triggered.connect(app.quit)

        # set tray menu
        tray_menu = QMenu()
        tray_menu.addAction(self.start_action)
        tray_menu.addAction(self.stop_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.resume_action)
        tray_menu.addAction(self.pause_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.auto_action)
        tray_menu.addAction(self.manual_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.exit_action)

        # set tray configurations
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.stopped_icon)
        self.tray.setVisible(True)
        self.tray.setContextMenu(tray_menu)
        # self.tray.show()

        # set tray click action
        self.tray.activated.connect(self.onTrayIconActivated)
        self.disambiguateTimer = QTimer(self)
        self.disambiguateTimer.setSingleShot(True)
        self.disambiguateTimer.timeout.connect(self.disambiguateTimerTimeout)

        self.error_msg = QMessageBox()
        self.error_msg.setWindowIcon(self.stopped_icon)
        self.error_msg.setWindowTitle("Error!")
        self.error_msg.setIcon(QMessageBox.Critical)
        self.error_msg.setText("Error!")
        self.error_msg.setInformativeText("Error!")
        self.error_msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort)
        self.error_msg.setDefaultButton(QMessageBox.Retry)

        self.waiting_msg = QMessageBox()
        self.waiting_msg.setWindowIcon(self.stopped_icon)
        self.waiting_msg.setWindowTitle("Waiting")
        self.waiting_msg.setIcon(QMessageBox.Information)
        self.waiting_msg.setText("Waiting")
        self.waiting_msg.setInformativeText("Connecting to the Obs Studio...")
        self.waiting_msg.setStandardButtons(QMessageBox.Abort)
        self.waiting_msg.setDefaultButton(QMessageBox.Abort)

        self.obs_worker = None
        self.obs_thread = None
        self.counter = None
        self.count_thread = None
        self.count_worker = None
        self.listen_thread = None
        self.listen_worker = None

    def initial(self) -> None:
        # start obs thread
        self.obs_thread = QThread()
        self.obs_worker = ObsWorker(self.logger)

        self.obs_worker.connect_wait_done_sig.connect(self.waiting_msg.done)
        self.obs_worker.ui_update_sig.connect(lambda status: self.update_ui(status))
        self.obs_connect_sig.connect(self.obs_worker.ws_connect)
        self.obs_start_sig.connect(self.obs_worker.start)
        self.obs_stop_sig.connect(self.obs_worker.stop)
        self.obs_resume_sig.connect(self.obs_worker.resume)
        self.obs_pause_sig.connect(self.obs_worker.pause)
        self.obs_resume_or_start_sig.connect(self.obs_worker.resume_or_start)
        self.obs_paused_then_stop_sig.connect(self.obs_worker.paused_then_stop)

        self.obs_worker.moveToThread(self.obs_thread)
        # self.obs_thread.started.connect(self.obs_worker.run)
        self.obs_thread.finished.connect(app.exit)
        self.obs_thread.start()

        while True:
            if not os.path.isfile(CONF_FILE):
                self.show_error_message("Configuration file (conf.toml) not found!")
            else:
                conf = toml.load(CONF_FILE)
                try:
                    host = conf["OBS"]["host"]
                    port = conf["OBS"]["port"]
                    pw = conf["OBS"]["password"]

                    if "AutoOBS" in conf:
                        if "listener_timer_time" in conf["AutoOBS"]:
                            global LISTENER_TIMER_TIME
                            LISTENER_TIMER_TIME = conf["AutoOBS"]["listener_timer_time"]
                        if "counter_interval" in conf["AutoOBS"]:
                            global COUNTER_INTVL
                            COUNTER_INTVL = conf["AutoOBS"]["counter_interval"]
                        if "counter_bound" in conf["AutoOBS"]:
                            global COUNTER_BOUND
                            COUNTER_BOUND = conf["AutoOBS"]["counter_bound"]
                except KeyError as e:
                    self.show_error_message("Configuration Key \"{}\" does not exist!".format(e.args[0]))

            self.obs_worker.set_connect(host, port, pw)

            self.obs_connect_sig.emit()

            ret = self.show_waiting_message()
            if ret == CONNECT_FAILED_RET:
                self.show_error_message("Can not connect to the Obs Studio!")
            else:
                break

        # set counter
        self.counter = Counter(COUNTER_BOUND, self.logger)

        # set count thread
        self.count_thread = QThread()
        self.count_worker = CountWorker(COUNTER_INTVL, self.counter, self.logger)
        self.count_worker.pause.connect(self.auto_pause)
        self.count_worker.stop.connect(self.auto_stop)
        self.count_worker.moveToThread(self.count_thread)
        self.count_thread.started.connect(self.count_worker.run)
        self.count_thread.finished.connect(app.exit)
        self.count_thread.start()

        # set listen thread
        self.listen_thread = QThread()
        self.listen_worker = ListenWorker(self.counter, self.logger)
        self.listen_worker.resume_sig.connect(self.auto_resume)
        self.listen_worker.moveToThread(self.listen_thread)
        self.listen_thread.started.connect(self.listen_worker.run)
        self.listen_thread.finished.connect(app.exit)
        self.listen_thread.start()

        # initial mode: auto
        self.trigger_auto_mode()

    def show_error_message(self, info: str) -> None:
        # self.logger.info("Begin error_message.")

        # self.error_msg = QMessageBox()
        # obs_icon = QIcon("images/idle.png")
        # self.error_msg.setWindowIcon(obs_icon)
        # self.error_msg.setWindowTitle("Error!")
        # self.error_msg.setIcon(QMessageBox.Critical)
        # self.error_msg.setText("Error!")
        # self.error_msg.setInformativeText(info)
        # self.error_msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort)
        # self.error_msg.setDefaultButton(QMessageBox.Retry)

        # self.logger.info("Set error_message over.")

        self.error_msg.setInformativeText(info)

        ret = self.error_msg.exec()
        if ret == QMessageBox.Abort:
            sys.exit(app.exit())

    def show_waiting_message(self) -> int:
        # self.logger.info("Begin waiting_message.")

        # self.waiting_msg = QMessageBox()
        # obs_icon = QIcon("images/idle.png")
        # self.waiting_msg.setWindowIcon(obs_icon)
        # self.waiting_msg.setWindowTitle("Error!")
        # self.waiting_msg.setIcon(QMessageBox.Critical)
        # self.waiting_msg.setText("Error!")
        # self.waiting_msg.setInformativeText(info)
        # self.waiting_msg.setStandardButtons(QMessageBox.Abort)
        # self.waiting_msg.setDefaultButton(QMessageBox.Abort)

        # self.logger.info("Set waiting_message over.")

        ret = self.waiting_msg.exec()
        if ret == QMessageBox.Abort:
            sys.exit(app.exit())

        return ret

    # override closeEvent to implement closing to tray
    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()

    def onTrayIconActivated(self, reason) -> None:
        print("onTrayIconActivated:", reason)
        if reason == QSystemTrayIcon.Trigger:
            self.disambiguateTimer.start(app.doubleClickInterval())
        elif reason == QSystemTrayIcon.DoubleClick:
            self.disambiguateTimer.stop()

            self.logger.debug("Tray icon double clicked.")
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def disambiguateTimerTimeout(self) -> None:
        self.logger.debug("Tray icon single clicked.")

    def set_title(self, status: int) -> None:
        self.setWindowTitle("AutoOBS | " + self.run_mode + " | " + status_to_str[status])

    @pyqtSlot()
    def update_ui(self, status: int) -> None:
        self.status.setPixmap(self.pixmaps[status])
        self.tray.setIcon(self.icons[status])
        self.set_title(status)

    # remote set obs and change status
    def _start(self) -> None:
        self.obs_start_sig.emit()
        # self.update_ui(UI_STATUS_RECRORDING)

    def _stop(self) -> None:
        self.obs_stop_sig.emit()
        # self.update_ui(UI_STATUS_STOPPED)

    def _resume(self) -> None:
        self.obs_resume_sig.emit()
        # self.update_ui(UI_STATUS_RECRORDING)

    def _pause(self) -> None:
        self.obs_pause_sig.emit()
        # self.update_ui(UI_STATUS_PAUSED)

    def _paused_then_stop(self) -> None:
        self.obs_paused_then_stop_sig.emit()
        # self.update_ui(UI_STATUS_STOPPED)

    def _resume_or_start(self):
        self.obs_resume_or_start_sig.emit()
        # self.update_ui(UI_STATUS_RECRORDING)

    # methods for auto mode
    @pyqtSlot()
    def auto_resume(self) -> None:
        if self.run_mode == "auto":
            self._resume_or_start()

    @pyqtSlot()
    def auto_pause(self) -> None:
        if self.run_mode == "auto":
            self._pause()

    @pyqtSlot()
    def auto_stop(self) -> None:
        if self.run_mode == "auto":
            self._paused_then_stop()

    # methods for manual mode
    def manual_start(self) -> None:
        if self.run_mode == "manual":
            self._start()

    def manual_resume(self) -> None:
        if self.run_mode == "manual":
            self._resume()

    def manual_pause(self) -> None:
        if self.run_mode == "manual":
            self._pause()

    def manual_stop(self) -> None:
        if self.run_mode == "manual":
            self._stop()

    # change to auto mode
    def trigger_auto_mode(self) -> None:
        self.run_mode = "auto"
        self.update_ui(self.obs_worker.status)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.auto_btn.setEnabled(False)
        self.manual_btn.setEnabled(True)

        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(False)
        self.resume_action.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.auto_action.setEnabled(False)
        self.manual_action.setEnabled(True)

    # change to manual mode
    def trigger_manual_mode(self) -> None:
        self.run_mode = "manual"
        self.update_ui(self.obs_worker.status)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.resume_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        self.auto_btn.setEnabled(True)
        self.manual_btn.setEnabled(False)

        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(True)
        self.resume_action.setEnabled(True)
        self.pause_action.setEnabled(True)
        self.auto_action.setEnabled(True)
        self.manual_action.setEnabled(False)


def main():
    # arg
    m_parser = argparse.ArgumentParser(prog='AutoOBS',
                                        description='')
    m_parser.add_argument('--debug', action='store_true')
    args = m_parser.parse_args()

    # get logging level
    if args.debug:
        logger_level = "DEBUG"
    else:
        logger_level = "INFO"

    # set logging
    if not os.path.isdir(LOG_PATH):
        os.mkdir(LOG_PATH)

    logger = logging.getLogger("AutoOBS")
    logger.setLevel(logger_level)
    log_filename = os.path.join(LOG_PATH, "{}.log".format(time.strftime("%Y-%m-%d_%H-%M-%S")))
    log_file_handler = logging.FileHandler(log_filename, mode='a', encoding="utf-8")
    log_file_handler.setLevel(logger_level)
    log_formatter = logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    log_file_handler.setFormatter(log_formatter)
    logger.addHandler(log_file_handler)

    global app
    app = QApplication(sys.argv)
    window = Window(logger)
    window.show()
    window.initial()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
