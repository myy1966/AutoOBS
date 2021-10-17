import sys
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QObject,
)
from obswebsocket import obsws, requests
import obswebsocket.exceptions

from const import (
    STATUS_STOPPED,
    STATUS_RECRORDING,
    STATUS_PAUSED,

    CONNECT_FAILED_RET,
    CONNECT_SUCCESS_RET,
)


class ObsWorker(QObject):

    connect_wait_done_sig = pyqtSignal(int)
    ui_update_sig = pyqtSignal(int)

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__()

        self.logger = logger

        self.host = None
        self.port = None
        self.pw = None
        self.ws = obsws(self.host, self.port, self.pw)

        self.recording_flag = False
        self.paused_flag = False
        self.status = "stopped"

    def set_connect(self, host: str, port: int, pw: str) -> None:
        self.host = host
        self.port = port
        self.pw = pw
        self.ws.host = host
        self.ws.port = port
        self.ws.password = pw

    @pyqtSlot()
    def ws_connect(self) -> None:
        try:
            self.ws.connect()
            self._update_status()
            self.connect_wait_done_sig.emit(CONNECT_SUCCESS_RET)
        except obswebsocket.exceptions.ConnectionFailure:
            self.logger.exception("ws_connect: Connection Failed.")
            self.connect_wait_done_sig.emit(CONNECT_FAILED_RET)
        except:
            self.logger.exception("ws_connect: Unexpected error: {}.".format(sys.exc_info()[0]))
            self.connect_wait_done_sig.emit(CONNECT_FAILED_RET)

    def _ws_call(self, req: requests.Baserequests) -> None:
        try:
            self.ws.call(req)
        except obswebsocket.exceptions.MessageTimeout:
            # self.logger.exception("Time:                {}.".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            recording_flag, paused_flag = self.get_status()
            self.logger.exception("ws_call Request:       {}.".format(req.name))
            self.logger.exception("Before call Recording? {}.".format(self.recording_flag))
            self.logger.exception("Before call Paused?    {}.".format(self.paused_flag))
            self.logger.exception("After call Recording?  {}.".format(recording_flag))
            self.logger.exception("After call Paused?     {}.".format(paused_flag))
        except:
            self.logger.exception("ws.call: Unexpected error: {}.".format(sys.exc_info()[0]))

    def _update_status(self) -> None:
        status_flag = self.ws.call(requests.GetRecordingStatus())
        self.recording_flag = status_flag.getIsRecording()
        self.paused_flag = status_flag.getIsRecordingPaused()

        if self.paused_flag:
            self.status = STATUS_PAUSED
        elif self.recording_flag:
            self.status = STATUS_RECRORDING
        else:
            self.status = STATUS_STOPPED

    @pyqtSlot()
    def start(self) -> None:
        self._update_status()
        if self.status == STATUS_STOPPED:
            self.logger.debug("Request starting.")
            self._ws_call(requests.StartRecording())

            self._update_status()
            self.ui_update_sig.emit(STATUS_RECRORDING)

    @pyqtSlot()
    def stop(self) -> None:
        self._update_status()
        if self.status != STATUS_STOPPED:
            self.logger.debug("Request directly stopping.")
            self._ws_call(requests.StopRecording())

            self._update_status()
            self.ui_update_sig.emit(STATUS_STOPPED)

    @pyqtSlot()
    def resume(self) -> None:
        self._update_status()
        if self.status == STATUS_PAUSED:
            self.logger.debug("Request resuming.")
            self._ws_call(requests.ResumeRecording())

            self._update_status()
            self.ui_update_sig.emit(STATUS_RECRORDING)

    @pyqtSlot()
    def pause(self) -> None:
        self._update_status()
        if self.status == STATUS_RECRORDING:
            self.logger.debug("Request pausing.")
            self._ws_call(requests.PauseRecording())

            self._update_status()
            self.ui_update_sig.emit(STATUS_PAUSED)

    @pyqtSlot()
    def resume_or_start(self) -> None:
        self._update_status()
        if self.status == STATUS_PAUSED:
            self.logger.debug("Request resuming in resume_or_start, status is paused.")
            self._ws_call(requests.ResumeRecording())

            self._update_status()
            self.ui_update_sig.emit(STATUS_RECRORDING)
        elif self.status == STATUS_STOPPED:
            self.logger.debug("Request resuming in resume_or_start, status is stopped.")
            self._ws_call(requests.StartRecording())

            self._update_status()
            self.ui_update_sig.emit(STATUS_RECRORDING)

    @pyqtSlot()
    def paused_then_stop(self) -> None:
        self._update_status()
        if self.status == STATUS_PAUSED:
            self.logger.debug("Request stopping when obs is paused.")
            self._ws_call(requests.StopRecording())

            self._update_status()
            self.ui_update_sig.emit(STATUS_STOPPED)
