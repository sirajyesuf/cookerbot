import logging
import telegram
from telegram_helper import updater,dispatcher,send_weekly_meal_plan





def main():
    """Runs our bot."""
    logging.info("Starting the bot!")
    try:
        dispatcher.job_queue.run_repeating(callback=send_weekly_meal_plan, interval=604800)
        # 1 week=604,800 seconds
        updater.start_polling()
        updater.idle()
    except telegram.error.TelegramError as e:
        logging.error(f"Something went wrong! {e}")
        raise e

    logging.info("Bot shutting down. See ya next time!")


if __name__ == "__main__":
    main()