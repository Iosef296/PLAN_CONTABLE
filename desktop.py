import threading
import time
import webbrowser

from app import app

PORT = 5000


def run_server():
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1)
    webbrowser.open(f"http://127.0.0.1:{PORT}/")
    t.join()
