# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
# software, either in source code form or as a compiled binary, for any purpose,
# commercial or non-commercial, and by any means.
#
# In jurisdictions that recognize copyright laws, the author or authors of this
# software dedicate any and all copyright interest in the software to the public
# domain. We make this dedication for the benefit of the public at large and to the
# detriment of our heirs and successors. We intend this dedication to be an overt act
# of relinquishment in perpetuity of all present and future rights to this software
# under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

import argparse
import os
import socket
import sys
from textwrap import dedent

CHUNK_SIZE = 4096


def send_file(args) -> int | None:
    """
    Send a file to a remote server over a TCP/IP connection.

    This function establishes a socket connection to the specified host and port,
    then transmits the requested file. The file is sent in chunks to efficiently
    handle large files without excessive memory usage.

    Args:
        args: A namespace object containing the following attributes:
            ip (str): The IP address of the target server.
            port (int): The port number on the target server.
            filename (str): Path to the file to be transmitted.

    Returns:
        int | None: Returns 1 if an error occurs (file not found, connection refused,
            socket error, or other exception), None if transmission completes
            successfully.

    Raises:
        No exceptions are raised directly, but socket errors may occur during
        connection or transmission and are handled accordingly:

        - FileNotFoundError: If the specified file doesn't exist
        - ConnectionRefusedError: If the remote server refuses the connection
        - socket.error: If a socket-related error occurs
        - Exception: For any other unexpected errors

    """
    host = args.ip
    port = args.port
    filename = args.filename

    try:
        filesize = os.path.getsize(filename)
    except FileNotFoundError:
        print(f"Error: file {filename} not found.")
        return 1

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(f"{filesize}\n".encode())

            # Send the file in chunks
            bytes_sent = 0
            with open(filename, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    s.sendall(chunk)
                    bytes_sent += len(chunk)
                    print(
                        f"\rSent {bytes_sent}/{filesize} bytes ({bytes_sent/filesize:.1%})",
                        end="",
                    )

            print("\nFile transmission complete!")

    except ConnectionRefusedError:
        print(f"Connection refused to {host}:{port}")
        return 1
    except socket.error as e:
        print(f"Socket error occurred: {e}")
        return 1
    except Exception as e:
        print(f"Error encountered: {e}")
        return 1


def receive_file(args) -> int | None:
    """Receive a file from a remote client over a TCP/IP connection.

    This function creates a socket server that listens on the specified IP address
    and port for incoming connections. Once a connection is established, it receives
    the file size first, then the file data in chunks, writing the received data to
    a local file named 'output.txt'.

    Args:
        args: A namespace object containing the following attributes:
            ip (str): The IP address to bind the server to.
            port (int): The port number to listen on.

    Returns:
        int | None: Returns 1 if an error occurs during execution, None if the
            file is received successfully.

    Note:
        - The function always saves the received file as 'output.txt' in the
        current working directory regardless of the original filename.
        - The function will block until a connection is received.
    """
    host = args.ip
    port = args.port

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()

            print(f"Listening on {host}:{port}...")

            conn, addr = s.accept()
            with conn:
                print(f"Connection from {addr} established")

                # Get the file size
                filesize = int(conn.recv(1024).decode().strip())
                bytes_received = 0

                with open("output.txt", "wb") as f:
                    while bytes_received < filesize:
                        chunk = conn.recv(min(CHUNK_SIZE, filesize - bytes_received))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_received += len(chunk)
                        print(
                            f"\rReceived {bytes_received}/{filesize} bytes ({bytes_received/filesize:.1%})",
                            end="",
                        )

                print("\nFile received and saved!")
    except Exception as e:
        print(f"Error encountered: {e}")
        return 1


def main() -> int:
    """Main entry point for the file transmitter utility.

    This function sets up the command-line interface using argparse, defining
    two main commands: 'send' and 'recv' for sending and receiving files over
    a network connection. It parses command-line arguments and calls the
    appropriate function based on the selected command.

    Commands:
        send: Transmit a file to a specified IP address and port.
        recv: Listen on a specified IP address and port to receive a file.

    Returns:
        int: Returns 0 on successful execution.
    """
    parser = argparse.ArgumentParser(
        prog="transmitter",
        description=dedent("""\
            File transmitter utility

            This tool provides a simple interface for transferring files between
            networked computers using TCP/IP sockets. Use the 'send' command to
            transmit files to a remote host, and the 'recv' command to receive
            incoming files. All transfers are handled as binary data to preserve
            file integrity."""),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        title="commands", dest="command", help="Command to execute"
    )

    # Send command
    send_parser = subparsers.add_parser("send", help="Send a file")
    send_parser.add_argument("filename", help="File to send")
    send_parser.add_argument("ip", help="Target IP address")
    send_parser.add_argument("port", type=int, help="Target port")
    send_parser.set_defaults(func=send_file)

    # Receive command
    recv_parser = subparsers.add_parser("recv", help="Receive a file")
    recv_parser.add_argument("ip", help="Listening IP address")
    recv_parser.add_argument("port", type=int, help="Listening port")
    recv_parser.set_defaults(func=receive_file)

    # Parse arguments
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
