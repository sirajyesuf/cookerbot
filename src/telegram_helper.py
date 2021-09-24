from functools import update_wrapper
import logging
from typing import Text
from certifi import contents
import spoonacular

import telegram
from telegram.ext import (CommandHandler, Filters, MessageHandler, Updater)

import config
import exceptions
import spoonacular_helper as sp

spoon = sp.SpoonacularFacade()

logging.info("Creating updaters and dispatchers...")

UPDATER = Updater(config.TELEGRAM_TOKEN)
DISPATCHER = UPDATER.dispatcher

logging.info("Updater and Dispatcher created.")


def format_message_and_get_parse_mode(recipe):
    """Formats a message and returns the proper parse mode.
    
    Args:
        recipe: json-like dict of recipe data.
    Returns:
        Tuple of formatted message and parse mode
    """
    logging.info(
        f"Formatting the recipe: {recipe['title']} | id: {recipe['id']}")
    parse_mode = telegram.ParseMode.HTML
    message = sp.SpoonacularFacade.format_recipe_data_as_html(recipe)

    if len(message) > config.TELEGRAM_MESSAGE_CHAR_LIMIT:
        logging.info("Recipe too long! Formatting a link instead.")
        link = sp.SpoonacularFacade.format_recipe_title_link_as_markdown(
            recipe)
        message = (f"This recipe was too long to send here\! Here's the "
                   f"link instead: {link}")
        parse_mode = telegram.ParseMode.MARKDOWN_V2

    return message, parse_mode


def start(update, context):
    """Start bot command function."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=("We're up! You can use the following commands to talk to me:\n"
              "/recipe [ingredients,to,search]\n"
              "/random\n"
              "/happyhour\n"
              "/taco\nMake something delicious!\n"
              "/randomfoodjokes"))


def recipes_for_ingredients(update, context):
    """Returns html formatted recipes given the input string."""
    ingredients = ''.join(context.args).lower()
    if not ingredients:
        logging.info("No ingredients provided!")
        raise exceptions.MissingIngredientError()

    recipe_ids = spoon.get_recipe_ids_for_ingredients(ingredients)
    if not recipe_ids:
        logging.info("No recipes found.")
        raise exceptions.RecipesNotFoundError()

    recipes = spoon.get_recipes_for_ids(recipe_ids)
    for recipe in recipes:
        message, parse_mode = format_message_and_get_parse_mode(recipe)
        logging.info("Sending...")
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message,
                                 parse_mode=parse_mode)
        logging.info("Recipe sent!")


def random_recipe(update, context):
    """Returns html formatted random recipe."""
    # Clean up arguments so we can validate tags
    all_args = ",".join(context.args).lower().split(",")
    for value in all_args:
        if value not in config.ALLOWED_TAGS:
            raise exceptions.InvalidRandomTagError()

    # Consolidate valid tags into single query
    tags = ",".join(all_args)
    recipe = spoon.get_random_recipe(tags=tags)
    message, parse_mode = format_message_and_get_parse_mode(recipe)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=message,
                             parse_mode=parse_mode)


def random_alcoholic_beverage(update, context):
    """Returns html formatted random alcoholic beverage recipe."""
    recipe_id = spoon.get_random_alcoholic_beverage_recipe_id()
    recipe = spoon.get_recipes_for_ids([recipe_id])
    message, parse_mode = format_message_and_get_parse_mode(recipe[0])

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=message,
                             parse_mode=telegram.ParseMode.HTML)


def _help(update, context):
    """Returns list of commands."""
    message = (
        "Commands:\n"
        "\t/recipe [ingredients,to,search] -> separted by commas, no brackets\n"
        "\t/random [optional:tags] -> returns a random recipe\n"
        "\t/taco -> returns a random taco recipe\n"
        "\t /randomfoodjokes -> return a random food jokes")
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def get_a_taco(update, context):
    """Returns a random taco!"""
    taco = "[Taco\!](https://taco-randomizer.herokuapp.com)"
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=taco,
                             parse_mode=telegram.ParseMode.MARKDOWN_V2)


def random_food_jokes(update, context):
    """return random food jokes"""
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=spoon.get_random_food_jokes())


def unknown(update, context):
    """Handles unknown commands."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm sorry, I don't understand. Please use /help to see commands."
    )


def error_handler(update, context):
    """Handles errors we get while executing commands."""
    logging.error(msg="Something went wrong when trying to handle an update.",
                  exc_info=context.error)

    parse_mode = None

    # Handle quota error
    if isinstance(context.error, exceptions.QuotaError):
        message = "We've hit our recipe quota for today! Come back tomorrow."
    # Missing ingredient argument error
    elif isinstance(context.error, exceptions.MissingIngredientError):
        message = "I need ingredients to search!"
    # No recipes found error
    elif isinstance(context.error, exceptions.RecipesNotFoundError):
        message = ("Yikes! I couldn't find anything for those ingredients. "
                   "Sorry about that. Please try some different ones.")
    # Invalid random tag error
    elif isinstance(context.error, exceptions.InvalidRandomTagError):
        message = (
            "Only the following are allowed as tags: "
            "[Diets](https://spoonacular.com/food-api/docs#Diets), "
            "[Intolerances](https://spoonacular.com/food-api/docs#Intolerances), "
            "[Cuisines](https://spoonacular.com/food-api/docs#Cuisines), "
            "and [Meal Types](https://spoonacular.com/food-api/docs#Meal-Types)\."
            " Please try your search again with a valid tag\.")
        parse_mode = telegram.ParseMode.MARKDOWN_V2
    # Catchall for other errors
    else:
        message = "Something went wrong with that last one! Try again or use /help"

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=message,
                             parse_mode=parse_mode)


# Handler registration
START_HANDLER = CommandHandler('start', start)
RECIPE_INGREDIENTS_HANDLER = CommandHandler('recipe', recipes_for_ingredients)
RANDOM_RECIPE_HANDLER = CommandHandler('random', random_recipe)
TACO_HANDLER = CommandHandler('taco', get_a_taco)
FOOD_JOKES_HANDLER = CommandHandler('randomfoodjokes', random_food_jokes)
UNKNOWN_HANDLER = MessageHandler(Filters.command, unknown)
HELP_HANDLER = CommandHandler('help', _help)

handlers = [
    START_HANDLER,
    HELP_HANDLER,
    RECIPE_INGREDIENTS_HANDLER,
    RANDOM_RECIPE_HANDLER,
    TACO_HANDLER,
    FOOD_JOKES_HANDLER,
    # Unknown handler must be last
    UNKNOWN_HANDLER
]

logging.info("Registering handlers with dispatcher...")

for handler in handlers:
    DISPATCHER.add_handler(handler)

DISPATCHER.add_error_handler(error_handler)

logging.info("Handlers added to dispatcher.")