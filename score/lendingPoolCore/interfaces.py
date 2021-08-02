from iconservice import *


class AddressDetails(TypedDict):
    name: str
    address: Address


class ReserveAttributes(TypedDict):
    reserveAddress: Address
    oTokenAddress: Address
    dTokenAddress: Address
    lastUpdateTimestamp: int
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex: int
    baseLTVasCollateral: int
    liquidationThreshold: int
    liquidationBonus: int
    decimals: int
    borrowingEnabled: bool
    usageAsCollateralEnabled: bool
    isFreezed: bool
    isActive: bool


class UserDataAttributes(TypedDict):
    lastUpdateTimestamp: int
    originationFee: int
    useAsCollateral: bool


class Constant(TypedDict):
    reserve: Address
    optimalUtilizationRate: int
    baseBorrowRate: int
    slopeRate1: int
    slopeRate2: int


class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


# An interface to oToken
class OTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def principalBalanceOf(self, _user: Address) -> int:
        pass

    @interface
    def getUserLiquidityCumulativeIndex(self, _user: Address) -> int:
        pass


# An interface to debt token
class DTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def principalBalanceOf(self, _user: Address) -> int:
        pass

    @interface
    def mintOnBorrow(self, _user: Address, _amount: int, _balanceIncrease: int):
        pass

    @interface
    def getUserBorrowCumulativeIndex(self, _user: Address) -> int:
        pass

    @interface
    def principalTotalSupply(self) -> int:
        pass

    @interface
    def burnOnRepay(self, _user: Address, _amount: int, _balanceIncrease: int):
        pass

    @interface
    def burnOnLiquidation(self, _user: Address, _amount: int, _balanceIncrease: int) -> None:
        pass


# An interface to Reserve
class ReserveInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass

    @interface
    def delegate(self, _delegations: List[PrepDelegations]):
        pass
