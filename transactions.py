import uuid
import sqlite3
from enum import Enum
from datetime import datetime
from exceptions import UserNotFound, NotEnoughPoints, UserAlreadyExists

class TransactionTypes(Enum):
    ADD = 1
    DEDUCT = 2

class TransactionSystem:
    def __init__(self, dbName):
        self.dbHandle = DbHandle(dbName)

    def createUser(self, firstName, lastName, email):
        userId = self.dbHandle.insertUserRecord(firstName, lastName, email)
        return userId

    def lookupUserId(self, email):
        userId = self.dbHandle.lookupUserId(email)
        return userId

    def addPoints(self, userId, amount):
        totalPoints = self.dbHandle.lookupUserPoints(userId)
        updatedPoints = totalPoints + amount
        self.dbHandle.insertTransactionRecord(userId, TransactionTypes.ADD, amount)
        self.dbHandle.updateUserPoints(userId, updatedPoints)
        self.dbHandle.commitTransaction()

    def deductPoints(self, userId, amount):
        totalPoints = self.dbHandle.lookupUserPoints(userId)
        if (totalPoints >= amount):
            updatedPoints = totalPoints - amount
            self.dbHandle.insertTransactionRecord(userId, TransactionTypes.DEDUCT, amount)
            self.dbHandle.updateUserPoints(userId, updatedPoints)
            self.dbHandle.commitTransaction()
        else:
            raise NotEnoughPoints

    def retreiveTransactionHistory(self, userId):
        return self.dbHandle.lookupUserTransactionHistory(userId)


class DbHandle():
    def __init__(self, name):
        self.dbName = name
        self.connection = sqlite3.connect(name)
        self.connection.row_factory = sqlite3.Row

    def lookupUserId(self, email):
        c = self.connection.cursor()
        c.execute('''SELECT userId from users 
            WHERE email=?''', (email, ))
        row = c.fetchone()
        if row is None:
            raise UserNotFound
        return row["userId"]

    def lookupUserPoints(self, userId):
        # throw Exception if user cannot be found
        c = self.connection.cursor()
        c.execute(''' SELECT totalPoints from users
            WHERE userId=?''', (userId, ))
        row = c.fetchone()
        if row is None:
            raise UserNotFound
        return row["totalPoints"]

    def insertUserRecord(self, firstName, lastName, email):
        #TODO: assuming valid email. could probably validate email
        userId = str(uuid.uuid5(uuid.NAMESPACE_URL, email))
        c = self.connection.cursor()
        timestamp = datetime.now().isoformat(timespec="seconds")
        userRecord = (userId, email, firstName, lastName, 0.0, timestamp)
        try:
            c.execute('''INSERT INTO users
                VALUES (?, ?, ?, ?, ?, ?)''', userRecord)
            self.commitTransaction()
        except sqlite3.IntegrityError:
            raise UserAlreadyExists
        return userId

    def updateUserPoints(self, userId, totalPoints):
        c = self.connection.cursor()
        c.execute('''UPDATE users SET totalPoints=?
            WHERE userId=?''', (totalPoints, userId))

    def insertTransactionRecord(self, userId, type, amount):
        transactionId = str(uuid.uuid4())
        c = self.connection.cursor()
        timestamp = datetime.now().isoformat(timespec="seconds")
        transactionRecord = (transactionId, type.value, userId, amount, timestamp)
        c.execute('''INSERT INTO transfers
            VALUES (?, ?, ?, ?, ?)''', transactionRecord)

    def lookupUserTransactionHistory(self, userId):
        c = self.connection.cursor()
        c.execute('''SELECT amount, type from transfers
            WHERE userId=? ORDER BY lastUpdateDatetime''', (userId, ))
        rows = c.fetchall()
        transferHistory = []
        for r in rows:
            transfer = {
                "amount": r["amount"],
                "type": r["type"]
            }
            transferHistory.append(transfer)
        return transferHistory

    def __closeDb__(self):
        self.connection.close()

    def commitTransaction(self):
        self.connection.commit()