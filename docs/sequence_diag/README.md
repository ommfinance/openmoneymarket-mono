
# Sequence Diagrams
The above sequence diagrams depicts the various SCOREs involved and the inter-SCORE calls for deposit, borrow, redeem, repay and liquidation process.

## ICX and USDb Deposit
Sequence diagram for ICX deposit is slightly different than that of USDb as we have introduced staking pool in the system and all the ICX that gets deposited in the system is staked by the staking pool to earn staking rewards.

## ICX Withdraw
For ICX withdraw, users can choose any of the two paths. As all the ICX in the system will be staked, users can withdraw their deposited amount plus the interest accumulated in ICX after waiting for the unstaking period or if they want immediate access to their asset, they will be provided with sICX ( token representation for staked ICX ) which can be converted to ICX using DEX.



