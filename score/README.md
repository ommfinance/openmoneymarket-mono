Open Money Market Pool primary SCOREs

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
