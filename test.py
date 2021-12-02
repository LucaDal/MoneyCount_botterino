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


def test():
    if(not os.path.exists("./MoneyCount_tables.db")):
        f = open('MoneyCount_tables.db', 'w')
        f.close()
        db.call_create_tables()
    conn = db.create_connection()
    cur = conn.cursor()
    # id_group = 461718130
    cur.execute("SELECT * FROM user ")
    value = cur.fetchall()
    for val in value:
        print(val)


if __name__ == "__main__":
    main()
