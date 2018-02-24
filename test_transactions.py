import unittest
import sqlite3
from transactions import TransactionSystem, TransactionTypes
from initializeDb import createDb
from exceptions import UserNotFound, NotEnoughPoints, UserAlreadyExists

class TestTransactionSystem(unittest.TestCase):

    def setUp(self):
        createDb("mock.db")
        self.transactionSystem = TransactionSystem("mock.db")
        self.connection = sqlite3.connect("mock.db")
        self.connection.row_factory = sqlite3.Row

    def tearDown(self):
        self.transactionSystem = None
        c = self.connection.cursor()
        c.execute('''DROP TABLE transfers''')
        c.execute('''DROP TABLE users''')
        self.connection.commit()

    def test_createUser(self):
        userId = self.transactionSystem.createUser("YJ", "Chen", "chen.yanjiun@gmail.com")
        c = self.connection.cursor()
        c.execute('''SELECT * FROM users WHERE userId=?''', (userId, ))
        row = c.fetchone()
        self.assertEqual(row["firstName"], "YJ")
        self.assertEqual(row["lastName"], "Chen")
        self.assertEqual(row["email"], "chen.yanjiun@gmail.com")
        self.assertEqual(row["totalPoints"], 0)

    def test_createUserAlreadyExists(self):
        self.transactionSystem.createUser("YJ", "Chen", "chen.yanjiun@gmail.com")
        with self.assertRaises(UserAlreadyExists):
            self.transactionSystem.createUser("YJ", "Chen", "chen.yanjiun@gmail.com")

    def test_lookupValidUser(self):
        userId = self.transactionSystem.createUser("YJ", "Chen", "abc@123.com")
        self.assertEqual(self.transactionSystem.lookupUserId("abc@123.com"), userId);

    def test_lookupInvalidUser(self):
        with self.assertRaises(UserNotFound):
            self.assertEqual(self.transactionSystem.lookupUserId("random@blah.foo"))

    def test_addPoints(self):
        userId = self.transactionSystem.createUser("YJ", "Chen", "yj@yay.org")
        pointsToAdd = 10

        self.transactionSystem.addPoints(userId, pointsToAdd);

        c = self.connection.cursor()
        c.execute('''SELECT totalPoints FROM users WHERE userId=?''', (userId, ))
        row = c.fetchone()
        self.assertEqual(row["totalPoints"], pointsToAdd)
        c.execute('''SELECT amount, type FROM transfers WHERE userId=?''', (userId, ))
        rows = c.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amount"], pointsToAdd)
        self.assertEqual(rows[0]["type"], TransactionTypes.ADD.value)

    def test_addPointsInvalidUser(self):
        invalidId = "abcc"
        pointsToAdd = 10
        with self.assertRaises(UserNotFound):
            self.transactionSystem.addPoints(invalidId, pointsToAdd)

    def test_deductPoints(self):
        userId = self.transactionSystem.createUser("YJ", "Chen", "yj@yay.org")
        self.transactionSystem.addPoints(userId, 10);
        self.transactionSystem.deductPoints(userId, 3);

        c = self.connection.cursor()
        c.execute('''SELECT totalPoints FROM users WHERE userId=?''', (userId, ))
        row = c.fetchone()
        self.assertEqual(row["totalPoints"], 7)
        c.execute('''SELECT amount, type FROM transfers WHERE userId=?''', (userId, ))
        rows = c.fetchall()
        self.assertEqual(len(rows), 2)
        for r in rows:
            if r["type"] == TransactionTypes.ADD.value:
                self.assertEqual(r["amount"], 10)
            elif r["type"] == TransactionTypes.DEDUCT.value:
                self.assertEqual(r["amount"], 3)
            else:
                self.assertFalse(1==1, "invalid transfer type found")

    def test_deductPointsInvalidUser(self):
        invalidId = "abcc"
        with self.assertRaises(UserNotFound):
            self.transactionSystem.addPoints(invalidId, 33)

    def test_deductPointsInsufficientPoints(self):
        userId = self.transactionSystem.createUser("YJ", "Chen", "yj@yay.org")
        self.transactionSystem.addPoints(userId, 2);
        with self.assertRaises(NotEnoughPoints):
            self.transactionSystem.deductPoints(userId, 3);

    def test_retrieveHistory(self):
        userId = self.transactionSystem.createUser("YJ", "Chen", "yj@yay.org")
        self.transactionSystem.addPoints(userId, 10);
        self.transactionSystem.deductPoints(userId, 3);
        self.transactionSystem.deductPoints(userId, 2);

        history = self.transactionSystem.retreiveTransactionHistory(userId)

        expectedHistory = [
            {"amount": 10.0, "type": 1},
            {"amount": 3.0, "type": 2},
            {"amount": 2.0, "type": 2}
        ]
        self.assertEquals(history, expectedHistory)

    def test_retrieveEmptyHistory(self):
        userId = self.transactionSystem.createUser("YJ", "Chen", "yj@yay.org")

        history = self.transactionSystem.retreiveTransactionHistory(userId)
        self.assertEqual(history, [])

if __name__ == "__main__":
    unittest.main(verbosity=2)