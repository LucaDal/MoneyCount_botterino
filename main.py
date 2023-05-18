from time import sleep
from threading import Thread
import schedule
import telebot
import dataBase as db
import json
from utils import create

name_schedule = {}

with open(".env", "r") as file:
    env = json.load(file)
    KEY_TOKEN = env['KEY_TOKEN']
    bot = telebot.TeleBot(KEY_TOKEN)


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, message)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Ciao! i comandi sono:")
    help_message(message)


@bot.message_handler(commands=['help'])
def help_message(message):
    if message.chat.id == message.from_user.id:  # private chat
        help_mes = "/groupDebit [<groupID>]\nBilancio tra chiamante e tutti coloro che sono nel gruppo." \
                   "\n<groupID> necessario solo se mi usi in più gruppi.\n-------------" \
                   "----\n/getGroupID\nRichiedi ID dei gruppi in cui sono utilizzato."
    else:  # Group chat
        help_mes = "/addMe\nNecessario per usarmi.\n-----------------\n" \
                   "/addEq <prezzo> [<username> [altri username]] || ['all']\n" \
                   "Aggiunge il prezzo equamente diviso per il " \
                   "numero totale di partecipanti, escluso il chiamante.\n-----------------\n" \
                   "/add <prezzo> <username>\nAggiunge la spesa intera all'username inserito.\n-----------------\n" \
                   "/debitWith <username>\nBilancio tra chiamante e l'username.\n-----------------\n" \
                   "/debitGroup\nBilancio tra chiamante e ognuno del gruppo.\n-----------------\n" \
                   "/balanceCredit <username> || 'all'\nBilancia il conto a 0€ con l'username inserito (o con tutti)," \
                   " solo se si è in credito.\n-----------------\n" \
                   "/updateMe\nAggiornamento username in caso di cambio.\n-----------------\n" \
                   "# Gli username devono iniziare con @.\n# Se non ricevi risposta qualcosa è andato storto, " \
                   "o il server è giù.\n# Valori negativi non sono ammessi."
    bot.send_message(message.chat.id, help_mes)


@bot.message_handler(commands=['setDutyTurn'])
def set_duty_turn(message):
    conn = db.create_connection()
    if conn is None:
        return
    user_list = get_list_of_usernames_if_correct(conn, message, get_list_from_message(message), True)
    if user_list is None:
        return
    for i in range(len(user_list)):
        db.insert_turn_duty_user_into_db(conn, message.chat.id, user_list[i], i+1)
    bot.send_message(message.chat.id, "turni aggiornati")


def get_username_from_db(id):
    conn = db.create_connection()
    if conn is None:
        username = id
    else:
        username = db.get_username_from_id(conn, id)
    conn.close()
    return username


def schedule_delay(name_task, id_group):
    """
    stops the main task and it will remember after delay_response time!
    :param name_task:
    :param id_group:
    :return:
    """
    username = ""
    for key, val in name_schedule.items():
        if val[0] == name_task and val[1] == id_group:
            schedule.cancel_job(key)
            username = get_username_from_db(val[2])
    bot.send_message(id_group, "{} ti ricordo: {}!".format(username, name_task))


@bot.message_handler(commands=['done', 'fatto', 'ok'])
def job_done(message):  # TODO se tocca al suo turno => stop task
    conn = db.create_connection()
    if conn is None:
        return
    list_turn = db.get_turn_user(conn,message.chat.id)
    if list_turn[0][0] == message.from_user.id:
        db.update_turn_user(conn, message.chat.id, message.from_user.id)
    #set_new_schedule() #TODO richiamare il db e prendere le informazioni
    for key, val in name_schedule.items():
        if val[0] == name_task and val[1] == id_group:
            schedule.cancel_job(key)


def schedule_job(name_task, id_group, id_user_turn, delay_response):
    bot.send_message(id_group, "{} {}".format(get_username_from_db(id_user_turn), name_task))
    # set a reminder
    schedule.every(delay_response).seconds.do(schedule_delay, name_task, id_group)
    ## TODO Aggiungere il task all Dir

def set_new_schedule(conn, name, id_group, frequency, delay_response, id_user_turn):
    """
    it start schedule job, and after some delay, if it won't get a notification that the jobe is done
    then, after delay_response time, it will send new messages
    :param id_user_turn:
    :param name: of the schedule
    :param id_group: id of the chat
    :param frequency: time between notification
    :param delay_response: time before new messages start warning!
    :return: id of the user that has to do this task!
    """
    # db.set_new_schedule(conn, name, id_group, frequency, delay_response)
    tag = schedule.every(frequency).seconds.do(schedule_job, name, id_group, id_user_turn, delay_response)
    name_schedule[tag] = (name, id_group, id_user_turn)
    return True


@bot.message_handler(commands=['setSchedule'])
def new_schedule(message):
    # verifico che esista un ordine da cui partire
    conn = db.create_connection()
    if conn is None:
        return
    order_list = db.get_turn_user(conn, message.chat.id)
    # controllo se esiste un ordine nel gruppo
    if len(order_list) == 0:
        bot.send_message(message.chat.id,
                         "Settate prima i turni")
        conn.close()
        return
    text_list = get_list_from_message(message)
    if len(text_list) != 3:
        bot.send_message(message.chat.id,
                         "Ho bisogno di: frequenza in minuti, ed il tempo d'attesa prima che venga " \
                         "ricordato il task")
        conn.close()
        return
    for index in range(1, 3):
        if not text_list[index].isdigit():
            bot.send_message(message.chat.id, "Inserisci i minuti nel parametro {}".format(index + 1))
            conn.close()
            return
    if int(text_list[1]) < int(text_list[2]):
        bot.send_message(message.chat.id, "Il secondo valore deve essere minore del primo, poiché deve ricordare prima "
                                          "che riaccad")
        conn.close()
        return
    if set_new_schedule(conn, text_list[0], message.chat.id, int(text_list[1]), int(text_list[2]), order_list[0][0]):
        bot.send_message(message.chat.id, "novo schedule \"{}\" settato".format(text_list[0]))
    conn.close()


@bot.message_handler(commands=['getGroupID'])
def get_group_id(message):
    conn = db.create_connection()
    if conn is None:
        return
    text = ""
    group_id_list = db.get_group_list(conn, message.from_user.id)
    lenList = len(group_id_list)
    if lenList > 0:
        for i in range(lenList):
            text += "{}: {}\n".format(i + 1, db.get_group_name_from_id(conn, group_id_list[i][0]))
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Non sei in nessun gruppo")
    conn.close()


@bot.message_handler(commands=['groupDebit'])
def debit_with_group(message):
    conn = db.create_connection()
    if conn is None:
        return
    if db.is_user_on_db(conn, message.from_user.id, None, False):
        group_id_list = db.get_group_list(conn, message.from_user.id)
        if len(group_id_list) == 1:
            get_debit_group(message, group_id_list[0][0], conn)
        else:
            text = get_list_from_message(message)
            if len(text) == 0:
                bot.send_message(message.chat.id, "Inserire l'ID del gruppo: /getGroupID")
                conn.close()
                return
            try:
                value = int(text[0]) - 1
            except ValueError:
                bot.send_message(message.chat.id, "Inserire l'ID del gruppo correttamente")
                conn.close()
                return
            if value >= len(group_id_list) or value < 0:
                bot.send_message(message.chat.id, "ID Gruppo non esistente")
                conn.close()
                return
            get_debit_group(message, group_id_list[0][value], conn)
    else:
        bot.send_message(message.chat.id, "Non sei in nessun gruppo")
    conn.close()


@bot.message_handler(commands=['addEq'])
def add_equal_to(message):
    """
    aggiungi a tutti la spesa in modo uguale - tranne a chi la chiama
    """
    conn = is_connection_all_right(message)
    if conn is False:
        return
    message_as_list = get_list_from_message(message)
    if len(message_as_list) == 0:
        bot.send_message(message.chat.id, "Mi serve almeno un'username o, usa 'all'.")
        return
    price_to_divide = return_value_if_correct(message_as_list[0])
    if price_to_divide is None:
        bot.send_message(message.chat.id, "Inserisci il prezzo correttamente.")
        return
    elif price_to_divide == 0:
        bot.send_message(message.chat.id, ">:[, non provarci mai più!")
        return
    caller = message.from_user.username
    users_called = []
    dividendo = 0
    if message_as_list[1] == "all":
        users_called = db.get_list_user_group(conn, message.chat.id)
        dividendo = len(users_called)
        users_called.remove(caller)
        if not users_called:
            bot.send_message(message.chat.id, "Nessun utente a cui aggiungere la spesa.")
            return
    else:
        users_called = get_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list)
        if not users_called:
            return
        dividendo = len(users_called) + 1
    try:
        value = truncate(price_to_divide / dividendo)
        db.insert_transactions_into_db(conn, message.from_user.id, users_called, float(value), message.chat.id)
    except:
        bot.send_message(message.chat.id, "Qualcosa è andato storto.")
        conn.close()
        return
    str_user = get_string_of_usernames(users_called)
    bot.send_message(message.chat.id,
                     "{} ha indebitato {} di:\n{}€".format(message.from_user.username, str_user, value, 2))
    conn.close()


@bot.message_handler(commands=['balanceCredit'])
def balance_with(message):
    conn = is_connection_all_right(message)
    if conn is None:
        return
    list_from_msg = get_list_from_message(message)
    list_debtors = []
    caller = message.from_user.username
    if not list_from_msg:
        bot.send_message(message.chat.id, "Inserisci l'username o 'all'.")
        conn.close()
        return
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
        user_in_list = get_list_of_usernames_if_correct(conn, message, list_from_msg)
        if user_in_list is None:
            conn.close()
            return
        if len(user_in_list) != 1:
            bot.send_message(message.chat.id, "Considererò solo il primo username.")
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
    conn.close()


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
        bot.send_message(message.chat.id, "Sus.")
        return None
    username = get_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list)
    if username is None:
        bot.send_message(message.chat.id, "Inserisci un username.")
        return None
    if len(username) != 1:
        bot.send_message(message.chat.id, "Necessito di un solo username.")
        return None
    return val, username, conn


@bot.message_handler(commands=['add'])
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
        conn.close()
        return
    bot.send_message(message.chat.id, "Spesa aggiunta a: {}".format(username[0]))
    conn.close()


@bot.message_handler(commands=['updateMe'])
def update_username(message):
    conn = db.create_connection()
    if conn is None:
        return
    if db.is_username_on_db(conn, message.from_user.username, message.chat.id):
        bot.send_message(message.chat.id, "Niente da aggiornare.")
        conn.close()
        return
    elif db.is_user_on_db(conn, message.from_user.id, message.chat.id):
        db.update_username(conn, message.from_user.id, message.chat.id, message.from_user.username)
        bot.send_message(message.chat.id, "Username aggiornato!")
    else:
        bot.send_message(message.chat.id, "Non sei nel mio db! usa /addMe.")
    conn.close()


@bot.message_handler(commands=['debitGroup'])
def get_debit_group(message, group_id=None, conn=None):
    """
    print into the chat the balance of each one
    """
    if conn is None:
        conn = is_connection_all_right(message)
    if conn is False:
        return
    if group_id is None:
        group_id = message.chat.id
    list_group = db.get_list_user_group(conn, group_id)
    list_group.remove(message.from_user.username)
    message.text = ""
    # is needed otherwise when i call get_balance_with it will search for usernames into this text
    if len(list_group) != 0:
        for user in list_group:
            get_balance_with(message, user, True, conn, group_id)
    else:
        bot.send_message(message.chat.id, "Nessuno nel gruppo.")
    conn.close()


@bot.message_handler(commands=['debitWith'])
def get_balance_with(message, user="", called_by_debit_group=False, conn=None, group_id=None):
    """
    print into the chat the balance with the username selected
    """
    if conn is None:
        conn = is_connection_all_right(message)
        if conn is False:
            return
    user_called = []

    if group_id is None:
        group_id = message.chat.id
    if called_by_debit_group is False:
        user_called = get_list_of_usernames_if_correct(conn, message, get_list_from_message(message))
        if user_called is None:
            bot.send_message(message.chat.id, "Dammi un solo username o usa /debitGroup.")
            conn.close()
            return
    else:

        if user != "":
            user_called.append(user)
        else:
            return
    if len(user_called) != 1:
        bot.send_message(message.chat.id, "Dammi un solo username o usa /debitGroup.")
        conn.close()
        return
    try:
        bal = truncate(db.get_balance_from(conn, message.from_user.id, user_called[0], group_id), 2)
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
    if not is_message_in_group(message):
        bot.send_message(message.chat.id, "Non puoi inserirmi in una chat privata, ma solo nei gruppi.\nPotrai però "
                                          "visualizzare le informazioni dei debiti se sei un qualche gruppo.")
        return
    conn = db.create_connection()
    if conn is None:
        bot.send_message(message.chat.id, "Problemi con il db.")
        return
    # add group if not exists
    db.add_new_group(conn, (message.chat.id, message.chat.title))
    user = (message.from_user.id, message.from_user.username, message.chat.id)
    if db.insert_user_into_db(conn, user) < 0:
        bot.send_message(message.chat.id, "Sei gia dentro.")
    else:
        print("Aggiunto: {}".format(user))
        bot.send_message(message.chat.id, "{} aggiunto.".format(message.from_user.first_name))
        conn.close()
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


def get_list_of_usernames_if_correct_first_value_is_numeric(conn, message, message_as_list):
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
            bot.send_message(message.chat.id, "Dammi l'username correttamente inserendo la @.")
            return None
        users_called.append(message_as_list[i][1:])
    if are_username_in_db(conn, message, users_called) is None:
        return None
    return users_called


def get_list_of_usernames_if_correct(conn, message, message_as_list, dont_check_caller=False):
    """
        return a list within all the username without the one which will call the bot
        :param dont_check_caller: added because in schedules i check the usernames
        :param conn:
        :param message: the obg message
        :param message_as_list: the list of username
        :return: None if isn't correct - will give response
        """
    users_called = []
    for i in range(len(message_as_list)):
        if message_as_list[i][0:1] != '@':
            bot.send_message(message.chat.id, "inserisci l'username correttamente inserendo la @.")
            return None
        users_called.append(message_as_list[i][1:])
    if are_username_in_db(conn, message, users_called, dont_check_caller) is None:
        return None
    return users_called


def are_username_in_db(conn, message, users_called, dont_check_caller=False):
    group_id = message.chat.id
    caller = message.from_user.username
    if len(users_called) == 0:
        return None
    for user in users_called:
        if not db.is_username_on_db(conn, user, group_id):
            bot.send_message(message.chat.id, "Username errato o da aggiungere al db.")
            return None
        else:
            if user == caller and dont_check_caller is False:
                bot.send_message(message.chat.id, "Non indebitarti con te stesso.")
                return None
    return True


def is_connection_all_right(message):
    """
    :param message:
    :return: False id something fails, the connection instead
    """
    conn = db.create_connection()
    if conn is None:
        bot.send_message(message.chat.id, "Problemi con il db.")
        return False
    if is_message_in_group(message):
        if not is_caller_on_db(conn, message.chat.id, [message.from_user.username]):
            return False
        return conn
    return False


def is_message_in_group(message):
    if message.chat.type == "group":
        return True
    return False


def is_caller_on_db(conn, id_chat, users_caller):
    """
    :param conn:
    :param id_chat:
    :param users_caller:
    :return: True if user is on db, False Otherwise
    """
    if not db.is_username_on_db(conn, users_caller[0], int(id_chat)):
        bot.send_message(id_chat, "Per usarmi, Necessiti di essere aggiunto con /addMe.")
        return False
    return True


def start_server():
    print("Starting server")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    create()
    Thread(target=schedule_checker).start()
    start_server()
