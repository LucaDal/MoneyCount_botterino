import os
import telebot
import dataBase as db
import json

file = open(".env", "r")
env = json.load(file)
KEY_TOKEN = env['KEY_TOKEN']
print(KEY_TOKEN)
bot = telebot.TeleBot(KEY_TOKEN)
file.close()

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, message)


@bot.message_handler(commands=['addEqualTo'])  # TODO aggiungere la spesa a tutti gli altri
def addEveryOne(message):
    """
    aggiungi a tutti la spesa in modo uguale - tranne a chi la chiama
    """
    messageAsList = getListFromMessage(message)
    priceToDivide = return_value_if_correct(messageAsList[0])
    if (priceToDivide is None):
        bot.send_message(message.chat.id, "Gimme money correctly bruh")
        return
    elif (priceToDivide == 0):
        bot.send_message(message.chat.id, "Brutto coglione, non provarci mai più!")
        return

    conn = db.create_connection()
    usersCalled = return_list_of_usernames_if_correct(conn, message, messageAsList)
    if (usersCalled is None):
        conn.close()
        return
    value = truncate(priceToDivide / (len(messageAsList)))
    db.insert_transactions_into_db(conn, message.from_user.username, usersCalled, value)
    bot.send_message(message.chat.id, "{} ti ha indebitato di {}".format(message.from_user.username,value))
    conn.close()


@bot.message_handler(commands=['addTo'])  ## TODO da finire
def addTo(message):
    """
    inserisce la spesa divisa per il totale delle persone coinvolte (chiamante compreso)
    """
    # dividendo = len(db.keys())
    # if (dividendo == 0):
    #  bot.send_message(message.chat.id,"no one signed to me :c")
    #  return
    # price = priceToDivide/dividendo
    # bot.send_message(message.chat.id,price)


@bot.message_handler(commands=['balance'])
def getBalance(message):
    """
    print into the chat the balance of each one
    """

    # bot.send_message(message.chat.id,response)


@bot.message_handler(commands=['addMe'])
def addMe(message):
    """
    add users to set them into the db
    person(id_person,name,username,portfoglio,group_id)
    """
    conn = db.create_connection()
    if conn is not None:
        user = (int(message.from_user.id), str(message.from_user.first_name), str(message.from_user.username), 0,
                int(message.chat.id))
        if (db.insert_user_into_db(conn, user) < 0):
            bot.send_message(message.chat.id, "Nope")
        else:
            print("Aggiunto: {}".format(user))
            bot.send_message(message.chat.id, "oky, {}".format(message.from_user.first_name))
            conn.close()
    else:
        bot.send_message(message.chat.id, "wait, qualcosa non funge")
        conn.close()


def getStringFromMessage(message):
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


def getListFromMessage(message):
    string = getStringFromMessage(message)
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

def truncate(num,n=2):
    temp = str(num)
    for x in range(len(temp)):
        if temp[x] == '.':
            try:
                return float(temp[:x+n+1])
            except:
                return float(temp)
    return float(temp)

def return_list_of_usernames_if_correct(conn, message, messageAsList):
    usersCalled = []
    for i in range(1, len(messageAsList)):
        if (messageAsList[i][0:1] != '@'):
            return None
        usersCalled.append(messageAsList[i][1:])
    if (are_username_in_db(conn, message, usersCalled) is None):
        return None
    return usersCalled


def are_username_in_db(conn, message, usersCalled):
    group_id = message.chat.id
    caller = message.from_user.username
    if (len(usersCalled) == 0):
        bot.send_message(message.chat.id, "bro, i need one or more usernames")
        return None
    for user in usersCalled:
        if (not db.is_username_on_db(conn, user, group_id)):
            bot.send_message(message.chat.id, "bro pls, give me real usernames or tell them to use /addMe")
            return None
        else:
            if (user == caller):
                bot.send_message(message.chat.id, "oh c'mon, do you really wanna have credit with yourself?")
                return None
    return True


bot.polling();