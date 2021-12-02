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
    help_mes = "/addMe: will add you into db\n" \
               "/addEqualTo <value> <Usernames>[others]: price divided by you and others\n"

    bot.send_message(message.chat.id, help_mes)


@bot.message_handler(commands=['addEqualTo'])  # TODO aggiungere la spesa a tutti gli altri
def add_equal_to(message):
    """
    aggiungi a tutti la spesa in modo uguale - tranne a chi la chiama
    """
    message_as_list = get_list_from_message(message)
    price_to_divide = return_value_if_correct(message_as_list[0])
    if price_to_divide is None:
        bot.send_message(message.chat.id, "Gimme money correctly bruh")
        return
    elif price_to_divide == 0:
        bot.send_message(message.chat.id, "Brutto coglione, non provarci mai più!")
        return

    conn = db.create_connection()
    users_called = return_list_of_usernames_if_correct(conn, message, message_as_list)
    if users_called is None:
        conn.close()
        return
    value = truncate(price_to_divide / (len(message_as_list)))
    db.insert_transactions_into_db(conn, message.from_user.username, users_called, value,message.chat.id)
    bot.send_message(message.chat.id, "{} ti ha indebitato di:\n{}€".format(message.from_user.username, value))#TODO aggiungere la lista delle persone indebitate
    conn.close()


@bot.message_handler(commands=['addTo'])  # TODO da finire
def addTo(message):
    """
    inserisce la spesa solo ad una persona
    """
    # dividendo = len(db.keys())
    # if (dividendo == 0):
    #  bot.send_message(message.chat.id,"no one signed to me :c")
    #  return
    # price = priceToDivide/dividendo
    # bot.send_message(message.chat.id,price)


@bot.message_handler(commands=['balance'])
def get_balance(message):
    """
    print into the chat the balance of each one
    """

    # bot.send_message(message.chat.id,response)


@bot.message_handler(commands=['addMe'])
def add_me(message):
    """
    add users to set them into the db
    person(id_person,name,username,portfoglio,group_id)
    """
    conn = db.create_connection()
    if conn is not None:
        user = (int(message.from_user.id), str(message.from_user.first_name), str(message.from_user.username), 0,
                int(message.chat.id))
        if db.insert_user_into_db(conn, user) < 0:
            bot.send_message(message.chat.id, "Nope")
        else:
            print("Aggiunto: {}".format(user))
            bot.send_message(message.chat.id, "oky, {}".format(message.from_user.first_name))
            conn.close()
    else:
        bot.send_message(message.chat.id, "wait, qualcosa non funge")
        conn.close()


def get_string_from_message(message):
    myList = list(message.text)
    mySecondList = []
    startInserting = False
    for i in myList:
        if (startInserting):
            mySecondList.append(i)
        if (startInserting == False and i == ' '):
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
    if (valueTest.replace('.', '').isnumeric()):
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


def return_list_of_usernames_if_correct(conn, message, messageAsList):
    users_called = []
    for i in range(1, len(messageAsList)):
        if (messageAsList[i][0:1] != '@'):
            return None
        users_called.append(messageAsList[i][1:])
    if (are_username_in_db(conn, message, users_called) is None):
        return None
    return users_called


def are_username_in_db(conn, message, users_called):
    group_id = message.chat.id
    caller = message.from_user.username
    if (len(users_called) == 0):
        bot.send_message(message.chat.id, "bro, i need one or more usernames")
        return None
    for user in users_called:
        if (not db.is_username_on_db(conn, user, group_id)):
            bot.send_message(message.chat.id, "bro pls, give me real usernames or tell them to use /addMe")
            return None
        else:
            if (user == caller):
                bot.send_message(message.chat.id, "oh c'mon, do you really wanna have credit with yourself?")
                return None
    return True


bot.polling();
