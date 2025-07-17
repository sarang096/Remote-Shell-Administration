# Remote Administration Tool (RAT)

This is a lightweight remote administration tool built in Python that allows a server to remotely control a client machine. It supports:

- Command execution
- File upload/download
- Real-time screen sharing

> for educational use only. Do **not** deploy or use without proper authorization. Unauthorized access to computer systems is illegal.

---

## Features

- **Remote Command Execution:** Send shell commands to the client and receive output.
- **File Transfer:** Upload/download files from the client machine.
- **Screen Sharing:** Real-time screen capture from the client, streamed over sockets.

---

## Requirements

- Python 3.8+
- Required libraries:
  ```
  pip install opencv-python mss numpy
  ```
  ## Usage
  ```
  python3
