
## Transmitter Project

### Description
Develop a simple sender/receiver program using python to transmit files over a network using tcp socket streams.

The sender program will read a file, divide it into smaller chunks, and transmit the chunks to the receiver
over a socket connection. The receiver program will receive the chunks, reassemble them, and write the data back into a new file.

The project will demonstrate how to handle command line argument parsing, network communication, packet fragmentation, and error detection,
focusing on using sockets to manage the lower-level transmission of data.

### Usage
    `transmitter.py send <filename> <ip> <port>`
    `transmitter.py recv <ip> <port>`

### Notes
- Must use Git/Github for version control
- Cannot use external libraries, only Python standard library
- Must handle command line arguments

"""python

#!/usr/bin/env python3
import argparse
import os
import socket
import sys
from pathlib import Path

CHUNK_SIZE = 8192  # 8KB chunks

def send_file(filename, ip, port):
    """Send a file in chunks to the specified address."""
    # Validate file exists
    file_path = Path(filename)
    if not file_path.exists():
        print(f"Error: File '{filename}' not found")
        return 1
    
    # Setup socket connection
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        
        # First send the filename
        base_filename = os.path.basename(filename)
        s.sendall(f"{base_filename}\n".encode())
        
        # Then send file size
        file_size = os.path.getsize(filename)
        s.sendall(f"{file_size}\n".encode())
        
        # Send the file in chunks
        bytes_sent = 0
        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                s.sendall(chunk)
                bytes_sent += len(chunk)
                print(f"\rSent {bytes_sent}/{file_size} bytes ({bytes_sent/file_size:.1%})", end="")
        
        print("\nFile transfer complete!")
        
    except ConnectionRefusedError:
        print(f"Error: Connection refused to {ip}:{port}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        if 's' in locals():
            s.close()
    
    return 0

def receive_file(ip, port):
    """Receive a file in chunks and save it."""
    try:
        # Setup socket connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ip, port))
        s.listen(1)
        
        print(f"Listening on {ip}:{port}...")
        conn, addr = s.accept()
        print(f"Connection from {addr[0]}:{addr[1]}")
        
        # First receive the filename
        filename = conn.recv(1024).decode().strip()
        
        # Then receive file size
        file_size_str = conn.recv(1024).decode().strip()
        try:
            file_size = int(file_size_str)
        except ValueError:
            print("Error: Invalid file size received")
            return 1
        
        # Make sure we don't overwrite existing files
        output_filename = filename
        counter = 1
        while os.path.exists(output_filename):
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_{counter}{ext}"
            counter += 1
        
        # Receive and write the file
        bytes_received = 0
        with open(output_filename, 'wb') as f:
            while bytes_received < file_size:
                chunk = conn.recv(min(CHUNK_SIZE, file_size - bytes_received))
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)
                print(f"\rReceived {bytes_received}/{file_size} bytes ({bytes_received/file_size:.1%})", end="")
        
        print(f"\nFile saved as '{output_filename}'")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        if 's' in locals():
            s.close()
    
    return 0

"""

## Progress bar with standard library

"""python
import time

def progress_bar(iteration, total, bar_length=50):
    """
    Displays a progress bar in the console.

    Args:
        iteration (int): Current iteration number.
        total (int): Total number of iterations.
        bar_length (int, optional): Length of the progress bar. Defaults to 50.
    """
    percent = "{0:.1f}".format(100 * (iteration / float(total)))
    filled_length = int(bar_length * iteration // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\rProgress: |{bar}| {percent}% Complete ({iteration}/{total})', end='\r')
    if iteration == total:
        print()

if __name__ == '__main__':
    items = list(range(0, 20))
    total_items = len(items)

    for i, item in enumerate(items):
        time.sleep(0.1)  # Simulate work
        progress_bar(i + 1, total_items)
"""

## Progress bar using socket to send file

'''python
import socket
import sys
import os

def send_file_with_progress(filename, host, port):
    """Sends a file over a socket and displays a progress bar."""
    try:
        filesize = os.path.getsize(filename)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return

    try:
        s = socket.socket()
        s.connect((host, port))
        s.send(filename.encode())
        s.send(str(filesize).encode())

        with open(filename, "rb") as f:
            bytes_sent = 0
            while True:
                data = f.read(1024)
                if not data:
                    break
                s.sendall(data)
                bytes_sent += len(data)
                percent_complete = (bytes_sent / filesize) * 100
                # Update progress bar
                print(f"\rSent: {bytes_sent}/{filesize} bytes ({percent_complete:.2f}%)", end="")
                sys.stdout.flush()  # Ensure the output is displayed immediately
        print("\nFile sent successfully!")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    filename = "example.txt"  # Replace with your file
    host = "127.0.0.1"  # Replace with the receiver's IP
    port = 12345  # Replace with the receiver's port

    # Create a dummy file for testing
    with open(filename, "w") as f:
        f.write("This is a test file.\n" * 1000)

    send_file_with_progress(filename, host, port)
'''