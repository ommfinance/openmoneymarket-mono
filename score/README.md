##Open Money Market Pool primary SCOREs

1. LendingPool

   This is the primary external facing score to initiate actions such as deposit, withdraw, repay , borrow etc.
2. LendingPoolCore

   This score maintains the reserve pools.
3. LendingPoolConfigurator

   Provides configuration functions for LendingPool and LendingPoolCore
4. LendingPoolDataProvider

   Provides system level metrics such as pool stats , user stats etc.
5. AddressProvider

   Provides the various score addresses such as oTokens, collatrals etc.
6. FeeProvider

   Collects and stores origination fees and rates.
7. DaoFund

   Collects the interest difference between lending and borrowing. Fund will be managed via DAO governance.
8. LiquidationManager

   Provides the interface for liquidators liquidate loans that are undercollateralized.
9. oToken

   Interest bearing redeem tokens to represent the collatral deposited. oUSDb to represent USDb deposited. oICX to represent ICX.



## How to run tests

- Assuming you're in score directory.
- copy `.env.test.sample` and create `.env.test` with appropriate value
   - `T_BEARS_URL` - t-bears url 
   - `SCORE_ADDRESS_PATH` - path to deployed score address json 
- To run docker t-bears
```shell
docker-compose up -d --build
```
- Install dependencies for tests
```shell
pip install -r tests/config/test_requirement.txt
``` 
- To run all tests
```shell
tbears test tests
```

- To run individual test
```shell
python3 -m unittest tests.integration_test.test_integrate_icx_cases.ICXTest
```