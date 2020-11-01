from iconservice import *

TAG = 'LendingPool'

# An interface to oToken
class OTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

# An interface to USDb contract
class USDbInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes=None):
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


class LendingPool(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCore', db, value_type = Address)
        self._USDbAddress = VarDB('USDbAddress', db, value_type = Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def setLendingPoolCoreAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._lendingPoolCoreAddress.set(_address)


    @external(readonly = True)
    def getLendingPoolCoreAddress(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @external
    def setUSDbAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._USDbAddress.set(_address)

    @external(readonly = True)
    def getUSDbAddress(self) -> Address:
        return self._USDbAddress.get()
    
    @payable
    @external
    def deposit(self, _reserve: Address, _amount: int):
        """
        deposits the underlying asset to the reserve
        :param _reserve:the address of the reserve
        :param _amount:the amount to be deposited
        :return:
        """
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        USDb = self.create_interface_score(self._USDbAddress.get(), USDbInterface)
        reserveData = core.getReserveData(_reserve)
        oTokenAddress = reserveData['oTokenAddress']
        oToken = self.create_interface_score(oTokenAddress, OTokenInterface)

        if oToken.balanceOf(self.tx.origin) == 0:
            isFirstDeposit = True
        
        core.updateStateOnDeposit(_reserve, self.tx.origin, _amount, isFirstDeposit)

        oToken.mintOnDeposit(self.tx.origin, _amount)

        USDb.transfer( self._lendingPoolCoreAddress.get(), _amount)

    @external
    def redeemUnderlying(self, _reserve: Address, _user: Address, _amount: int, _balanceAfterRedeem: int):
        """
        redeems the underlying amount of assets requested by the _user.This method is called from the oToken contract
        :param _reserve:the address of the reserve
        :param _user:the address of the user requesting the redeem
        :param _amount:the amount to be deposited, should be -1 if the user wants to redeem everything
        :param _balanceAfterRedeem:the remaining balance of _user after the redeem is successful
        :return:
        """

    @external
    def borrow(self, _reserve: Address, _amount: int):
        """
        allows users to borrow _amount of _reserve asset as a loan ,provided that the borrower has already deposited enough amount of collateral
        :param _reserve:the address of the reserve
        :param _amount:the amount to be borrowed
        :return:
        """

    @payable
    @external
    def repay(self, _reserve: Address, _amount: int):
        """
        repays a borrow on the specific reserve, for the specified amount (or for the whole amount, if -1 is send as params for _amount).
        :param _reserve:the address of the reserve
        :param _amount:the amount to repay,should be -1 if the user wants to repay everything
        :return:
        """

    @payable
    @external
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int):
        """
        liquidates an undercollateralized loan
        :param _collateral:the address of the collateral to be liquidated
        :param _reserve:the address of the reserve
        :param _user:the address of the borrower
        :param _purchaseAmount:the amount to liquidate
        :return:
        """

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:

        try:
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            revert(f'Invalid data: {_data}. Exception: {e}')

        if set(d.keys()) != set(["method", "params"]):
            revert('Invalid parameters.')
        if d["method"] == "deposit":
            self.deposit(self.msg.sender, d["params"].get("amount", -1))
        else:
            revert(f'No valid method called, data: {_data}')