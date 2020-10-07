**Omm SCORE APIs Documentation**

1.**Readonly methods**

  a. Get all addresses ( USDb, sICX, oICX , oUSDb, LendingPool, LendingPoolDataProvider)

_{ &quot;to&quot; : AddressProvider ,_

&quot;_method&quot;: &quot;getAllAddresses&quot;,_

_}_

Example response:

_{_

_&quot;collateral&quot; :{_

_&quot;USDb&quot; :&quot;0xc...&quot;,_

_&quot;sICX &quot;:&quot;0xc..&quot;_

_} ,_

_&quot;oTokens&quot; : {_

_&quot;oICX&quot;:&quot;&quot;,_

_&quot;oUSDb&quot;:&quot;&quot;_

_},_

_&quot;systemContract&quot;: {_

_&quot;LendingPool&quot;:&quot;&quot;,_

_&quot;LendingPoolCore&quot;:&quot;&quot;_

_}_

_}_

  b. Get reserve data for a specific reserve

_{ &quot;to&quot; : LendingPoolDataProvider_

&quot;_method&quot;: &quot;getReserveData&quot;,_

&quot;_params&quot;: {&quot;\_reserve&quot;: Address using 1 a for USDb and sICX }_

_}_

Example response:

_{&quot;totalLiquidity&quot;: 100000 ,_

_&quot;availableLiquidity&quot;:1000,_

&quot;_liquidityRate&quot;: 3.4,_

&quot;_borrowRate&quot;: 5.6,_

&quot;_utilizationRate&quot;: 65.5,_

&quot;_liquidityRate&quot;: 0.5,_

&quot;_oTokenAddress&quot;: &quot;cx8u88…&quot;,_

&quot;_lastUpdateTimestamp&quot; : 23454543 }_

  c. Get user reserve data for a specific reserve

_{ &quot;to&quot; : LendingPoolDataProvider,_

&quot;_method&quot;: &quot;getUserReserveData&quot;,_

&quot;_params&quot;: {&quot;\_reserve&quot;: Address using 1 a for USDb and sICX ,_

&quot;_\_user&quot;: &quot;hx09dd……&quot;}_

_}_

Example response:

_{&quot;currentOTokenBalance&quot;: 100000 ,_

_&quot;currentBorrowBalance&quot;:1000,_

&quot;_principalBorrowBalance&quot;: 900,_

&quot;_liquidityRate&quot;: 3.4,_

&quot;_borrowRate&quot;: 5.6,_

&quot;_originationFee&quot;: 0.0001,_

&quot;_variableBorrowIndex&quot;: 0.1_

&quot;_lastUpdateTimestamp&quot; : 23454543,_

&quot;_usageAsCollateralEnabled&quot;: True }_

  d. Get user account data

_{ &quot;to&quot; : LendingPoolDataProvider,_

&quot;_method&quot;: &quot;getUserAccountData&quot;,_

&quot;_params&quot;: {&quot;\_user&quot;: &quot;hx09dd……&quot;}_

_}_

Example response:

_{&quot;totalLiquidityICX&quot;: 100000 ,_

_&quot;totalCollateralICX&quot;:1000,_

&quot;_totalBorrowsICX&quot;: 100,_

&quot;_totalFeesICX&quot;: 5.6,_

&quot;_availableBorrowsICX&quot;:100,_

&quot;_currentLiquidationThreshold&quot;: 0.65,_

&quot;_ltv&quot; :0.75,_

&quot;_healthFactor&quot;: 1.2 }_

  e. Get reserve configuration data

_{ &quot;to&quot; : LendingPoolDataProvider,_

&quot;_method&quot;: &quot;getReserveConfigurationData&quot;,_

&quot;_params&quot;: {&quot;reserve&quot;: &quot;Address using 1 a for USDb and sICX &quot;}_

_}_

Example response:

_{&quot;ltv&quot;: 0.6_

_&quot;liquidationThreshold&quot;:0.65,_

&quot;_liquidationBonus&quot;: 0.1,_

&quot;_usageAsCollateralEnabled&quot;: True,_

&quot;_borrowingEnabled&quot;:True,_

&quot;_isActive&quot;: True,_

_}_

2.**External methods**

  a. [Deposit ICX](https://app.lucidchart.com/invitations/accept/e2de6c8f-91c4-4ddd-a07a-8186a89cd664)

_{ &quot;to&quot; : from response in 1 a for LendingPool,_

&quot;_method&quot;: &quot;deposit&quot;,_

&quot;_params&quot;: { &quot;\_amount&quot;: 10 \*\* 18 },_

&quot;_value&quot;: 10 \*\* 18_

_}_

  1. [Deposit USDb](https://app.lucidchart.com/invitations/accept/65cdc890-fb7e-4ddc-8d33-75259c2a17d8)

_{ &quot;to&quot; : from response in 1 a for USDb,_

&quot;_method&quot;: &quot;transfer&quot;,_

&quot;_params&quot;: {&quot;\_to&quot;: from response in 1 a for LendingPool,_

&quot;_\_value&quot;: 10 \*\* 18,_

&quot;_\_data&quot;: bytes(&#39;{ &quot;method&quot;: &quot;deposit&quot;, &quot;params&quot;: {&quot;\_amount&quot;: 10 \*\* 18}}&#39;) })_

_}_

_}_

  b. [Redeem USDb](https://app.lucidchart.com/invitations/accept/0bd317b0-4214-433a-9817-97955def300b)

{ _&quot;to&quot; : from response in 1 a for oUSDb,_

_&quot;method&quot;: &quot;redeem&quot;,_

_&quot;params&quot; : {&quot;\_amount&quot; : 10 \*\* 18}_

}

  c. [Redeem ICX](https://app.lucidchart.com/invitations/accept/1f2b8e6a-b3b8-4be7-ac91-037f0d6b1e9e)(

{ _&quot;to&quot; : from response in 1 a for oICX,_

_&quot;method&quot;: &quot;redeem&quot;,_

_&quot;params&quot; : {&quot;\_amount&quot; : 10 \*\* 18,_

&quot;_\_waitForUnstaking&quot;: True}_

}

_\*\*Note: If \_waitForUnstaking is set to true, it waits for an unstaking period to transfer ICX amount back to the user wallet else if set to false then it transfers the equivalent amount of sICX to the user wallet instantly. \*\*_

  d. [Borrow](https://app.lucidchart.com/invitations/accept/5916d025-5030-4d44-8860-c7548759acaa) (

{ _&quot;to&quot; : from response in 1 a for LendingPool,_

_&quot;method&quot;: &quot;borrow&quot;,_

_&quot;params&quot; : {&quot;\_amount&quot; : 10 \*\* 18,_

&quot;_\_reserveAddress&quot;: from response in 1 a for USDb or sICX}_

}

  e. [Repay](https://app.lucidchart.com/invitations/accept/82ec9b41-e0db-463e-a933-1040c4cf8177) (

{ _&quot;to&quot; : from response in 1 a for USDb or sICX,_

&quot;_method&quot;: &quot;transfer&quot;,_

&quot;_params&quot;: {&quot;\_to&quot;: from response in 1 a for LendingPool,_

&quot;_\_value&quot;: 10 \*\* 18,_

&quot;_\_data&quot;: bytes(&#39;{ &quot;method&quot;: &quot;repay&quot;, &quot;params&quot;: {&quot;\_reserveAddress&quot;:from response in 1 a for USDb or sICX, \_amount&quot;: 10 \*\* 18}}&#39;) }_

_}_

  f. [Liquidation](https://app.lucidchart.com/invitations/accept/746bb070-ab05-4966-aad4-0ca369ecde19) (

{ _&quot;to&quot; : from response in 1 a for USDb or sICX,_

&quot;_method&quot;: &quot;transfer&quot;,_

&quot;_params&quot;: {&quot;\_to&quot;: from response in 1 a for LendingPool,_

&quot;_\_value&quot;: 10 \*\* 18,_

&quot;_\_data&quot;: bytes(&#39;{ &quot;method&quot;: &quot;liquidationCall&quot;,_

_&quot;params&quot;: {&quot;\_collateral&quot;:from response in 1 a for USDb or sICX,_

&quot;_\_reserve&quot;: from response in 1 a for sICX or USDb,_

&quot;_\_user&quot;:&quot;hx4555...&quot;,_

&quot;_\_purchaseAmount&quot;: 10 \*\* 18}}&#39;) }_

_}_
