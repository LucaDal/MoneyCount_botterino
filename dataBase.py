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


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def sql_table_statment(
        conn):  # TODO aggiungere id_group alle transizioni perche se ho piu persone in gruppi diversi -> crasha il db
    sql_create_user_table = """CREATE TABLE IF NOT EXISTS user (
                                id_user integer,
                                name text NOT NULL,
                                username text NOT NULL,
                                id_group integer,
                                PRIMARY KEY(id_user,id_group)
                                );"""

    sql_create_transactions_table = """ CREATE TABLE IF NOT EXISTS transactions (
                                  id integer PRIMARY KEY,
                                  id_payer integer NOT NULL,
                                  id_debtor integer NOT NULL,
                                  id_group integer NOT NULL,
                                  value real,
                                  FOREIGN KEY (id_payer) REFERENCES user(id_user),
                                  FOREIGN KEY (id_debtor) REFERENCES user(id_user)
                                  );
                                  """
    deploy_tables(conn, sql_create_user_table)
    deploy_tables(conn, sql_create_transactions_table)


def is_user_on_db(conn, id_user, id_group):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM user WHERE ? = id_user AND ? = id_group", (id_user, id_group))
    value = cur.fetchall()
    if value[0][0] == 1:
        return True


def is_username_on_db(conn, username, id_group):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM user WHERE ? = username AND ? = id_group", (username, id_group))
    value = cur.fetchall()
    if (value[0][0] == 1):
        return True


def insert_user_into_db(conn, user):
    """
    Create a new user into the user table
    user = (id_user,name,username,portfolio,id_group)
    :return: -1 if is already into the same group
    """
    if is_user_on_db(conn, user[0], user[3]):
        return -1
    else:
        sql = ''' INSERT INTO user(id_user,name,username,id_group) VALUES(?,?,?,?) '''
        deploy_commit(conn, sql, user)
        return 0


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
