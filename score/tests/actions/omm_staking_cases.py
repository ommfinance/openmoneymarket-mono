from .steps import Steps
EXA = 10 ** 18

ACTIONS = {
	"description": "OMM staking tests.",
	"transaction": [
		{
			"_step": Steps.STAKE_OMM,
			"user": "user1",
			"amount": 100 * EXA,
			"expectedResult": 1,
			"feeShared": 0
		},
		{
			"_step": Steps.TRANSFER_OMM,
			"user": "user1",
			"amount": 990 * EXA,
			"expectedResult": 0,
			"remarks": "User had 1000 OMM and staked 100. User should not be able to transfer 990 OMM tokens."
		},
		{	
			"_step": Steps.UNSTAKE_OMM,
			"user": "user1",
			"amount": 110 * EXA,
			"expectedResult": 0,
			"feeShared": 0
		},
		{	
			"_step": Steps.UNSTAKE_OMM,
			"user": "user1",
			"amount": 10 * EXA,
			"expectedResult": 1,
			"feeShared": 0
		},
		{		
            "_step": Steps.DEPOSIT_USDS,
            "user": "user1",
            "amount": 10 * EXA,
            "expectedResult": 1,
            "feeShared": 0
        },        
		{
        	"_step": Steps.STAKE_OMM,
        	"user": "user1",
        	"amount": 120 * EXA,
        	"expectedResult": 1,
        	"feeShared": 1,
        	"addedStake": 30 * EXA
        },
        {
        	"_step": Steps.UNSTAKE_OMM,
        	"user": "user1",
        	"amount": 15 * EXA,
        	"expectedResult": 1,
        	"feeShared": 1
        }
	]
}