import socket
import threading
import auth
import contacts

HOST = '127.0.0.1'
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
usernames = {}  # client_socket: username

print(f"[SERVER] Listening on {HOST}:{PORT}")

def broadcast(message, sender):
    for client in clients:
        if client != sender:
            try:
                client.send(message)
            except:
                remove_client(client)

def remove_client(client):
    if client in clients:
        username = usernames.get(client, "Unknown")
        print(f"[SERVER] Removing client {username}")
        clients.remove(client)
        if client in usernames:
            del usernames[client]
        client.close()

def handle_client(client):
    username = None
    try:
        # Authentication loop
        auth_success = False
        while not auth_success:
            msg = client.recv(1024).decode()
            if not msg:
                remove_client(client)
                return

            if msg.startswith("AUTH:"):
                parts = msg.split(":", 3)
                if len(parts) != 4:
                    client.send("ERROR:Bad auth format".encode())
                    continue

                _, mode, user, pwd = parts

                if mode == "register":
                    success = auth.register_user(user, pwd)
                    if success:
                        client.send("OK".encode())
                    else:
                        client.send("ERROR:User already exists".encode())

                elif mode == "login":
                    success = auth.authenticate_user(user, pwd)
                    if success:
                        client.send("OK".encode())
                        username = user
                        auth_success = True
                    else:
                        client.send("ERROR:Invalid username or password".encode())
                else:
                    client.send("ERROR:Invalid auth mode".encode())

            else:
                client.send("ERROR:Authentication required".encode())

        # Post-auth: add client to lists
        usernames[client] = username
        clients.append(client)
        contacts.load_contacts()
        print(f"[SERVER] User '{username}' authenticated and connected")
        client.send(f"Welcome {username}!".encode())

        # Main loop for messages and commands
        while True:
            msg = client.recv(4096)
            if not msg:
                break

            if msg.startswith(b"FILE:"):
                filename = msg.decode().split(":", 1)[1]
                client.send("READY".encode())
                filesize = int(client.recv(1024).decode())
                client.send("READY".encode())

                with open(f"server_received_{filename}", "wb") as f:
                    bytes_read = 0
                    while bytes_read < filesize:
                        chunk = client.recv(min(4096, filesize - bytes_read))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_read += len(chunk)

                print(f"[SERVER] Received file '{filename}' from {username}")
                client.send(f"File {filename} received successfully.".encode())

            else:
                text = msg.decode()
                print(f"[SERVER] Received from {username}: {text}")

                if text.startswith("/"):
                    parts = text.split(maxsplit=2)
                    command = parts[0].lower()

                    if command == "/addcontact" and len(parts) == 2:
                        result = contacts.add_contact(username, parts[1])
                        client.send(result.encode())

                    elif command == "/delcontact" and len(parts) == 2:
                        result = contacts.remove_contact(username, parts[1])
                        client.send(result.encode())

                    elif command == "/mycontacts":
                        clist = contacts.get_contacts(username)
                        client.send(f"Your contacts: {', '.join(clist)}".encode())

                    elif command == "/msg" and len(parts) == 3:
                        recipient, message = parts[1], parts[2]
                        sent = False
                        for c, uname in usernames.items():
                            if uname == recipient:
                                c.send(f"[DM from {username}] {message}".encode())
                                sent = True
                                break
                        if not sent:
                            client.send(f"User {recipient} not found or offline.".encode())

                    else:
                        client.send("Unknown command or wrong format.".encode())

                else:
                    broadcast(f"[{username}] {text}".encode(), client)

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        remove_client(client)

def receive():
    while True:
        client, addr = server.accept()
        print(f"[SERVER] Connection from {addr}")
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()

if __name__ == "__main__":
    receive()
