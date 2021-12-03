import os
import telebot
import dataBase as db
import json

file = open(".env", "r")
env = json.load(file)
KEY_TOKEN = env['KEY_TOKEN']
bot = telebot.TeleBot(KEY_TOKEN)
file.close()


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, message)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Nice, I'll take account your debts \nbut first write /addMe")


@bot.message_handler(commands=['help'])
def help_message(message):
    help_mes = "/addMe\n will add you into db\n" \
               "/addEqualTo <value> <@usernames>[others @usernames]\nprice divided by you and others\n" \
               "/balanceWith <username>\nWill tell you the balance between you and the username"
    bot.send_message(message.chat.id, help_mes)


@bot.message_handler(commands=['addEqualTo'])  # TODO aggiungere la spesa a tutti gli altri
def add_equal_to(message):
    """
    aggiungi a tutti la spesa in modo uguale - tranne a chi la chiama
    """
    conn = db.create_connection()
    if not is_caller_on_db(conn, message.chat.id, [message.from_user.username]):
        return
    message_as_list = get_list_from_message(message)
    price_to_divide = return_value_if_correct(message_as_list[0])
    if price_to_divide is None:
        bot.send_message(message.chat.id, "Gimme money correctly bruh")
        return
    elif price_to_divide == 0:
        bot.send_message(message.chat.id, "Brutto coglione, non provarci mai più!")
        return

    users_called = return_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list)
    if users_called is None:
        return
    value = truncate(price_to_divide / (len(message_as_list)))
    try:
        db.insert_transactions_into_db(conn, message.from_user.id, users_called, float(value), message.chat.id)
    except:
        bot.send_message(message.chat.id, "Something went wrong diomaialo")
        return
    str_user = ""
    len_list = len(users_called)
    for i in range(len_list):
        if i == len_list or i == 0:
            div = ""
        else:
            div = ","
        str_user = "{}{} {}".format(str_user, div, users_called[i])
    bot.send_message(message.chat.id, "{} ha indebitato{} di:\n{}€".format(message.from_user.username, str_user,
                                                                           value))  # TODO aggiungere la lista delle persone indebitate
    conn.close()


@bot.message_handler(commands=['addTo'])  # TODO da finire
def add_to(message):
    """
    inserisce la spesa solo ad una persona
    """


@bot.message_handler(commands=['balance'])
def get_balance(message):
    """
    print into the chat the balance of each one
    """

    # bot.send_message(message.chat.id,response)


@bot.message_handler(commands=['balanceWith'])
def get_balance_from(message):
    """
    print into the chat the balance of each one
    """
    conn = db.create_connection()
    if not is_caller_on_db(conn, message.chat.id, [message.from_user.username]):
        return
    message_as_list = get_list_from_message(message)
    user_called = return_list_of_usernames_if_correct(conn, message, message_as_list)
    if user_called is None:
        return
    if len(user_called) != 1:
        bot.send_message(message.chat.id, "Gimme just one username ")
        return
    try:
        print(user_called[0])
        bal = db.get_balance_from(conn, message.from_user.id, user_called[0], message.chat.id)
        print(bal)
        if bal < 0:
            bot.send_message(message.chat.id, "Sei in crick di:\n{}€".format(bal))
        elif bal == 0:
            bot.send_message(message.chat.id, "Niente crick:\n{}€, gg".format(0))
        else:
            bot.send_message(message.chat.id, "{} è in crick di:\n{}€".format(user_called[0], bal))
    finally:
        conn.close()


@bot.message_handler(commands=['addMe'])
def add_me(message):
    """
    add users to set them into the db
    person(id_person,name,username,portfolio,group_id)
    """
    conn = db.create_connection()
    try:
        user = (message.from_user.id, message.from_user.first_name, message.from_user.username, message.chat.id)
        if db.insert_user_into_db(conn, user) < 0:
            bot.send_message(message.chat.id, "Nope")
        else:
            print("Aggiunto: {}".format(user))
            bot.send_message(message.chat.id, "Oky, {}".format(message.from_user.first_name))
            conn.close()
    except:
        bot.send_message(message.chat.id, "Wait, qualcosa non funge")
    conn.close()


def get_string_from_message(message):
    myList = list(message.text)
    mySecondList = []
    startInserting = False
    for i in myList:
        if startInserting:
            mySecondList.append(i)
        if startInserting is False and i == ' ':
            startInserting = True
    newMessage = str.join("", mySecondList)
    return newMessage


def get_list_from_message(message):
    string = get_string_from_message(message)
    stringSplitted = str.split(string)
    listToReturn = []
    for string in stringSplitted:
        listToReturn.append(string)
    return listToReturn


def return_value_if_correct(value):
    """
    given a value it test if it has , and if is a number obv
    """
    valueTest = value.replace(',', '.')
    if valueTest.replace('.', '').isnumeric():
        try:
            priceToDivide = float(valueTest)
        except:
            return None
        priceToDivide = truncate(priceToDivide)
    else:
        return None
    return priceToDivide


def truncate(num, n=2):
    temp = str(num)
    for x in range(len(temp)):
        if temp[x] == '.':
            try:
                return float(temp[:x + n + 1])
            except:
                return float(temp)
    return float(temp)


def return_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list):
    """
    return a list within all the username without the one which will call the bot
    :param conn:
    :param message: the obg message
    :param message_as_list: the list of username
    :return: None if isn't correct - will give response
    """
    users_called = []
    for i in range(1, len(message_as_list)):
        if message_as_list[i][0:1] != '@':
            bot.send_message(message.chat.id, "Gimme usernames correctly")
            return None
        users_called.append(message_as_list[i][1:])
    if are_username_in_db(conn, message, users_called) is None:
        return None
    return users_called


def return_list_of_usernames_if_correct(conn, message, message_as_list):
    """
        return a list within all the username without the one which will call the bot
        :param conn:
        :param message: the obg message
        :param message_as_list: the list of username
        :return: None if isn't correct - will give response
        """
    users_called = []
    for i in range(len(message_as_list)):
        if message_as_list[i][0:1] != '@':
            bot.send_message(message.chat.id, "Gimme usernames correctly")
            return None
        users_called.append(message_as_list[i][1:])
    if are_username_in_db(conn, message, users_called) is None:
        return None
    return users_called


def are_username_in_db(conn, message, users_called):
    group_id = message.chat.id
    caller = message.from_user.username
    if len(users_called) == 0:
        bot.send_message(message.chat.id, "Bro, i need one or more usernames")
        return None
    for user in users_called:
        if not db.is_username_on_db(conn, user, group_id):
            bot.send_message(message.chat.id, "Bro pls, give me real usernames or tell them to use /addMe")
            return None
        else:
            if user == caller:
                bot.send_message(message.chat.id, "Oh c'mon, ti spacco")
                return None
    return True


def is_caller_on_db(conn, id_chat, users_caller):
    """
    :param conn:
    :param id_chat:
    :param users_caller:
    :return: True if user is on db, False Otherwise
    """
    if not db.is_username_on_db(conn, users_caller[0], int(id_chat)):
        bot.send_message(id_chat, "to abuse me, you need to be added with /addMe")
        return False
    return True


bot.polling();
