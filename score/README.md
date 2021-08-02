## Open Money Market Pool primary SCOREs

1. addressProvider
   This score provides the address of all the scores required for OMM,configures addresses to all the scores required for inter-score method calls.

2. dToken
   This score maintains the burning and minting of interest bearing borrow token,represents the borrow of a particular reserve.Each reserve have a corresponding   dToken,ICX -> dICX, USDS -> dUSDS , IUSDC -> dIUSDC.

3. daoFund
   This score  collects the daily OMM token rewards. The collected funds will be managed via DAO governance.
   
4. delegation
   This score manages and handles the delegation preferences of OMM users,calculates overall delegation preference of the OMM based on the user preferences.
 
5. feeProvider
   This score collects and stores origination fees and interest difference between lending and borrowing.
   
6. governance
   This score handles the governance part of OMM,includes reserves initialization and reserves' attributes modification.
   
7. lendingPool
   This is the primary external facing score to inititate basic transactions i.e deposit,borrow,repay,redeem,liquidation,omm stake/unstake,rewards claim.This score supports fee sharing.
   
8. LendingPoolCore
   This score maintains the reserve pools,stores all the deposited tokens and maintain user level and reserve level states.
   
9. LendingPoolDataProvider
   This score provides system level metrics such as pool stats , user stats etc.It interfaces with other scores and reflects all the various data regarding the OMM system.
   

10. LiquidationManager
    This score provides the interface for liquidators to liquidate loans that are undercollateralized,handles the calculations for liquidation.

11. oToken
    This score maintains the burning and minting of interest bearing redeem tokens to represent the collatral deposited.Each reserve have a corresponding oToken; USDS -> oUSDS ,ICX -> oICX, IUSDC -> OIUSDC.
   
12. ommToken
    This score represents the OMM protocol token.OMM token is distributed  on per second basis to protocol users,dex liquidity providers and on daily basis for DAOfund and Worker token holders.
   
13. priceOracle
    This score is proxy for Band oracle,returns the price of the tokens used in OMM i.e IUSDC,USDS,ICX,Omm token.
    
14. rewardDistribution
    This score calculates the reward distibution for each entity and distibutes the rewards.It maintians the indices for the per second rewards issuance for the users and the rewards details for all the users across various interaction with Omm protocol.
   
15. stakedLp
   This score manages the staking/unstaking of Lp token for OMM pools.Lp token holders need to stake their Lp tokens to receive rewards 
   
16. workerToken
    This score is an IRC2 token which is distributed to the early contributors of the OMM protocol and the token holders receive certain portion of the daily rewards issued.
    


## How to run tests

- Assuming you're in score directory.
- copy `.env.test.sample` and create `.env.test` with appropriate value
   - `T_BEARS_URL` - t-bears url 
   - `SCORE_ADDRESS_PATH` - path to deployed score address json 
- To run docker t-bears
```shell
docker-compose up -d --build && docker logs -f omm-tbears
```
- Install dependencies for tests
```shell
pip install -r tests/config/test_requirement.txt
``` 
- To run all tests
```shell
tbears test tests
```

- To initialize P-Reps on T-Bears service
```shell
T_BEARS_URL=http://18.237.205.52:9000/ python3 -m unittest tests.config.register_preps.RegisterPReps
```


- To run individual test
```shell
python3 -m unittest tests.integration_test.test_integrate_001_basic_cases.OMMBaseTestCases.test_01_icx_cases
```


## 💡**FYI**

- If you get `is inactive SCORE` JSONRPCException, please remove score address json file and try again.
- To clear t-bears (all score), first remove score address json file and use following command
```shell
docker restart omm-tbears
```
