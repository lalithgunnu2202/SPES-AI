import os
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.components.llm import reply_to_user
# from src.components.main import send_text
from src.logger import logging

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    welcome_text = f"""
👋 Hello {user.first_name}!

I'm an AI assistant powered by SPES AI.

Available commands:
/start - To Start me
/help - Get help
/ask <question> - Ask me anything!

Just send me a message and I'll respond!
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
🤖 **How to use this bot:**

1. Just type your question and send it!
2. Use commands:
   /ask <question> - Ask a question
   /help - This message
   Else Type any message i can handle it
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None):
    user_text = text or update.message.text
    logging.info("Recieved user text")
    # Show "typing" indicator
    await update.message.chat.send_action(action="typing")
    try:
        response = reply_to_user(user_text)
        
        # Send response (Telegram has 4096 character limit)
        if len(response) > 4000:
                response = response[:4000] + "...\n\n[Response truncated due to length]"
            
        await update.message.reply_text(response)

    except Exception as e:
        error_msg = f"❌ Error: {str(e)[:100]}..."
        logging.error("Error while process the user request!!")
        # More specific error messages
        if "rate limit" in str(e).lower() or "429" in str(e):
            error_msg = "⚠️ Rate limit exceeded. Free models allow ~2 requests per minute. Please wait a moment."
        elif "404" in str(e):
            error_msg = "❌ Model not found. The AI model might be unavailable. Try changing the model in code."
        
        await update.message.reply_text(error_msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logging.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    # Get bot token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("❌ Please set TELEGRAM_BOT_TOKEN in your .env file")
        print("Get a token from @BotFather on Telegram")
        return
    
    # Create Application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # application.add_handler(CommandHandler("model", show_model))
    # application.add_handler(CommandHandler("ask", ask_command))
    
    # Add message handler for regular messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("🤖 Bot is starting...")
    print(f"✅ Using token: {token[:10]}...")
    print("Press Ctrl+C to stop")
    
    # Run the bot until Ctrl+C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()