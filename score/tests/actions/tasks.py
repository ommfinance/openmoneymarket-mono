ICX = 10 ** 18
USDS = 10 ** 18
IUSDC = 10 ** 6

ACTIONS = {
	"transactions": 
		[
		{	
			"action": "deposit",
			"reserve": "usds",
			"user": "1",
			"amount": 100 * USDS,
			"expectedResult": 1
		},
		{
			"action": "borrow",
			"reserve": "usds",
			"user": "1",
			"amount": 10 * USDS,
			"expectedResult": 1
		},
		{
			"action": "borrow",
			"reserve": "usds",
			"user": "1",
			"amount": 100000000000 * USDS,
			"expectedResult": 0
		},
		{
			"action": "redeem",
			"reserve": "usds",
			"user": "1",
			"amount": 50 * USDS,
			"expectedResult": 1
		},
		{
			"action": "redeem",
			"reserve": "usds",
			"user": "1",
			"amount": 100000000000 * USDS,
			"expectedResult": 0
		},
		{
			"action": "repay",
			"reserve": "usds",
			"user": "1",
			"amount": 100 * USDS,
			"expectedResult": 1
		},
		{
			"action": "deposit",
			"reserve": "icx",
			"user": "1",
			"amount": 1 * ICX,
			"expectedResult": 1
		},{
			"action": "deposit",
			"reserve": "icx",
			"user": "1",
			"amount": 5 * ICX,
			"expectedResult": 1
		},{
			"action": "deposit",
			"reserve": "icx",
			"user": "1",
			"amount": 1234 * ICX,
			"expectedResult": 1
		},
		{
			"action": "borrow",
			"reserve": "icx",
			"user": "1",
			"amount": 10000 * ICX, # higher than collateral amount, so should fail
			"expectedResult": 0
		},
		{
			"action": "borrow",
			"reserve": "icx",
			"user": "1",
			"amount": 50 * ICX,
			"expectedResult": 1
		},
		{
			"action": "redeem",
			"reserve": "icx",
			"user": "1",
			"amount": 50 * ICX,
			"expectedResult": 1
		},
		{
			"action": "redeem",
			"reserve": "icx",
			"user": "1",
			"amount": 5000000 * ICX, # trying to redeem more than collateral
			"expectedResult": 0
		},	
		{
			"action": "repay",
			"reserve": "icx",
			"user": "1",
			"amount": 50 * ICX,
			"expectedResult": 1
		},
		{
			"action": "redeem",
			"reserve": "icx",
			"user": "1",
			"amount": -1, # since loans are pending, we can't redeem all
			"expectedResult": 0
		}
		# test left: repay more than loan, and check if extra balance is back. 
	]	
}
