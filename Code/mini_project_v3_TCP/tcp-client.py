import socket
import random
import signal
import sys

TCP_HOST = "127.0.0.1"
TCP_PORT = 5000

# Flag to control server loop
running = True

def signal_handler(sig, frame):
    global running
    print("\nGracefully shutting down TCP Ranking Server...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def start_tcp_ranking_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((TCP_HOST, TCP_PORT))
        server.listen()
        server.settimeout(1.0)  # 1 second timeout on accept()
        print(f"TCP Ranking Server running on {TCP_HOST}:{TCP_PORT}")

        while running:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                # Timeout allows to check 'running' flag regularly
                continue
            except Exception as e:
                print(f"Server accept error: {e}")
                break

            with conn:
                print(f"Connected by {addr}")
                conn.settimeout(1.0)  # Timeout on recv() as well
                try:
                    request = conn.recv(1024).decode().strip()
                    if request == "GET_RANKING":
                        ranking = random.randint(1, 100)
                        conn.sendall(str(ranking).encode())
                except socket.timeout:
                    print("Recv timed out, closing connection.")
                except Exception as e:
                    print(f"Connection error: {e}")

    print("Server has shut down.")

if __name__ == "__main__":
    start_tcp_ranking_server()
