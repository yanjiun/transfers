import uuid
import sqlite3
from enum import Enum
from datetime import datetime
from exceptions import UserNotFound, NotEnoughPoints, UserAlreadyExists

class TransferTypes(Enum):
    ADD = 1
    DEDUCT = 2

class TransferSystem:
    """
    Class that contains the apis for a point transfer system.
    Assumes that an email may only correspond to one user account

    Args:
        dbName - name of sqlite db handle

    Methods:
        createUser - creates a user with name and email
        lookupUserId - looks up user id via email
        addPoints - adds points to an account
        deductPoints - deducts points from an account
        retrieveTransferHistory - retrieves the transfer history for an account
    """
    def __init__(self, dbName):
        self.dbHandle = DbHandle(dbName)

    def createUser(self, firstName, lastName, email):
        """
        creates a new user account. Raises UserAlreadyExists exception if
        user already exists

        :param firstName: (str)
        :param lastName: (str)
        :param email: (str)
        :return userId: (str) - the user id that was created
        """
        userId = self.dbHandle.insertUserRecord(firstName, lastName, email)
        return userId

    def lookupUserId(self, email):
        """
        looks up a user's id based on their email. Raises exception UserNotFound if
        user does not exist.
        :param email: (str)
        :return userId: (str)
        """
        userId = self.dbHandle.lookupUserId(email)
        return userId

    def addPoints(self, userId, amount):
        """
        adds points to user's account based on userId. Raises exception
        UserNotFound if user does not exist
        :param userId: (str)
        :param amount: (int)
        """
        totalPoints = self.dbHandle.lookupUserPoints(userId)
        updatedPoints = totalPoints + amount
        self.dbHandle.insertTransferRecord(userId, TransferTypes.ADD, amount)
        self.dbHandle.updateUserPoints(userId, updatedPoints)
        self.dbHandle.commitTransaction()

    def deductPoints(self, userId, amount):
        """
        deducts points from user's account based on userId. Raises
        NotEnoughPoints if user has insufficient balance. Raises
        UserNotFound if user does not exist
        :param userId: (str)
        :param amount: (int)
        :return:
        """
        totalPoints = self.dbHandle.lookupUserPoints(userId)
        if (totalPoints >= amount):
            updatedPoints = totalPoints - amount
            self.dbHandle.insertTransferRecord(userId, TransferTypes.DEDUCT, amount)
            self.dbHandle.updateUserPoints(userId, updatedPoints)
            self.dbHandle.commitTransaction()
        else:
            raise NotEnoughPoints

    def retreiveTransferHistory(self, userId):
        """
        returns user's transfer history in chronological order
        raises UserNotFound exception if user does not exist
        :param userId: (str)
        :return: (list) list of transfers with have structure
                {
                    type: ADD/DEDUCT,
                    amount: (int)
                }
        """
        return self.dbHandle.lookupUserTransferHistory(userId)


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

    def insertTransferRecord(self, userId, type, amount):
        transferId = str(uuid.uuid4())
        c = self.connection.cursor()
        timestamp = datetime.now().isoformat(timespec="seconds")
        transferRecord = (transferId, type.value, userId, amount, timestamp)
        c.execute('''INSERT INTO transfers
            VALUES (?, ?, ?, ?, ?)''', transferRecord)

    def lookupUserTransferHistory(self, userId):
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