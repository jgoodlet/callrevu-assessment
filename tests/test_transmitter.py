import os
import socket
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Import the module to test
import transmitter


class TestFileTransmitter(unittest.TestCase):
    """Test cases for the file transmitter utility."""

    FILE_CONTENTS = b"This is test content for the file transmitter."

    IP = "127.0.0.1"
    PORT = 12345

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(self.FILE_CONTENTS)
        self.temp_file.close()
        self.temp_file_size = os.path.getsize(self.temp_file.name)

    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        # Remove output file if it exists
        if os.path.exists("output.txt"):
            os.unlink("output.txt")

    @patch("socket.socket")
    def test_send_file_success(self, mock_socket):
        """Test successful file sending."""
        # Mock the socket object and its methods
        mock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_instance

        # Create args object with test values
        args = MagicMock()
        args.ip = self.IP
        args.port = self.PORT
        args.filename = self.temp_file.name

        # Redirect stdout to capture progress output
        captured_output = StringIO()
        sys.stdout = captured_output

        # Call the send_file function
        result = transmitter.send_file(args)

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Verify that send_file was called correctly
        mock_instance.connect.assert_called_once_with((self.IP, self.PORT))
        self.assertIsNone(result)
        self.assertIn("File transmission complete!", captured_output.getvalue())

    @patch("socket.socket")
    def test_send_file_nonexistent(self, mock_socket):
        """Test sending a file that doesn't exist."""
        # Create args object with non-existent file
        args = MagicMock()
        args.ip = self.IP
        args.port = self.PORT
        args.filename = "nonexistent_file.txt"

        # Redirect stdout to capture error output
        captured_output = StringIO()
        sys.stdout = captured_output

        # Call the send_file function
        result = transmitter.send_file(args)

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Verify error handling
        self.assertEqual(result, 1)
        self.assertIn(
            "Error: file nonexistent_file.txt not found", captured_output.getvalue()
        )

    @patch("socket.socket")
    def test_send_file_connection_refused(self, mock_socket):
        """Test sending a file with connection refused error."""
        # Mock the socket to raise ConnectionRefusedError
        mock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_instance
        mock_instance.connect.side_effect = ConnectionRefusedError()

        # Create args object with test values
        args = MagicMock()
        args.ip = self.IP
        args.port = self.PORT
        args.filename = self.temp_file.name

        # Redirect stdout to capture error output
        captured_output = StringIO()
        sys.stdout = captured_output

        # Call the send_file function
        result = transmitter.send_file(args)

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Verify error handling
        self.assertEqual(result, 1)
        self.assertIn(
            f"Connection refused to {self.IP}:{self.PORT}", captured_output.getvalue()
        )

    @patch("socket.socket")
    def test_receive_file_success(self, mock_socket):
        """Test successful file receiving."""
        # Mock the socket object and its methods
        mock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_instance

        # Mock the connection
        mock_conn = MagicMock()
        mock_instance.accept.return_value = (mock_conn, (self.IP, self.PORT))

        # Mock the file size and content
        mock_conn.recv.side_effect = [
            f"{self.temp_file_size}\n".encode(),
            self.FILE_CONTENTS,  # Second recv returns file content
        ]

        # Create args object with test values
        args = MagicMock()
        args.ip = self.IP
        args.port = self.PORT

        # Redirect stdout to capture progress output
        captured_output = StringIO()
        sys.stdout = captured_output

        # Call the receive_file function
        result = transmitter.receive_file(args)

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Verify that receive_file was called correctly
        mock_instance.bind.assert_called_once_with((self.IP, self.PORT))
        mock_instance.listen.assert_called_once()
        self.assertIsNone(result)
        self.assertIn("File received and saved!", captured_output.getvalue())

        # Check that the output file was created with the correct content
        self.assertTrue(os.path.exists("output.txt"))
        with open("output.txt", "rb") as f:
            content = f.read()
            self.assertEqual(content, self.FILE_CONTENTS)

    @patch("socket.socket")
    def test_receive_file_error(self, mock_socket):
        """Test receiving a file with an error."""
        # Mock the socket to raise an Exception
        mock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_instance
        mock_instance.bind.side_effect = socket.error("Address already in use")

        # Create args object with test values
        args = MagicMock()
        args.ip = self.IP
        args.port = self.PORT

        # Redirect stdout to capture error output
        captured_output = StringIO()
        sys.stdout = captured_output

        # Call the receive_file function
        result = transmitter.receive_file(args)

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Verify error handling
        self.assertEqual(result, 1)
        self.assertIn("Error encountered", captured_output.getvalue())


if __name__ == "__main__":
    unittest.main()
