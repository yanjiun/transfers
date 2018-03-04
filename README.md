# Transfer Platform
A module prototype for tracking user loyalty points

## Dependencies
assumes Python 3.6 or greater

## Usage
1. choose a db name such as "transfers.db"
2. Initialize DB with script
    python initializeDb.py <dbName>
3. use the API:
```Python
        from transfers import TransferSystem
        ts = TransferSystem("transfers.db") 
        ts.createUser("Bart", "Simpson", "bs@foo.bar")
```
## API

methods include:
- createUser
- lookupUserId
- addPoints
- deductPoints
- retrieveTransferHistory

see docstrings for more details

## To test

run
```
    python test_transfers.py
```

## Assumptions
- a unique email is required for each account

## Further Considerations
- sqlite was used as the database, but if delivering to production we may want to migrate to postgresql
