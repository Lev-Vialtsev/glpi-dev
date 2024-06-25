import telebot, json, requests, logging, traceback, configparser


bot_token = '6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU'
bot = telebot.TeleBot(bot_token)

class LibraryTelegram():

    '''Функции init и connect не прописаны в классе библиотеки, ими является структура основного кода
      и возможность в пользователя контактировать с ботом'''
    



    def send_message(message, name_chat, text):
        bot.send_message(message.name_chat, text)
    '''Функция send_message принимает на вход чат в который уходит сообщение и тот или иной текст, который оно содержит'''    



    
    def callback_button(message, name_chat, callback_data):
        pass
        '''Функция callback_button по моей задумке может либо просто замечать нажатия на кнопки, 
        либо в добавок к этому в функции можно будет указать действие после нажатия кнопки'''

    # @bot.callback_query_handler(func=lambda callback: True)
        # def again(callback):
    
        #     if callback.data == "описать_заново":
        #         bot.delete_message(callback.message.chat.id, callback.message.message_id)

        #         bot.send_message(callback.message.chat.id, 'Для этого нужно выбрать действие "Создать заявку"')
    
        '''В случае успешной проработки этой функции, вместо того, чтобы расписывать действие 
        для каждого варианта нажатия кнопки внутри главного кода, просто указывать функцию со значением callback_data в аргументе,
        а уже в библиотеке можно написать действия для нажатия разнвх кнопок.'''