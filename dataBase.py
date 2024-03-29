import sqlite3
from sqlite3 import Error


def create_connection():
    db_file = r"MoneyCount_tables.db"
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn


def sql_table_statment(conn):
    sql_create_turn_duty_user_table = """CREATE TABLE IF NOT EXISTS turn_duty_user(
                                id_user integer NOT NULL,
                                id_group integer NOT NULL,
                                turn integer NOT NULL,
                                PRIMARY KEY(id_user,id_group),
                                FOREIGN KEY (id_group) REFERENCES group_info(id_group),
                                FOREIGN KEY (id_user) REFERENCES user(id_user)
                                );"""
    sql_create_duty_schedule_table = """CREATE TABLE IF NOT EXISTS duty_schedule(
                                name text NOT NULL,
                                id_group integer NOT NULL,
                                frequency integer NOT NULL,
                                delay_response integer NOT NULL,
                                PRIMARY KEY(name,id_group),
                                FOREIGN KEY (id_group) REFERENCES group_info(id_group)
                                );"""

    sql_create_group_table = """CREATE TABLE IF NOT EXISTS group_info(
                                id_group integer PRIMARY KEY,
                                group_name text NOT NULL
                                );"""

    sql_create_user_table = """CREATE TABLE IF NOT EXISTS user(
                                id_user integer NOT NULL,
                                username text NOT NULL,
                                id_group integer NOT NULL,
                                PRIMARY KEY(id_user,id_group)
                                FOREIGN KEY (id_group) REFERENCES group_info(id_group)
                                );"""

    sql_create_transactions_table = """ CREATE TABLE IF NOT EXISTS transactions (
                                  id integer PRIMARY KEY,
                                  id_payer integer NOT NULL,
                                  id_debtor integer NOT NULL,
                                  id_group integer NOT NULL,
                                  value real,
                                  FOREIGN KEY (id_payer) REFERENCES user(id_user),
                                  FOREIGN KEY (id_debtor) REFERENCES user(id_user),
                                  FOREIGN KEY (id_group) REFERENCES group_info(id_group)
                                  );
                                  """
    deploy_tables(conn, sql_create_duty_schedule_table)
    deploy_tables(conn, sql_create_turn_duty_user_table)
    deploy_tables(conn, sql_create_group_table)
    deploy_tables(conn, sql_create_user_table)
    deploy_tables(conn, sql_create_transactions_table)


def update_turn_user(conn, id_group, id_user):
    """
    aggiorna la tabella decrementando l'ordine e mettendo il primo in fondo alla fila
    :param id_user:
    :param conn:
    :param id_group:
    """
    ## TODO migliorare
    sql = "SELECT MAX(turn) FROM turn_duty_user where id_group = ? GROUP BY turn"
    max_turn = execute_sql_without_commit(conn, sql, (id_group,))[0][0]
    print(max_turn)
    sql = "DELETE FROM turn_duty_user WHERE id_user = ? AND id_group = ?"
    deploy_commit(conn, sql, (id_user, id_group))
    sql = "UPDATE turn_duty_user SET turn = turn - 1 WHERE id_group = ?"
    deploy_commit(conn, sql, (id_group,))
    query = ''' INSERT INTO turn_duty_user(id_user,id_group,turn) VALUES(?,?,?) '''
    deploy_commit(conn, query, (id_user, id_group, max_turn))


def get_duty_schedule_by_group_id(conn, id_group):
    """"
    :param conn:
    :param id_group:
    :return: name ,id_group ,frequency,delay_response,
    """
    sql = "SELECT * FROM duty_schedule WHERE ? = id_group"
    return execute_sql_without_commit(conn, sql, (id_group,))


def delete_if_duty_already_setted(conn, name, id_group):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM duty_schedule WHERE ? = name AND ? = id_group", (name, id_group))
    value = cur.fetchall()
    if value[0][0] == 1:
        sql = "DELETE FROM duty_schedule WHERE name = ? AND id_group = ?"
        deploy_commit(conn, sql, (name, id_group))
    return False


def get_turn_user_in_order_asc(conn, id_group):
    cur = conn.cursor()
    cur.execute("SELECT id_user FROM turn_duty_user WHERE ? = id_group ORDER BY turn ASC", (id_group,))
    return cur.fetchall()


def set_new_schedule(conn, name, id_group, frequency, delay_response):
    query = ''' INSERT INTO duty_schedule(name,id_group,frequency,delay_response) VALUES(?,?,?,?) '''
    deploy_commit(conn, query, (name, id_group, frequency, delay_response))
    return


def get_group_name_from_id(conn, id_group):
    cur = conn.cursor()
    cur.execute("SELECT group_name FROM group_info WHERE ? = id_group", (id_group,))
    return cur.fetchall()[0][0]


def get_group_list(conn, id_user):
    cur = conn.cursor()
    cur.execute("SELECT id_group FROM user WHERE ? = id_user", (id_user,))
    return cur.fetchall()


def is_user_on_db(conn, id_user, id_group, need_group_id=True):
    """
    it uses the id of the user
    :param need_group_id: if False it only check if the id is on the db (for Private chat)
    :param conn: db connection
    :param id_user: id of the user on telegram
    :param id_group: if related to the chat which is writing
    :return: True if exists, False otherwise
    """
    cur = conn.cursor()
    if need_group_id:
        cur.execute("SELECT COUNT(1) FROM user WHERE ? = id_user AND ? = id_group", (id_user, id_group))
        value = cur.fetchall()
        if value[0][0] == 1:
            return True
        return False
    else:
        cur.execute("SELECT COUNT(1) FROM user WHERE ? = id_user", (id_user,))
        value = cur.fetchall()
        if value[0][0] > 0:
            return True
        return False


def is_username_on_db(conn, username, id_group):
    """
    it uses the id of the user
    :param conn: db connection
    :param username: username of the user on telegram
    :param id_group: if related to the chat which is writing
    :return: True if exists, False otherwise
    """
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM user WHERE ? = username AND ? = id_group", (username, id_group))
    value = cur.fetchall()
    if value[0][0] == 1:
        return True
    return False


def insert_user_into_db(conn, user):
    """
    Create a new user into the user table
    user = (id_user,username,id_group)
    :return: -1 if is already into the same group
    """
    if is_user_on_db(conn, user[0], user[2]):
        return -1
    else:
        sql = ''' INSERT INTO user(id_user,username,id_group) VALUES(?,?,?) '''
        deploy_commit(conn, sql, user)
        return 0


def add_new_group(conn, group):
    # check if group already exists
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM group_info WHERE ? = id_group", (group[0],))
    value = cur.fetchall()
    if value[0][0] == 0:
        print("Group added: {}".format(group[1]))
        sql = ''' INSERT INTO group_info(id_group,group_name) VALUES(?,?) '''
        deploy_commit(conn, sql, group)


def update_username(conn, id_user, id_group, username):
    sql = "UPDATE user SET username = ? WHERE id_user = ? AND id_group = ?"
    deploy_commit(conn, sql, (username, id_user, id_group))


def insert_turn_duty_user_into_db(conn, id_group, user, turn):
    sql = ''' INSERT INTO turn_duty_user(id_group,id_user,turn) VALUES(?,?,?) '''
    deploy_commit(conn, sql, (id_group, get_id_from_username(conn, user), turn))


def insert_transactions_into_db(conn, id_caller, list_usernames, value, id_group):
    """
    Create a new transaction into the transaction table
    and it will update the portfolio directly
    passare id,payer,payer,value
    :param: caller: the username of the caller
    :param: list_usernames:
    """
    for debtor in list_usernames:
        sql = ''' INSERT INTO transactions(id_payer,id_debtor,id_group,value) VALUES(?,?,?,?) '''
        deploy_commit(conn, sql, (id_caller, get_id_from_username(conn, debtor), id_group, value))


def get_id_from_username(conn, username):
    sql = "SELECT id_user FROM user WHERE username = ?"
    return execute_sql_without_commit(conn, sql, (username,))[0][0]


def get_username_from_id(conn, id):
    sql = "SELECT username FROM user WHERE id_user = ?"
    return execute_sql_without_commit(conn, sql, (id,))[0][0]


def remove_transactions_between(conn, id_payer, id_debtor, id_group):
    sql = "DELETE FROM transactions WHERE id_payer = ? AND id_debtor = ? AND id_group = ?"
    deploy_commit(conn, sql, (id_payer, id_debtor, id_group))
    deploy_commit(conn, sql, (id_debtor, id_payer, id_group))


def get_balance_from(conn, id_payer, debtor, id_group):
    """
    will return the amount that the debtor has to give you
    """
    id_debtor = get_id_from_username(conn, debtor)
    sql = "SELECT SUM(value) FROM transactions WHERE id_payer = ? AND id_debtor = ? AND id_group = ?"
    val_caller = execute_sql_without_commit(conn, sql, (id_payer, id_debtor, id_group))[0][0]
    if val_caller is None:
        val_caller = 0
    sql = "SELECT SUM(value) FROM transactions WHERE id_payer = ? AND id_debtor = ? AND id_group = ?"
    val_debtor = execute_sql_without_commit(conn, sql, (id_debtor, id_payer, id_group))[0][0]
    if val_debtor is None:
        val_debtor = 0
    return float(val_caller) - float(val_debtor)


def get_list_user_group(conn, id_group):
    sql = "SELECT username FROM user WHERE id_group = ?"
    row = execute_sql_without_commit(conn, sql, (id_group,))
    user_list = []
    for user in row:
        user_list.append(user[0])
    return user_list


def execute_sql_without_commit(conn, sql, obg):
    """
    :param conn:
    :param sql: query
    :param obg: tuple with value to insert into the query
    :return: the list fetched
    """
    cur = conn.cursor()
    cur.execute(sql, obg)
    return cur.fetchall()


def deploy_commit(conn, sql, obg):
    cur = conn.cursor()
    cur.execute(sql, obg)
    conn.commit()


def deploy_tables(conn, sql):
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)


def call_create_tables():
    conn = create_connection()
    if conn is not None:
        print("sto creando le tabelle")
        sql_table_statment(conn)
    else:
        print("Error! cannot create the database connection.")
