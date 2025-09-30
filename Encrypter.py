import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== PORT BINDER FOR RENDER ==================
PORT = int(os.environ.get("PORT", "8000"))  # Render sets $PORT

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"OK")  # simple health check
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # disable noisy logs
        return

def start_http_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
        print(f"Health server listening on 0.0.0.0:{PORT}")
        server.serve_forever()
    except Exception as e:
        print("Failed to start health server:", e)

# Run in background thread so it doesn’t block your bot
threading.Thread(target=start_http_server, daemon=True).start()
# ============================================================


import subprocess
import sys
import base64, marshal, zlib
import pyfiglet
import telebot
from dotenv import load_dotenv

# Load environment variables (for local dev)
load_dotenv()

RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"

# ------------------ CONFIG ------------------

def logo(name):
    banner = pyfiglet.figlet_format(name, font="slant")
    print(f"\033[1m\033[31m{banner}\033[0m") 

logo('W l z b i')

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not set in environment")

bot = telebot.TeleBot(BOT_TOKEN)


class Obfuscator:
    def __init__(self, script_path):
        self.script = script_path

    def B85(self, iterations=3):
        try:
            with open(self.script, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"{RED}Error reading file: {e}{RESET}")
            return None
        
        for i in range(iterations):
            code = compile(content, "_", 'exec')
            data = marshal.dumps(code)
            compressed_data = zlib.compress(data)
            reversed_data = compressed_data[::-1]
            enc = base64.b85encode(reversed_data).decode('utf-8')
            content = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b85decode('%s')[::-1]));exec(_(_))" % enc
        
        output_name = os.path.splitext(self.script)[0] + "-enc.py"
        try:
            with open(output_name, 'w', encoding='utf-8') as file:
                file.write(content)
            return output_name
        except Exception as e:
            print(f"{RED}Error writing output file: {e}{RESET}")
            return None


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 Hello!\n"
        "Please send me a Python (.py) file and I will obfuscate it for you.\n"
        "After obfuscation, I will send it back to you!\n"
        "Join @Wlzbii for more tools."
    )


@bot.message_handler(content_types=['document'])
def handle_document(message):
    doc = message.document
    if not doc.file_name.endswith('.py'):
        bot.send_message(message.chat.id, "❌ Please send a valid Python (.py) file.")
        return

    file_info = bot.get_file(doc.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    input_file_path = f"temp_{doc.file_name}"
    with open(input_file_path, 'wb') as f:
        f.write(downloaded_file)
    
    bot.send_message(message.chat.id, f"✅ Received '{doc.file_name}'. Obfuscating...")

    obfuscator = Obfuscator(input_file_path)
    output_file_path = obfuscator.B85(iterations=1)

    if output_file_path:
        with open(output_file_path, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="✅ Here is your obfuscated file.\nJoin @Wlzbii")
        bot.send_message(message.chat.id, "❤️ Please support @Wlzbi || @Wlzbii")
    else:
        bot.send_message(message.chat.id, "❌ Failed to obfuscate the file.")

    # Cleanup temporary files
    try:
        os.remove(input_file_path)
        if output_file_path:
            os.remove(output_file_path)
    except Exception:
        pass


print(f"{CYAN}Bot is running... Press Ctrl+C to stop.{RESET}")
bot.infinity_polling()
