import dataBase as db
import os
import sys


def create():
    print("Cristo")


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
    cur.execute("SELECT portfolio FROM user WHERE id_user = 461718130 AND id_group = -648429536")
    val = cur.fetchall()
    print(val)
    sql = "UPDATE user SET portfolio = ? WHERE id_user = 461718130 AND id_group = -648429536"
    cur.execute(sql, (4.8,))
    cur.execute("SELECT * FROM user")
    value = cur.fetchall()
    for val in value:
        print(val)
    cur.close()
    conn.close()

def test():
    if not os.path.exists("./MoneyCount_tables.db"):
        f = open('MoneyCount_tables.db', 'w')
        f.close()
        db.call_create_tables()
    conn = db.create_connection()
    cur = conn.cursor()
    sql = "UPDATE user SET portfolio = 20 WHERE id_user = 461718130 AND id_group = -648429536"
    cur.execute(sql)
    conn.close()



if __name__ == "__main__":
    main()
