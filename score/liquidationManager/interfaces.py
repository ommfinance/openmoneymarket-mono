from iconservice import *

class AddressDetails(TypedDict):
    name: str
    address: Address


class DataProviderInterface(InterfaceScore):
    @interface
    def getUserAccountData(self, _user: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass

    @interface
    def getSymbol(self, _reserveAddress: Address) -> str:
        pass

    @interface
    def getReserveConfigurationData(self, _reserve: Address) -> dict:
        pass


class CoreInterface(InterfaceScore):
    @interface
    def getUserUnderlyingAssetBalance(self, _reserve: Address, _user: Address) -> int:
        pass

    @interface
    def getUserBorrowBalances(self, _reserve: Address, _user: Address):
        pass

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass

    @interface
    def getUserOriginationFee(self, _reserve: Address, _user: Address) -> int:
        pass

    @interface
    def updateStateOnLiquidation(self, _principalReserve: Address, _collateralReserve: Address, _user: Address,
                                 _amountToLiquidate: int, _collateralToLiquidate: int, _feeLiquidated: int,
                                 _liquidatedCollateralForFee: int, _balanceIncrease: int):
        pass

    @interface
    def getReserveOTokenAddress(self, _reserve: Address) -> Address:
        pass

    @interface
    def transferToUser(self, _reserve: Address, _user: Address, _amount: int) -> None:
        pass

    @interface
    def liquidateFee(self, _reserve: Address, _amount: int, _destination: Address) -> None:
        pass


class OtokenInterface(InterfaceScore):
    @interface
    def burnOnLiquidation(self, _user: Address, _value: int) -> None:
        pass


class ReserveInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _amount: int) -> None:
        pass


class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> int:
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass
