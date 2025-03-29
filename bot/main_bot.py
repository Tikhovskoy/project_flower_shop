import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FlowerShopBot.settings')
import django
django.setup()

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

from bot.handlers.start_handlers import (
    handle_start,
    handle_start_menu_selection,
    handle_event_selection,
    handle_messages
)
from bot.handlers.consult_handlers import handle_consult_request
from bot.handlers.catalog_handlers import handle_budget_selection, handle_catalog
from bot.handlers.order_handlers import handle_order_start, handle_card_choice

def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    updater = Updater(token=token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", handle_start))
    dispatcher.add_handler(CallbackQueryHandler(handle_start_menu_selection,
                                                pattern="^(choose_bouquet|choose_event|request_consult)$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_event_selection,
                                            pattern="^(march8|wedding|teacher|no_reason|custom)$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_budget_selection, pattern=r"^(500|1000|2000|any)$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_catalog, pattern="^show_catalog$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_order_start, pattern="^start_order$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_card_choice, pattern="^(add_card_yes|add_card_no)$"))    
    dispatcher.add_handler(CallbackQueryHandler(handle_consult_request, pattern="^request_consult$"))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_messages))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
