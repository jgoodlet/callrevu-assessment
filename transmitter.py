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
    """Send a file to a receiving server."""

    host = args.ip
    port = args.port
    filename = args.filename

    try:
        filesize = os.path.getsize(filename)
    except FileNotFoundError:
        print(f"Error: file {filename} not found.")
        return 1

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        # Send the file size so the server know how big of a file
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


def receive_file(args) -> None:
    """Receive a file from a sending client."""

    host = args.ip
    port = args.port

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

    Note:
        This function relies on the send_file and receive_file functions
        which must be defined elsewhere in the code.
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
