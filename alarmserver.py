#!/usr/bin/env python3

import logging
import threading
import socket
import socketserver
import time

import RPi.GPIO as GPIO
    
alarm = threading.Event()

class RequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(2)
        try:
            data = self.request.recv(32).strip()
        except socket.timeout:
            data = None

        if data == b'alarm':
            logging.info(f"Received valid alarm from {self.client_address[0]}")
            if alarm.is_set():
                logging.info("Alarm already in progress")
            else:
                alarm.set()
        else:
            logging.warning(f"Received invalid message from {self.client_address[0]}: {data}")

class Server(threading.Thread):
    def __init__(self):
        super().__init__()
        self.server = socketserver.TCPServer(("0.0.0.0", 8080), RequestHandler)
        
    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()

def sound_alarm(channel, duration=30, frequency=2, duty_cycle=0.5):
    """Sounds the an alarm connected to the raspberry pi's GPIO

    channel: The GPIO channel that the buzzer is connected to
    duration: The duration that the alarm will sound for
    frequency: The amount of times the buzzer will be activated per second (Hz)
    duty_cycle: The amount of time within a period that the buzzer is on 
        relative to the time that it is off.

    Example: A frequency of 5Hz and duty_cycle of 0.5 will result in the buzzer
        being on for 100ms and then off for 100ms.
    """
    period = 1 / frequency
    on = period * duty_cycle
    off = period - on

    for _ in range(frequency * duration):
        GPIO.output(channel, GPIO.HIGH)
        time.sleep(on)
        GPIO.output(channel, GPIO.LOW)
        time.sleep(off)

if __name__ == "__main__":
    channel = 11
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(channel, GPIO.OUT, initial=GPIO.LOW)
    logging.basicConfig(filename="log", format="%(asctime)s %(levelname)s: %(message)s", 
            datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
    server = Server()
    server.start()
    try:
        logging.info("Server started")
        while True:
            alarm.wait()
            sound_alarm(channel)
            alarm.clear()
    except KeyboardInterrupt:
        server.shutdown() 
        server.join()
        logging.info("Server shutdown")
