# Encrypter.py
import os
import tempfile
import base64
import marshal
import zlib
import pyfiglet
import telebot

# Print filename on startup (nice to see in logs)
print(f"Starting {os.path.basename(__file__)} (polling mode)...")

# ---------- CONFIG ----------
# IMPORTANT: set this env var on your host / Render. Do NOT hardcode your token.
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set. Set it before running.")

# Optional: set iterations via env var (defaults to 1)
try:
    ITERATIONS = max(1, int(os.environ.get("ITERATIONS", "1")))
except Exception:
    ITERATIONS = 1

# Pretty banner (safe fallback)
def logo(name="Encrypter"):
    try:
        print(pyfiglet.figlet_format(name, font="slant"))
    except Exception:
        print(f"=== {name} ===")

logo("W l z b i")

# Create bot (threaded True is fine for polling)
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ---------- OBFUSCATOR ----------
class Obfuscator:
    def __init__(self, script_path):
        self.script = script_path

    def B85(self, iterations=1):
        """Marshal -> zlib -> reverse -> base85 encode, wrapped in exec loader."""
        try:
            with open(self.script, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print("Error reading file:", e)
            return None

        for _ in range(iterations):
            code = compile(content, "_", "exec")
            data = marshal.dumps(code)
            compressed = zlib.compress(data)
            reversed_data = compressed[::-1]
            enc = base64.b85encode(reversed_data).decode("utf-8")
            content = "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b85decode('%s')[::-1]));exec(_(_))" % enc

        output_name = os.path.splitext(self.script)[0] + "-enc.py"
        try:
            with open(output_name, "w", encoding="utf-8") as out:
                out.write(content)
            return output_name
        except Exception as e:
            print("Error writing output file:", e)
            return None

# ---------- TELEGRAM HANDLERS ----------
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 Hello! Send me a Python (.py) file and I'll obfuscate it and send it back.\n"
        "Make sure the file is a .py file.\n"
        "Join @Wlzbii for more tools."
    )

@bot.message_handler(content_types=["document"])
def handle_document(message):
    doc = message.document
    name = doc.file_name or "file.py"
    if not name.lower().endswith(".py"):
        bot.send_message(message.chat.id, "❌ Please send a valid Python (.py) file.")
        return

    try:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to download file: {e}")
        return

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    out_path = None
    try:
        tmp.write(downloaded)
        tmp.flush()
        tmp.close()

        bot.send_message(message.chat.id, f"✅ Received '{name}'. Obfuscating (iterations={ITERATIONS})...")

        ob = Obfuscator(tmp.name)
        out_path = ob.B85(iterations=ITERATIONS)

        if out_path and os.path.exists(out_path):
            with open(out_path, "rb") as f:
                bot.send_document(message.chat.id, f, caption=f"✅ Here is your obfuscated file (iterations={ITERATIONS}).\nJoin @Wlzbii")
            bot.send_message(message.chat.id, "❤️Please support @Wlzbi || @Wlzbii")
        else:
            bot.send_message(message.chat.id, "❌ Failed to obfuscate the file.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error processing file: {e}")
    finally:
        # Cleanup
        try:
            if tmp and os.path.exists(tmp.name):
                os.remove(tmp.name)
            if out_path and os.path.exists(out_path):
                os.remove(out_path)
        except Exception:
            pass

# ---------- RUN ----------
if __name__ == "__main__":
    print("Bot started (polling). Press Ctrl+C to stop.")
    # infinity_polling will reconnect automatically on network issues
    bot.infinity_polling(timeout=20, long_polling_timeout=60)