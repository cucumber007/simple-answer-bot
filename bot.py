import json
from datetime import datetime, timedelta
import os
import traceback

from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters
from telegram.ext import CommandHandler


class Bot:
    owner_id = None
    greeting_message = None
    post_message = None

    chat_messages = {}

    @staticmethod
    def log(text):
        with open("logs.txt", "a") as logfile:
            logfile.write(str(text) + "\n")

    def run(self):
        try:
            with open("local-properties.json", "r", encoding="utf-8") as f:
                config = json.loads(f.read())
        except FileNotFoundError:
            config = json.loads(os.environ['BOT_CONFIG'])
        token = config["token"]
        self.owner_id = int(config.get("owner_id"))
        self.greeting_message = config.get("greeting_message")
        self.post_message = config.get("post_message")

        updater = Updater(token=token, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=self.message))

        # dispatcher.add_error_handler(self.handle_error)

        updater.start_polling()
        print("Bot successfully inited")

    def start(self, update, context):
        try:
            username = update.message.from_user['username']
            print("@{}: ".format(username), update.message.text)
            update.message.reply_text(self.greeting_message)
        except Exception as e:
            self.log(e)
            update.message.reply_text("Ошибка: " + str(e))

    def message(self, update, context, *kwargs):
        try:
            user_id = update.message.from_user['id']
            message = update.message
            username = message.from_user.username
            reply = message.reply_to_message
            if user_id != self.owner_id:
                # user message
                self.log("User message: {} {}: {}".format(username, user_id, message.text))
                print("User message: {} {}: {}".format(username, user_id, message.text))
                # context.bot.forward_message(
                #     chat_id=self.owner_id,
                #     from_chat_id=user_id,
                #     message_id=message.message_id
                # )
                context.bot.send_message(
                    chat_id=self.owner_id,
                    text="{} ### {}: {}".format(user_id, username, message.text)
                )
                if self.post_message:
                    latest_allowed_last_post_message_datetime = datetime.now() - timedelta(seconds=60 * 30)
                    last_message_datetime = context.user_data.get("last_post_message")
                    if not last_message_datetime or last_message_datetime < latest_allowed_last_post_message_datetime:
                        self.log("Post message: {} {}".format(username, user_id))
                        print("Post message: {} {}".format(username, user_id))
                        update.message.reply_text(self.post_message)
                        context.user_data["last_post_message"] = datetime.now()

            else:
                if reply:
                    if " ### " in reply.text:
                        # admin reply
                        reply_to_username = reply.text.split(":")[0].split(" ### ")[1]
                        reply_to_id = reply.text.split(" ### ")[0]

                        self.log("Reply: {} {}: {}".format(reply_to_username, reply_to_id, message.text))
                        print("Reply: {} {}: {}".format(reply_to_username, reply_to_id, message.text))
                        context.bot.send_message(
                            chat_id=reply_to_id,
                            text=message.text
                        )
        except Exception as err:
            self.log(err)
            print(err)
            user_id = update.message.from_user['id']
            if user_id != self.owner_id:
                update.message.reply_text("Произошла ошибка")
                context.bot.send_message(
                    chat_id=self.owner_id,
                    text="{} Error: {}".format(user_id, str(err))
                )
            else:
                update.message.reply_text(str(err))

            traceback.print_exc()


try:
    bot_instance = Bot()
    bot_instance.run()
except Exception as e:
    print(e)
