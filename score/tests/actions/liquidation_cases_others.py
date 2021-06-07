EXA = 10 ** 18

ACTIONS = [
    {
    "description": "2. Deposit 500 ICX, 500 USDb, Borrow 500 USDb, ICX price drops to $0.4, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer", # only deployer can change the price oracle value
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "icx",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "action": "deposit",
            "reserve": "usdb",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "usdb",
            "user": "new",
            "amount": 50 * EXA, # <.50.>
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer", 
            "rate": 4 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1.4 USD"
        },
        {
            "call":"liquidation",
            "action":"transfer",
            "liquidator": "deployer",
            "borrower": "new",
            "reserve": "usdb",
            "expectedResult":1
        }
    ]},
    {
    "description": "3. Deposit 1000 USDb, Borrow 500 ICX, ICX price increase to $1.4, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "usdb",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "icx",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer", 
            "rate": 14 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1.4 USD"
        },
        {
            "call":"liquidation",
            "action":"transfer",
            "liquidator": "deployer",
            "borrower": "new",
            "reserve": "icx",
            "expectedResult":1
        }
    ]},
    {
    "description": "4. Deposit 200 ICX, 800 USDb, Borrow 500 ICX, ICX price increases to $1.5, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "icx",
            "user": "new",
            "amount": 20 * EXA,
            "expectedResult": 1
        },
        {
            "action": "deposit",
            "reserve": "usdb",
            "user": "new",
            "amount": 80 * EXA, # 100 deposit
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "icx",
            "user": "new",
            "amount": 50 * EXA,
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer", 
            "rate": 15 * EXA // 10, 
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1.5 USD"
        },
        {
            "call":"liquidation",
            "action":"transfer",
            "liquidator": "deployer",
            "borrower": "new",
            "reserve": "icx",
            "expectedResult":1
        }
    ]},
    {
    "description": "5. Deposit 1000 ICX, Borrow 300 USDb, 200 ICX, ICX price drops to $0.6, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer", 
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "icx",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "usdb",
            "user": "new",
            "amount": 30 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "icx",
            "user": "new",
            "amount": 19 * EXA, # <.20.>
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 6 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.6 USD"
        },
        {
            "call":"liquidation",
            "action":"transfer",
            "liquidator": "deployer",
            "borrower": "new",
            "reserve": "usdb",
            "expectedResult":1
        },
    ]},
    {
    "description": "6. Deposit 1000 USDb, Borrow 300 USDb, 200 ICX, ICX price increase to $2, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "usdb",
            "user": "new",
            "amount": 100 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "usdb",
            "user": "new",
            "amount": 30 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "icx",
            "user": "new",
            "amount": 19 * EXA, # <.20.>
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 2 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        },
        {
            "call":"liquidation",
            "action":"transfer",
            "liquidator": "deployer",
            "borrower": "new",
            "reserve": "icx",
            "expectedResult":1
        }
    ]},
    {
    "description": "7. Deposit 800 USDb, 200 ICX, Borrow 100 USDb, 400 ICX, ICX price increase to $1.7, liquidation happens",
    "user":"new",
    "transaction": [
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 1 * EXA,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 1 USD"
        },
        {
            "action": "deposit",
            "reserve": "usdb",
            "user": "new",
            "amount": 80 * EXA,
            "expectedResult": 1
        },
        {
            "action": "deposit",
            "reserve": "icx",
            "user": "new",
            "amount": 20 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "usdb",
            "user": "new",
            "amount": 10 * EXA,
            "expectedResult": 1
        },
        {
            "action": "borrow",
            "reserve": "icx",
            "user": "new",
            "amount": 39 * EXA, #<.39.>
            "expectedResult": 1
        },
        {
            "action": "set_reference_data",
            "contract": "priceOracle",
            "user": "deployer",
            "rate": 17 * EXA // 10,
            "expectedResult": 1,
            "remarks": "Set price for ICX equal to 0.7 USD"
        }, 
        {
            "call":"liquidation",
            "action":"transfer",
            "liquidator": "deployer",
            "borrower": "new",
            "reserve": "icx",
            "expectedResult":1
        }
    ]}
]
