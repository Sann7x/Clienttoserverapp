import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def receive():
    while True:
        try:
            msg = client.recv(4096).decode()
            if msg:
                print("\n" + msg)
        except:
            print("[CLIENT] Disconnected from server")
            client.close()
            break

def send_file(path):
    if os.path.exists(path):
        filename = os.path.basename(path)
        filesize = os.path.getsize(path)

        client.send(f"FILE:{filename}".encode())
        response = client.recv(1024).decode()
        if response != "READY":
            print("[CLIENT] Server not ready to receive file size.")
            return

        client.send(str(filesize).encode())
        response = client.recv(1024).decode()
        if response != "READY":
            print("[CLIENT] Server not ready to receive file data.")
            return

        with open(path, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                client.send(chunk)

        print(f"[CLIENT] File '{filename}' sent successfully.")
    else:
        print("[CLIENT] File not found.")

def authenticate():
    while True:
        mode = input("Type 'login' or 'register': ").strip().lower()
        if mode not in ['login', 'register']:
            print("Invalid mode, please type 'login' or 'register'")
            continue
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        auth_msg = f"AUTH:{mode}:{username}:{password}"
        client.send(auth_msg.encode())

        response = client.recv(1024).decode()
        if response == "OK":
            print(f"[CLIENT] {mode} successful. Welcome, {username}!")
            return username
        else:
            print(f"[CLIENT] Authentication failed: {response}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                client.close()
                exit()

def write():
    while True:
        msg = input()
        if msg.startswith("/file"):
            try:
                _, path = msg.split(maxsplit=1)
                threading.Thread(target=send_file, args=(path,), daemon=True).start()
            except ValueError:
                print("Usage: /file path/to/file.jpg")
        else:
            try:
                client.send(msg.encode())
            except:
                print("[CLIENT] Failed to send message.")
                break

if __name__ == "__main__":
    authenticate()
    threading.Thread(target=receive, daemon=True).start()
    write()
