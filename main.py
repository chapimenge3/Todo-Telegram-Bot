import os
import dotenv
import logging
import requests
import datetime
import json
import traceback
import html

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, PicklePersistence,ChatMemberHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, message
from telegram.update import Update
from telegram.utils.helpers import mention_html

dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

BROADCAST_MSG = []

def check_user(user_id):
    try:
        with open("internal.json") as f:
            users = json.load(f)
            for user in users:
                if user_id == user:
                    return True
    except Exception as e:
        print(e)
    
    return False

def add_user(user_id):
    try:
        with open("internal.json") as f:
            users = json.load(f)
            users.append(user_id)
        
        with open("internal.json", "w") as f:
            json.dump(users, f)
        
        return True
    except Exception as e:
        print(e)
    
    return False
    
def create_user(user):
    try:
        user_base_access_token = os.getenv('USER_BASE_ACCESS_TOKEN')
        api = "https://api.telegra.ph"
        time_now = f"{datetime.datetime.now():%Y-%m-%d %I:%M:%S %p}"
        params = {
            "access_token": user_base_access_token,
            "title": f"{user.id}",
            "author": f"Chapi Menge",
        }
        
        content = '[{"tag": "p", "children": [' + json.dumps(user.to_json()) +']}]'
        new_user = requests.post(f'{api}/createPage?content={content}', params=params)
        add_user(user.id)
    except Exception as e:
        print(e)

def channel_user(update):
    try:
        with open("matches.json") as f:
            channels = json.load(f)
        
        channels.append(update)
        
        with open("matches.json", "w") as f:
            json.dump(channels, f)
        
    except :
        pass

def create_posts(post):
    try:
        
        chat = post.effective_chat
        
        if not chat or not post:
            return
        
        access_token = os.getenv('ACCESS_TOKEN')
        api = "https://api.telegra.ph"
        params = {
            "access_token": access_token,
            "title": f"{chat.title} {chat.id} {chat.type}",
            "author": f"{chat.title} {chat.id} {chat.type}",
            "return_content": True,
        }
        content = '[{"tag": "p", "children": [' + json.dumps(post.to_json()) +']}]'
        
        new_post = requests.get(f"{api}/createPage?content={content}", params=params)
        print("new_post", new_post.text)
    except Exception as e:
        print(e)

def start(update, context):
    logger.info(f"User Started")
    text = f"""Hey {update.effective_user.first_name} {update.effective_user.last_name or ""}

    <b>To use this bot</b>
 
1. Create a channel 🚩🚩🚩

2. Add the bot to the channel ➕  🤖  🚩

3. Start posting your todo's in the channel.

4. The bot will make a button for you to mark it as done or cancel it. 🤾‍♂️  ⛹️  👯‍♀️

<b>Enjoy the bot!</b> 💃 🕺 

👷 Developed by {mention_html(1697562512, "Chapi Menge")}

reach out for any questions 🤔 or bugs 🐞 @ChapiMenge

If you have weird 🤒🤕 idea 💡 for this bot, 🙏🏻please reach out to {mention_html(1697562512, "Chapi Menge")}

📜📆📎📐🖇📝✏️

"""
    keyboard = [[InlineKeyboardButton("Support Me🥤", url="https://www.buymeacoffee.com/chapimenge")]]
    update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    
    if not check_user(update.effective_user.id):
        create_user(update.effective_user)
        
def posts(update, context):

    try:

        if not update or not update.channel_post:
            print("No update posted")
            return

        chat_id = update.channel_post.chat.id
        message_id = update.channel_post.message_id
        keyboard = [
            [InlineKeyboardButton("Done ✅", callback_data='done'),
             InlineKeyboardButton("Delete", callback_data='cancel')],
        ]
        context.bot.edit_message_reply_markup(
            chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))

        create_posts(update)
        
    except Exception as e:
        print(e)
        import traceback
        traceback.print_exc()


def button_clicked(update, context):
    try:
        query = update.callback_query
        if query.data == "cancel":
            keyboard = [[
                InlineKeyboardButton("Item Canceled 🗑", callback_data='canceled')
            ]]
            keyboard = InlineKeyboardMarkup(keyboard)
        else:
            context.bot.answer_callback_query(query.id, text="Horary 🥳! Item marked as done 🎉")
            keyboard = None
            
        query.answer()
        chat_id = update.effective_chat.id
        message_id = update.effective_message.message_id
        context.bot.edit_message_reply_markup(
            chat_id, message_id, reply_markup=keyboard)

    except Exception as e:
        print(e)


def canceled_item(update, context):
    try:
        query = update.callback_query
        context.bot.answer_callback_query(
            query.id, text="This Item is Canceled!!!")
    except Exception as e:
        pass

def added_to_channel(update, context):
    # print("update", update)
    try:
        if not update.my_chat_member.new_chat_member :
            return
        
        if update.my_chat_member.new_chat_member.status != "administrator":
            return
        
        ch_us = {
            f"{update.my_chat_member.from_user.id}{update.my_chat_member.chat.id}": [
                update.my_chat_member.from_user.to_json(),update.my_chat_member.chat.to_json()
            ]
        }
        
        channel_user(ch_us)
        context.bot.send_message(update.my_chat_member.chat.id, "Post your todo's here 📝")
    except Exception as e :
        print(e)

def get_user_id():
    try:
        user_base_access_token = os.getenv('USER_BASE_ACCESS_TOKEN')
        api = "https://api.telegra.ph"
        response = requests.get(f"{api}/getPageList?access_token={user_base_access_token}")
        if response.status_code != 200:
            return None
        users = [
            int(user['title']) for user in response.json()['result']['pages']
        ]
        return users
    except Exception as e:
        pass

def broadcast_user(context):
    """
    Broadcast user in telegram bot
    """
    
    global BROADCAST_MSG
    
    users = get_user_id()
    
    if not users:
        context.bot.send_message( 1697562512,"No users found")
        return
    context.bot.send_message(1697562512, "Broadcasting the below message to all users started!!!")
    msgs = BROADCAST_MSG
    context.bot.send_message(1697562512, "_"*100)
    for msg in msgs:
        context.bot.send_message(1697562512, msg)
    
    context.bot.send_message(1697562512, "_"*100)
    
    number = 0
    fail = 0
    for user in users:
        for msg in msgs:
            try:
                import time
                context.bot.copy_message(user, 1697562512, msg )
                time.sleep(1)
                number += 1
            except Exception as e:
                fail += 1
                pass
    
    context.bot.send_message(1697562512, "Broadcasted to all users Finished!!!\n\nSuccesses: {}\nFailed: {}".format(number, fail))
    BROADCAST_MSG = []

def clear_broadcast_msg(update, context):
    BROADCAST_MSG = []
    update.message.reply_text("All messages cleared")

    
def broadcast_start(update, context):
    if update.effective_chat.type != "private":
        return
    
    if update.effective_user.id != 1697562512:
        return
    
    BROADCAST_MSG = []
    # update.message.reply_text("Start broadcasting 📣")
    update.message.reply_text("Send me Broadcast messages 📣")
    return "MESSAGES"

def broadcast_message(update, context):
    if update.effective_chat.type != "private":
            return
    
    if update.effective_user.id != 1697562512:
        return
    if update.message.text and update.message.text == "/done" :
        return broadcast_end(update, context)
        
    BROADCAST_MSG.append(update.message.message_id)
    update.message.reply_text("Message added to broadcast 📣. send me /done when you are done 📣")
    return "MESSAGES"

def broadcast_end(update, context):
    if update.effective_chat.type != "private":
            return
    
    if update.effective_user.id != 1697562512:
        return
    
    update.message.reply_text("Broadcast messages sent 📣")
    
    context.job_queue.run_once(broadcast_user, 5, context=update.message.chat_id)
    
    return ConversationHandler.END

broadcast_conv = ConversationHandler(
    entry_points=[CommandHandler('broadcast', broadcast_start)],
    states={
        "MESSAGES": [MessageHandler(Filters.all, broadcast_message)]
    }, 
    fallbacks=[CommandHandler('done', broadcast_end)]
)

def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=1697562512, text=message, parse_mode="HTML")


def main():
    pickle = PicklePersistence(filename='todo.pkl')
    updater = Updater(TOKEN, use_context=True, persistence=pickle)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.status_update, added_to_channel))
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('clear_msg', clear_broadcast_msg))
    dp.add_handler(broadcast_conv)
    
    dp.add_handler(CallbackQueryHandler(canceled_item, pattern=r"canceled"))
    dp.add_handler(CallbackQueryHandler(
        button_clicked, pattern=r"(done|cancel)"))
    
    dp.add_handler(MessageHandler(Filters.update.channel_posts, posts))
    dp.add_handler(ChatMemberHandler( added_to_channel))
    
    
    dp.add_error_handler(error_handler)
    
    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    updater.idle()


if __name__ == '__main__':
    main()
