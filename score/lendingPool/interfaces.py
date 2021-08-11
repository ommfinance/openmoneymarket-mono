from iconservice import *
class AddressDetails(TypedDict):
    name: str
    address: Address


# An interface to fee provider
class FeeProviderInterface(InterfaceScore):
    @interface
    def calculateOriginationFee(self, _user: Address, _amount: int) -> int:
        pass


# An interface to oToken
class OTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def mintOnDeposit(self, _user: Address, _amount: int) -> None:
        pass

    @interface
    def redeem(self, _user: Address, _amount: int) -> None:
        pass


# An interface to reserves
class ReserveInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


# An interface to reserves
class RewardInterface(InterfaceScore):
    @interface
    def claimRewards(self, _user: Address) -> int:
        pass


# An interface for sicx
class StakingInterface(InterfaceScore):
    @interface
    def stakeICX(self, _to: Address, _data: bytes = None) -> int:
        pass

    @interface
    def getTodayRate(self) -> int:
        pass


# An interface to LendingPoolCore
class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self) -> list:
        pass

    @interface
    def getUserBasicReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass

    @interface
    def updateStateOnDeposit(self, _reserve: Address, _user: Address, _amount: int) -> None:
        pass

    @interface
    def updateStateOnBorrow(self, _reserve: Address, _user: Address, _amountBorrowed: int, _borrowFee: int) -> dict:
        pass

    @interface
    def mintOnDeposit(self, _user: Address, _amount: int) -> None:
        pass

    @interface
    def isReserveBorrowingEnabled(self, _reserve: Address) -> bool:
        pass

    @interface
    def getReserveAvailableLiquidity(self, _reserve: Address) -> int:
        pass

    @interface
    def transferToUser(self, _reserve: Address, _user: Address, _amount: int, _data: bytes) -> None:
        pass

    @interface
    def getUserBorrowBalances(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def updateStateOnRepay(self, _reserve: Address, _user: Address, _paybackAmountMinusFees: int,
                           _originationFeeRepaid: int, _balanceIncrease: int, _repaidWholeLoan: bool):
        pass

    @interface
    def updateStateOnRedeem(self, _reserve: Address, _user: Address, _amountRedeemed: int) -> None:
        pass


# An interface to USDb contract
class DataProviderInterface(InterfaceScore):
    @interface
    def getUserAccountData(self, _user: Address) -> dict:
        pass

    @interface
    def calculateCollateralNeededUSD(self, _reserve: Address, _amount: int, _fee: int,
                                     _userCurrentBorrowBalanceUSD: int,
                                     _userCurrentFeesUSD: int, _userCurrentLtv: int) -> int:
        pass

    @interface
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass


# An interface to liquidation manager
class LiquidationManagerInterface(InterfaceScore):
    @interface
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int) -> dict:
        pass


# An interface to omm token
class OmmTokenInterface(InterfaceScore):
    @interface
    def unstake(self, _value: int, _user: Address) -> None:
        pass

    @interface
    def stake(self, _value: int, _user: Address) -> None:
        pass