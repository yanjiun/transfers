import sqlite3
import sys

def createDb(name):
    conn = sqlite3.connect(name)
    c = conn.cursor()

    c.execute('''CREATE TABLE users
        (userId text PRIMARY KEY, 
        email text, 
        firstName text, 
        lastName text, 
        totalPoints real, 
        lastUpdateDatetime text)''')


    c.execute('''CREATE TABLE transfers
        (transferId text PRIMARY KEY, 
        type integer, 
        userId text, 
        amount real, 
        lastUpdateDatetime text,
        FOREIGN KEY(userId) REFERENCES users(userId))''')

    conn.commit()

    conn.close()

if __name__ == "__main__":
    createDb(sys.argv[1])
