from functools import wraps
from models import db, subscription


def subscribe(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        chat_id = args[0]["message"]["chat"]["id"]
        print("func name", func.__name__)
        subscribed = db.search(subscription.chat_id == chat_id)
        print(subscribed)
        if (len(subscribed) and func.__name__ == 'start'):
            return func(*args, **kwargs)
        if (len(subscribed) and func.__name__ == '_help'):
            return func(*args, **kwargs)
        if (not len(subscribed) and func.__name__ == 'start'):
            message = "We're up! You can use the following commands to talk to me:\n/recipe [ingredients,to,search]\n/random\n/randomfoodjokes\n/subscribe_to_weeekly_meal_plan"
            args = (*args, str(message))
            return func(*args, **kwargs)
        if (not len(subscribed) and func.__name__ == '_help'):
            message = """
            Commands:\n
            \t/recipe [ingredients,to,search] -> separted by commas, no brackets\n
            \t/random [optional:tags] -> returns a random recipe\n
            \t/randomfoodjokes -> return a random food jokes,
            \t/subscribe_to_weekly_meal_plan -> get weekly meal plan
            """
            args = (*args, str(message))
            return func(*args, **kwargs)
    return wrapper
