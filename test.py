import dataBase as db
import os
import sys

def delete_tables():
    os.remove("MoneyCount_tables.db")
    print("tables removed")


def main():

    arguments = sys.argv
    if len(arguments) != 2:
        exit(1)
    try:
        print(globals().get(arguments[1])())
    except:
        exit(1)


def print_tables():
    conn = db.create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user")
    value = cur.fetchall()
    for val in value:
        print(val)
    cur.execute("SELECT * FROM transactions")
    value = cur.fetchall()
    for val in value:
        print(val)
    cur.close()
    conn.close()

def create():
    if not os.path.exists("./MoneyCount_tables.db"):
        f = open('MoneyCount_tables.db', 'w')
        f.close()
        db.call_create_tables()


def query():
    conn = db.create_connection()
    cur = conn.cursor()
    add_Lorenzo_sql = "INSERT INTO user(id_user,name,username,id_group) VALUES(876947202, 'Straptoc', 'Straptoc', -648429536)"
    add_user_sql = "INSERT INTO user(id_user,username,id_group) VALUES(3,'bot3', 461718130)"
    to_debug = "INSERT INTO transactions(id_payer,id_debtor,id_group,value) VALUES(461718130,3,461718130,2)"
    cur.execute(to_debug)
    val = cur.fetchall()
    print(val)
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
