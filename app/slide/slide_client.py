import socket
import sys, os
import zmq
sys.path.append(os.path.dirname(__file__))
from slide_common import *

class SlideClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://localhost:{PORT}")

    def __del__(self):
        pass

    def set_image(self, image_filename):
        command = SetImage(image_filename)
        self.socket.send_pyobj(command)
        self.socket.recv()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slide_client.py <image_filename>")
        sys.exit(1)

    image_filename = sys.argv[1]
    client = SlideClient()
    client.set_image(image_filename)

