"""
Job Hunt Intelligence & Excel Downloader Server
Runs a lightweight local web server and opens the interactive dashboard in your browser.
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 5000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

def main():
    os.chdir(DIRECTORY)
    url = f"http://localhost:{PORT}/index.html"
    print("=" * 65)
    print(" 🚀 Job Hunt Intelligence & Company Excel Exporter")
    print(f" 🌐 Server running at: {url}")
    print(" 📥 Features: Excel (.xlsx) Download, Cold Email Copy, Live Search")
    print(" 💡 Press Ctrl+C in this terminal to stop the server.")
    print("=" * 65)

    # Open web browser automatically
    webbrowser.open(url)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server. Goodbye!")

if __name__ == '__main__':
    main()
