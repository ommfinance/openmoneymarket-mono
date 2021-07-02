from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
	"description": "",
	"transaction": [
	{
		"_step": Steps.DEPOSIT_ICX,
		"user": "user1",
		"amount": 1 * EXA,
		"expectedResult": 1,
		"remarks": "User 1 deposited 1000 ICX."
	},
	{
		"_step": Steps.DEPOSIT_ICX,
		"user": "user2",
		"amount": 1 * EXA,
		"expectedResult": 1,
		"remarks": "User 2 deposited 1000 ICX."
	}
	]
}