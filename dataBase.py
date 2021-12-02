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
                                portfolio real DEFAULT 0,
                                id_group integer,
                                PRIMARY KEY(id_user,id_group)
                                );"""

    sql_create_transactions_table = """ CREATE TABLE IF NOT EXISTS transactions (
                                  id integer PRIMARY KEY,
                                  payer integer NOT NULL,
                                  debtor integer NOT NULL,
                                  value real,
                                  FOREIGN KEY (payer) REFERENCES user(id_user),
                                  FOREIGN KEY (debtor) REFERENCES user(id_user)
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
    if is_user_on_db(conn, user[0], user[4]):
        return -1
    else:
        sql = ''' INSERT INTO user(id_user,name,username,portfolio,id_group) VALUES(?,?,?,?,?) '''
        deploy_commit(conn, sql, user)
        return 0


def insert_transactions_into_db(conn, caller, list_usernames, value, id_group):
    """
    Create a new conto into the transaction table
    passare id,payer,payer,value
    """
    for debtor in list_usernames:
        sql = ''' INSERT INTO transactions(payer,debtor,value)
            VALUES(?,?,?) '''
        update_portfolio(conn, debtor, value, id_group)
        deploy_commit(conn, sql, (caller, debtor, value))


def update_portfolio(conn, id_user, value, id_group):
    sql = ''' UPDATE user set portfolio = portfolio ADD ? WHERE id_user = ? AND id_group = ? '''
    deploy_commit(conn, sql, (value, id_user, id_group))


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

    # with conn:
    # create a new project
    #     user = ()
    #     insert_user(conn, user)
