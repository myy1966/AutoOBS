import time
import datetime
import logging

import pynput
from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QObject,
    QMutex,
    QTimer
)


class Counter:

    def __init__(self, bound: int, logger: logging.Logger) -> None:
        self.logger = logger

        self.bound = bound
        self.count = bound
        self.overflow = False
        self.mutex = QMutex()

    def reset(self) -> None:
        self.mutex.lock()
        self.count = self.bound
        self.overflow = False
        self.mutex.unlock()

    def dec(self) -> None:
        if self.overflow == False:
            self.mutex.lock()
            self.count -= 1
            if self.count == 0:
                self.overflow = True
            self.mutex.unlock()


class CountWorker(QObject):

    pause = pyqtSignal()
    stop = pyqtSignal()

    def __init__(self, intvl: int, counter: Counter, logger: logging.Logger) -> None:
        super().__init__()

        self.logger = logger

        self.intvl = intvl
        self.counter = counter

    def check_time(self) -> bool:
        if datetime.time(23, 59, 55) < datetime.datetime.now().time() < datetime.time(23, 59, 59) \
            or datetime.time(0, 59, 55) < datetime.datetime.now().time() < datetime.time(0, 59, 59) \
            or datetime.time(1, 59, 55) < datetime.datetime.now().time() < datetime.time(1, 59, 59):
            return True
        else:
            return False

    @pyqtSlot()
    def run(self) -> None:
        while (True):
            time.sleep(self.intvl)

            self.logger.debug("Counter number: {}.".format(self.counter.count))

            if self.counter.overflow:
                self.logger.debug("Counter overflow.")
                if self.check_time():
                    self.logger.debug("Time to midnight, emit stop.")

                    self.stop.emit()
                else:
                    self.logger.debug("Normal time, emit pause.")

                    self.pause.emit()
            else:
                self.counter.dec()


from const import LISTENER_TIMER_TIME

class ListenWorker(QObject):

    resume_sig = pyqtSignal()
    timer_start_sig = pyqtSignal()

    def __init__(self, counter: Counter, logger: logging.Logger) -> None:
        super().__init__()

        self.logger = logger

        self.counter = counter

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_timeout)
        self.timer_start_sig.connect(self.timer_start)
        self.timeout_flag = False
        self.timer.start(LISTENER_TIMER_TIME)

    def on_event(self) -> None:
        if self.timeout_flag:
            self.logger.debug("Reset counter and emit resume.")

            self.timer_start_sig.emit()

            self.counter.reset()
            self.resume_sig.emit()
        else:
            self.logger.debug("Reset counter and emit resume.")

    def on_press(self, key) -> None:
        self.logger.debug("Key {} pressed.".format(key))
        self.on_event()

    def on_release(self, key) -> None:
        self.logger.debug("Key {} released.".format(key))
        self.on_event()

    def on_move(self, x, y) -> None:
        self.logger.debug("Mouse moved to ({}, {}).".format(x, y))
        self.on_event()

    def on_click(self, x, y, button, pressed) -> None:
        self.logger.debug("Mouse button {} {} on ({}, {})."
                            .format(button, "pressed" if pressed else "released", x, y))
        self.on_event()

    def on_scroll(self, x, y, dx, dy) -> None:
        self.logger.debug("Mouse scrolled to ({}, {}), dx, dy: ({}, {})."
                            .format(x, y, dx, dy))
        self.on_event()

    def timer_start(self) -> None:
        self.timeout_flag = False
        self.timer.start(LISTENER_TIMER_TIME)

    def timer_timeout(self) -> None:
        self.timeout_flag = True

    @pyqtSlot()
    def run(self) -> None:
        key_listener = pynput.keyboard.Listener(on_press=self.on_press,
                                                on_release=self.on_release)
        mouse_listener = pynput.mouse.Listener(on_move=self.on_move,
                                               on_click=self.on_click,
                                               on_scroll=self.on_scroll)
        
        key_listener.start()
        mouse_listener.start()

        # key_listener.join()
        # mouse_listener.join()
