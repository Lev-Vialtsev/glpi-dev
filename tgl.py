import telebot, logging, traceback

bot = None

'''Функции init и connect не прописаны в классе библиотеки, ими является структура основного кода
    и возможность пользователя контактировать с ботом'''

'''Функция init инициализирует телеграмм бота'''

def init(token):
    global bot
    bot = telebot.TeleBot(token)
    return bot

'''Функция send_message принимает на вход чат в который уходит сообщение и тот или иной текст, который оно содержит''' 

def send_message(chat_id, text):
    try:
        bot.send_message(chat_id, text)
    except Exception as e:
        logging.log.error(f"An error occurred while sending a message: {e}")
        traceback.print_exc()


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print("need 1 param - config file")
    sys.exit(1)
  else:
    config=loadConfig(sys.argv[1])
  log=logging.getLogger("matrix-reaction-signature-bot")

  if config["logging"]["debug"].lower()=="yes":
    log.setLevel(logging.DEBUG)
  else:
    log.setLevel(logging.INFO)

  # create the logging file handler
  #fh = logging.FileHandler(config.log_path)
  fh = logging.handlers.TimedRotatingFileHandler(config["logging"]["log_path"], when=config["logging"]["log_backup_when"], backupCount=int(config["logging"]["log_backup_count"]), encoding='utf-8')
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s() %(levelname)s - %(message)s')
  fh.setFormatter(formatter)

#  if config["logging"]["debug"].lower()=="yes":
  # логирование в консоль:
  stdout = logging.StreamHandler(sys.stdout)
  stdout.setFormatter(formatter)
  log.addHandler(stdout)

  # add handler to logger object
  log.addHandler(fh)

  log.info("Program started")
  log.info("python version=%s"%sys.version)

  asyncio.get_event_loop().run_until_complete(main())
  #if main()==False:
  #  log.error("error main()")
  #  sys.exit(1)
  log.info("program exit success")