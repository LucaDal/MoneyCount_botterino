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
    # bot.send_message(message.chat.id, message)
    pass


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Nice, I'll take account your debts \nbut first write /addMe")


@bot.message_handler(commands=['help'])
def help_message(message):
    help_mes = "/addMe\nNeeded to use me\n-----------------\n" \
               "/addExEqually <value> <username>[other usernames]\nIt'll add the value divided by you and others in " \
               "their account(you're excluded)\n-----------------\n" \
               "/addExTo <value> <username>\nSet an expense just for someone(entire price added to him)\n-----------------\n"\
               "/balanceWith <username>\nIt will tell you the balance between you and the username\n-----------------\n" \
               "/balanceGroup\nIt will tell the balance between you and each one of the group"
    bot.send_message(message.chat.id, help_mes)


@bot.message_handler(commands=['addExEqually'])
def add_equal_to(message):
    """
    aggiungi a tutti la spesa in modo uguale - tranne a chi la chiama
    """
    conn = is_all_right(message)
    if conn is False:
        return
    message_as_list = get_list_from_message(message)
    if len(message_as_list) == 0:
        bot.send_message(message.chat.id, "Bro, i need one username")
        return
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
    bot.send_message(message.chat.id, "{} ha indebitato{} di:\n{}€".format(message.from_user.username, str_user, value))
    conn.close()


@bot.message_handler(commands=['addExTo'])
def add_to(message):
    """
    inserisce la spesa solo ad una persona
    """
    conn = is_all_right(message)
    if conn is False:
        return
    message_as_list = get_list_from_message(message)
    if len(message_as_list) == 0:
        bot.send_message(message.chat.id, "Bro, i need one value and a username")
        return
    val = return_value_if_correct(message_as_list[0])
    if val is None:
        bot.send_message(message.chat.id, "First input needed is numeric moron")
        return
    username = return_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list)
    if username is None:
        return
    if len(username) != 1:
        bot.send_message(message.chat.id, "Give me just one username")
        return
    try:
        db.insert_transactions_into_db(conn, message.from_user.id, username, float(val), message.chat.id)
    except:
        bot.send_message(message.chat.id, "Something went wrong diomaialo")
        return
    bot.send_message(message.chat.id, "Expense added to{}".format(username[0]))
    conn.close()


@bot.message_handler(commands=['balanceGroup'])
def get_balance(message):
    """
    print into the chat the balance of each one
    """
    conn = is_all_right(message)
    if conn is False:
        return
    list_group = db.get_list_user_group(conn, message.chat.id)
    list_group.remove(message.from_user.username)
    for user in list_group:
        get_balance_with(message, user)


@bot.message_handler(commands=['balanceWith'])
def get_balance_with(message, user=""):
    """
    print into the chat the balance of each one
    """
    conn = is_all_right(message)
    if conn is False:
        return
    message_as_list = get_list_from_message(message)
    user_called = return_list_of_usernames_if_correct(conn, message, message_as_list)
    if user_called is None:
        if user != "":
            user_called = [user]
        else:
            bot.send_message(message.chat.id, "Bro, i need one username")
            return
    if len(user_called) != 1:
        bot.send_message(message.chat.id, "Gimme just one username ")
        return
    try:
        bal = db.get_balance_from(conn, message.from_user.id, user_called[0], message.chat.id)
        if bal < 0:
            bot.send_message(message.chat.id, "Sei in crick con {} di:\n{}€".format(user_called[0], bal))
        elif bal == 0:
            bot.send_message(message.chat.id, "non sei in crick con {}:\n{}€, gg".format(user_called[0], 0))
            db.remove_transactions_between(conn, message.from_user.id, db.get_id_from_username(conn, user_called[0]),
                                           message.chat.id)
        else:
            bot.send_message(message.chat.id, "{} è in crick con te di:\n{}€".format(user_called[0], bal))
    finally:
        conn.close()


@bot.message_handler(commands=['addMe'])
def add_me(message):
    """
    add users to set them into the db
    person(id_person,name,username,portfolio,group_id)
    """
    conn = db.create_connection()
    if conn is None:
        bot.send_message(message.chat.id, "Problems with data base")
        return
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
    string_splitted = str.split(string)
    listToReturn = []
    for string in string_splitted:
        listToReturn.append(string)
    return listToReturn


def return_value_if_correct(value):
    """
    given a value it test if it has ',' or other char and if is a number obv
    """
    valueTest = value.replace(',', '.')
    if valueTest.replace('.', '').isnumeric():
        try:
            val = float(valueTest)
        except:
            return None
        val = truncate(val)
    else:
        return None
    return val


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


def is_all_right(message):
    """
    :param message:
    :return: False id something fails, the connection instead
    """
    conn = db.create_connection()
    if conn is None:
        bot.send_message(message.chat.id, "Problems with data base")
        return False
    if not is_caller_on_db(conn, message.chat.id, [message.from_user.username]):
        return False
    return conn


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


bot.polling()
