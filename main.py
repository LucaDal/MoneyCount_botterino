import os
import telebot
import dataBase as db
import json

file = open(".env", "r")
env = json.load(file)
#KEY_TOKEN = env['KEY_TOKEN']
KEY_TOKEN = "5088120040:AAGEbLgK1eXdykfFHUCOxP_ZC0Jhxf2JnSE"
bot = telebot.TeleBot(KEY_TOKEN)
file.close()


@bot.message_handler(commands=['info'])
def info(message):
    # bot.send_message(message.chat.id, message)
    pass


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Ciao! i comandi sono:")
    help_message(message)


@bot.message_handler(commands=['help'])
def help_message(message):
    help_mes = "/addMe\nNecessario per essere aggiunto al db.\n-----------------\n" \
               "/addExEqTo <prezzo> <username>[altri username] || 'all'\nAggiunge il prezzo diviso il numero totale" \
               "di partecipanti, escluso chi la chiama.\n-----------------\n" \
               "/addExTo <prezzo> <username>\nAggiunge la spesa all'username inserito.\n-----------------\n"\
               "/debitWith <username>\nBilancio tra chiamante e l'username.\n-----------------\n" \
               "/debitGroup\nBilancio tra chiamante e ognuno del gruppo.\n-----------------\n" \
               "/balanceWith <username> || 'all'\nBilancia il conto a 0€ con l'username inserito (o con tutti)" \
               "se sei in credito.\n-----------------\n" \
               "/updateMe\nAggiornamento username in caso di cambio.\n-----------------\n" \
               "# Gli username devono iniziare con @.\n# Se non ricevi risposta hai mancato qualcosa, " \
               "o mi hanno ammazzato il server.\n# Valori negativi non sono ammessi."
    bot.send_message(message.chat.id, help_mes)


@bot.message_handler(commands=['addExEqTo'])
def add_equal_to(message):
    """
    aggiungi a tutti la spesa in modo uguale - tranne a chi la chiama
    """
    conn = is_connection_all_right(message)
    if conn is False:
        return
    message_as_list = get_list_from_message(message)
    if len(message_as_list) == 0:
        bot.send_message(message.chat.id, "Bro, i need one username or type 'all'")
        return
    price_to_divide = return_value_if_correct(message_as_list[0])
    if price_to_divide is None:
        bot.send_message(message.chat.id, "Gimme money correctly bruh")
        return
    elif price_to_divide == 0:
        bot.send_message(message.chat.id, "Bro, non provarci mai più!")
        return
    caller = message.from_user.username
    users_called = []
    dividendo = 0
    if message_as_list[1] == "all":
        users_called = db.get_list_user_group(conn, message.chat.id)
        dividendo = len(users_called)
        users_called.remove(caller)
        if users_called is None:
            bot.send_message(message.chat.id, "No users to add the expense")
            return
    else:
        users_called = return_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list)
        if users_called is None:
            return
        dividendo = len(message_as_list)
    value = truncate(price_to_divide / dividendo)
    try:
        db.insert_transactions_into_db(conn, message.from_user.id, users_called, float(value), message.chat.id)
    except:
        bot.send_message(message.chat.id, "Something went wrong diomaialo")
        return
    str_user = get_string_of_usernames(users_called)
    bot.send_message(message.chat.id,
                     "{} ha indebitato{} di:\n{}€".format(message.from_user.username, str_user, value, 2))
    conn.close()


def get_string_of_usernames(usernames_list):
    str_user = ""
    for i in range(len(usernames_list)):
        if i == usernames_list or i == 0:
            div = ""
        else:
            div = ","
        str_user = "{}{} {}".format(str_user, div, usernames_list[i])
    return str_user


@bot.message_handler(commands=['balanceWith'])
def balance_with(message):
    conn = is_connection_all_right(message)
    if conn is None:
        return
    list_from_msg = get_list_from_message(message)
    list_debtors = []
    caller = message.from_user.username
    if list_from_msg[0] == "all":
        for user in db.get_list_user_group(conn, message.chat.id):
            if user != caller:
                euro = db.get_balance_from(conn, message.from_user.id, user,
                                           message.chat.id)
                if euro > 0:
                    list_debtors.append(user)
                    db.remove_transactions_between(conn, message.from_user.id, db.get_id_from_username(conn, user),
                                                   message.chat.id)
    else:
        user_in_list = return_list_of_usernames_if_correct(conn, message, list_from_msg)
        if user_in_list is None:
            return
        if len(user_in_list) != 1:
            bot.send_message(message.chat.id, "Considererò solo il primo username")
        euro = db.get_balance_from(conn, message.from_user.id, user_in_list[0],
                                   message.chat.id)
        if euro > 0:
            list_debtors.append(user_in_list[0])
            db.remove_transactions_between(conn, message.from_user.id, db.get_id_from_username(conn, user_in_list[0]),
                                           message.chat.id)
    str_username = get_string_of_usernames(list_debtors)
    if str_username == "":
        bot.send_message(message.chat.id, "Niente da bilanciare.")
    else:
        bot.send_message(message.chat.id, "Conto bilanciato con:\n{}".format(str_username))


def get_value_and_username_connection(message):
    """
    handled error within this function
    :return: the first value of the string, one single username(if more it will advise the user) and the connection
    """
    conn = is_connection_all_right(message)
    if conn is False:
        return None
    message_as_list = get_list_from_message(message)
    if len(message_as_list) == 0:
        bot.send_message(message.chat.id, "Mi serve il prezzo e l'username.")
        return None
    val = return_value_if_correct(message_as_list[0])
    if val is None:
        bot.send_message(message.chat.id, "Il primo valore è numerico.")
        return None
    elif val == 0:
        bot.send_message(message.chat.id, "Non darmi prezzo 0 per favore.")
        return None
    username = return_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list)
    if username is None:
        return None
    if len(username) != 1:
        bot.send_message(message.chat.id, "Necessito di un solo username")
        return None
    return val, username, conn


@bot.message_handler(commands=['addExTo'])
def add_to(message):
    """
    inserisce la spesa solo ad una persona
    """
    return_value = get_value_and_username_connection(message)
    if return_value is None:
        return
    val = return_value[0]
    username = return_value[1]
    conn = return_value[2]
    try:
        db.insert_transactions_into_db(conn, message.from_user.id, username, float(val), message.chat.id)
    except:
        bot.send_message(message.chat.id, "Qualcosa è andato storto...")
        return
    bot.send_message(message.chat.id, "Spesa aggiunta a: {}".format(username[0]))
    conn.close()


@bot.message_handler(commands=['updateMe'])
def update_username(message):
    conn = db.create_connection()
    if conn is None:
        return
    if db.is_username_on_db(conn, message.from_user.username, message.chat.id):
        bot.send_message(message.chat.id, "Niente da aggiornare")
        return
    elif db.is_user_on_db(conn, message.from_user.id, message.chat.id):
        db.update_username(conn, message.from_user.id, message.chat.id, message.from_user.username)
        bot.send_message(message.chat.id, "Username aggiornato!")
    else:
        bot.send_message(message.chat.id, "Non sei nel mio db! usa /addMe")
    conn.close()


@bot.message_handler(commands=['debitGroup'])
def get_debit_group(message):
    """
    print into the chat the balance of each one
    """
    conn = is_connection_all_right(message)
    if conn is False:
        return
    list_group = db.get_list_user_group(conn, message.chat.id)
    list_group.remove(message.from_user.username)
    message.text = ""
    # is needed otherwise when i call get_balance_with it will search for usernames into this text
    if len(list_group) != 0:
        for user in list_group:
            get_balance_with(message, user, True)
    else:
        bot.send_message(message.chat.id, "Nessuno nel gruppo :c")

    conn.close()


@bot.message_handler(commands=['debitWith'])
def get_balance_with(message, user="", called_by_debit_group=False):
    """
    print into the chat the balance of each one
    """
    conn = is_connection_all_right(message)
    if conn is False:
        return
    user_called = []
    if called_by_debit_group is False:
        user_called = return_list_of_usernames_if_correct(conn, message, get_list_from_message(message))
        if user_called is None:
            return
    if called_by_debit_group is True:
        if user != "":
            user_called.append(user)
        else:
            return
    if len(user_called) != 1:
        bot.send_message(message.chat.id, "Dammi un solo username")
        return
    try:
        bal = truncate(db.get_balance_from(conn, message.from_user.id, user_called[0], message.chat.id), 2)
        if bal < 0:
            bot.send_message(message.chat.id, "Devi {}€\na: {}".format(abs(bal), user_called[0]))
        elif bal == 0:
            bot.send_message(message.chat.id, "Sei in pari con:\n{}".format(user_called[0]))
            db.remove_transactions_between(conn, message.from_user.id, db.get_id_from_username(conn, user_called[0]),
                                           message.chat.id)
        else:
            bot.send_message(message.chat.id, "{} ti deve:\n{}€".format(user_called[0], bal))
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
        bot.send_message(message.chat.id, "Problemi con il db.")
        return
    user = (message.from_user.id, message.from_user.username, message.chat.id)
    if db.insert_user_into_db(conn, user) < 0:
        bot.send_message(message.chat.id, "Sei dentro.")
    else:
        print("Aggiunto: {}".format(user))
        bot.send_message(message.chat.id, "{} aggiunto.".format(message.from_user.first_name))
        conn.close()
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
            bot.send_message(message.chat.id, "Dammi l'username correttamente inserendo la @")
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
            bot.send_message(message.chat.id, "Dammi l'username correttamente inserendo la @")
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
            bot.send_message(message.chat.id, "Username errato o da aggiungere al db")
            return None
        else:
            if user == caller:
                bot.send_message(message.chat.id, "Ti picchio")
                return None
    return True


def is_connection_all_right(message):
    """
    :param message:
    :return: False id something fails, the connection instead
    """
    conn = db.create_connection()
    if conn is None:
        bot.send_message(message.chat.id, "Problemi con il db")
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
        bot.send_message(id_chat, "Per usarmi, Necessiti di essere aggiunto con /addMe")
        return False
    return True


bot.infinity_polling(timeout=10, long_polling_timeout=5)
# bot.polling()
