from enum import IntEnum


CONF_FILE = "conf.toml"
LOG_PATH = "./logs"
DEBUG_FLAG = False

LISTENER_TIMER_TIME = 100
COUNTER_INTVL = 1
COUNTER_BOUND = 10

class OBStatus(IntEnum):
    stopped = 0
    recording = 1
    paused = 2

status_to_str = {
    OBStatus.stopped: "stopped",
    OBStatus.recording: "recording",
    OBStatus.paused: "paused" 
}

CONNECT_FAILED_RET = 101
CONNECT_SUCCESS_RET = 102

WIN_SZ_W = 480
WIN_SZ_H = 160
STATUS_IMG_SZ = 128
