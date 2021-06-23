from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
	"description": "Testing rewards",
	"transaction": [
		{
			"_step": Steps.DEPOSIT_ICX,
			"user": "user1",
			"amount": 100 * EXA,
			"expectedResult": 1,
			"remarks": "User 1 deposited 100 ICX."
		},
		{
			"_step": Steps.DEPOSIT_ICX,
			"user": "user2",
			"amount": 100 * EXA,
			"expectedResult": 1,
			"remarks": "User 2 deposited 100 ICX."
		},
		{
			"_step": Steps.DEPOSIT_USDS,
			"user": "user1",
			"amount": 20 * EXA,
			"expectedResult": 1,
			"remarks": "User 1 deposited 20 USDS."
		},
		{	
			"_step": Steps.SLEEP,
			"sleep": 10 # 100 seconds
		},
		{
			"_step": Steps.CLAIM_REWARDS,
			"user": "user1",
			"amount": 10,
			"expectedResult": 1,
			"reward": 1, # should get a reward
			"remarks": "User 1 claims a part of the reward."
		},
		{
			"_step": Steps.CLAIM_REWARDS,
			"user": "user2",
			"amount": 100000 * EXA ,
			"expectedResult": 1,
			"reward": 1, # should get a reward
			"remarks": "User 2 tries to claim more reward than what they have."
		},
		{
			"_step": Steps.CLAIM_REWARDS,
			"user": "user3",
			"amount": 1 * EXA ,
			"expectedResult": 1,
			"reward": 0, # should not get any rewards
			"remarks": "User 3 has not done any transactions. The user can call the method, but will not get any reward."
		},
		{
			"_step": Steps.BORROW_USDS,
			"user": "user1",
			"amount": 10 * EXA,
			"expectedResult": 1,
			"remarks": "User 1 borrows 10 USDS"
		},
		{
			"_step": Steps.CLAIM_REWARDS,
			"user": "user1",
			"amount": 10000000 * EXA,
			"expectedResult": 1,
			"reward": 1, # should get a reward
			"remarks": "User 1 claims all their reward."
		},
	]
}