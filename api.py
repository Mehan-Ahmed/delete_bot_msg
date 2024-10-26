from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio
import threading

app = Flask(__name__)

# Dictionary to store active bots by token
bots = {}

# Function to start a bot that deletes messages containing specified keywords
def start_bot(bot_token, ads_keywords):
    async def delete_ad_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Check if the message contains any of the ad keywords
        message_text = update.message.text.lower()
        if any(keyword in message_text for keyword in ads_keywords):
            try:
                # Attempt to delete the message
                await update.message.delete()
                print("Ad message deleted.")
            except Exception as e:
                print(f"Error deleting message: {e}")

    async def main() -> None:
        # Initialize the bot application
        app = Application.builder().token(bot_token).build()

        # Add the text filter handler
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_ad_message))

        # Run the bot
        await app.run_polling()

    # Start the bot in a new asyncio event loop on a separate thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

# API endpoint to start the bot with specified parameters
@app.route('/start_bot', methods=['POST'])
def start_bot_endpoint():
    data = request.json
    bot_token = data.get("bot_token")
    ads_keywords = data.get("ads_keyword")

    if not bot_token or not ads_keywords:
        return jsonify({"error": "Both 'bot_token' and 'ads_keyword' are required."}), 400

    # Convert ads_keywords to a list if it's a single keyword
    if isinstance(ads_keywords, str):
        ads_keywords = [ads_keywords]

    # Check if bot is already running with this token
    if bot_token in bots:
        return jsonify({"error": "Bot with this token is already running."}), 400

    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot, args=(bot_token, ads_keywords))
    bot_thread.start()
    
    # Store bot thread by token
    bots[bot_token] = bot_thread
    return jsonify({"status": "Bot started with specified keywords."}), 200

# Endpoint to stop the bot (optional)
@app.route('/stop_bot', methods=['POST'])
def stop_bot_endpoint():
    data = request.json
    bot_token = data.get("bot_token")

    if not bot_token or bot_token not in bots:
        return jsonify({"error": "Bot with this token is not running."}), 400

    # Terminate the bot thread (not ideal for production use)
    bots[bot_token].join()
    del bots[bot_token]
    return jsonify({"status": "Bot stopped."}), 200

if __name__ == "__main__":
    app.run(port=5000)
