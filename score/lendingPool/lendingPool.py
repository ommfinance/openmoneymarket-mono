from iconservice import *

TAG = 'LendingPool'


# An interface to oToken
class OTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def mintOnDeposit(self, _user: Address, _amount: int) -> None:
        pass


# An interface to USDb contract
class USDbInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
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
    def getReserveData(self, _reserveAddress: Address) -> dict:
        pass

    @interface
    def updateStateOnDeposit(self, _reserve: Address, _user: Address, _amount: int, _isFirstDeposit: bool) -> None:
        pass

    @interface
    def updateStateOnBorrow(self, _reserve: Address, _user: Address, _amountBorrowed: int, _borrowFee: int):
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
    def transferToUser(self, _reserve: Address, _user: Address, _amount: int) -> None:
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


# An interface to fee provider
class FeeProviderInterface(InterfaceScore):
    @interface
    def calculateOriginationFee(self, _user: Address, _amount: int) -> int:
        pass

    @interface
    def getReserveAvailableLiquidity(self, _reserve: Address) -> int:
        pass

class LendingPool(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCore', db, value_type=Address)
        self._dataProviderAddress = VarDB('lendingPoolDataProvider', db, value_type=Address)
        self._feeProviderAddress = VarDB('feeProvider', db, value_type=Address)
        self._USDbAddress = VarDB('USDbAddress', db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def Borrow(self, _reserve: Address, _user: Address, _amount: int, _borrowRate: int, _borrowFee: int,
               _borrowBalanceIncrease: int, _timestamp: int):
        pass
    
    @eventlog(indexed = 3)
    def RedeemUnderlying(self, _reserve: Address, _user: Address, _amount: int, _timestamp: int):
        pass

    @external
    def setLendingPoolCoreAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._lendingPoolCoreAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolCoreAddress(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @external
    def setUSDbAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._USDbAddress.set(_address)

    @external(readonly=True)
    def getUSDbAddress(self) -> Address:
        return self._USDbAddress.get()

    @external
    def setDataProvider(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._dataProviderAddress.set(_address)

    @external(readonly=True)
    def getDataProvider(self) -> Address:
        return self._dataProviderAddress.get()

    @external
    def setFeeProvider(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._feeProviderAddress.set(_address)

    @external(readonly=True)
    def getFeeProvider(self) -> Address:
        return self._feeProviderAddress.get()

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
        isFirstDeposit = False
        if oToken.balanceOf(self.tx.origin) == 0:
            isFirstDeposit = True

        core.updateStateOnDeposit(_reserve, self.tx.origin, _amount, isFirstDeposit)

        oToken.mintOnDeposit(self.tx.origin, _amount)

        USDb.transfer(self._lendingPoolCoreAddress.get(), _amount)

    @external
    def redeemUnderlying(self, _reserve: Address, _user: Address, _amount: int, _oTokenbalanceAfterRedeem: int):
        """
        redeems the underlying amount of assets requested by the _user.This method is called from the oToken contract
        :param _reserve:the address of the reserve
        :param _user:the address of the user requesting the redeem
        :param _amount:the amount to be deposited, should be -1 if the user wants to redeem everything
        :param _balanceAfterRedeem:the remaining balance of _user after the redeem is successful
        :return:
        """
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        if core.getReserveAvailableLiquidity(_reserve) < _amount:
            revert(f'There is not enough liquidity available to redeem')


        core.updateStateOnDeposit(_reserve, _user, _amount, _oTokenbalanceAfterRedeem == 0)
        core.transferToUser(_reserve, _user, _amount)

        self.RedeemUnderlying(_reserve, _user, _amount, self.block.timestamp)




        
        

    def _require(self, _condition: bool, _message: str):
        if not _condition:
            revert(_message)

    @external
    def borrow(self, _reserve: Address, _amount: int):
        """
        allows users to borrow _amount of _reserve asset as a loan ,provided that the borrower has already deposited enough amount of collateral
        :param _reserve:the address of the reserve
        :param _amount:the amount to be borrowed
        :return:
        """
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        dataProvider = self.create_interface_score(self._dataProviderAddress.get(), DataProviderInterface)
        feeProvider = self.create_interface_score(self._feeProviderAddress.get(), FeeProviderInterface)
        self._require(core.isReserveBorrowingEnabled(_reserve), "Borrow error:borrowing not enabled in  the reserve")
        availableLiquidity = core.getReserveAvailableLiquidity(_reserve)
        self._require(availableLiquidity >= _amount, "Borrow error:Not enough available liquidity in the reserve")
        userData = dataProvider.getUserAccountData(self.msg.sender)
        userCollateralBalanceUSD = userData['totalCollateralBalanceUSD']
        userBorrowBalanceUSD = userData['totalBorrowBalanceUSD']
        userTotalFeesUSD = userData['totalFeesUSD']
        currentLTV = userData['currentLtv']
        currentLiquidationThreshold = userData['currentLiquidationThreshold']
        healthFactorBelowThreshold = userData['healthFactorBelowThreshold']
        self._require(userCollateralBalanceUSD > 0, "Borrow error:The user dont have any collateral")
        self._require(not healthFactorBelowThreshold, "Borrow error:Health factor is below threshold")
        borrowFee = feeProvider.calculateOriginationFee(self.msg.sender, _amount)
        
        self._require(borrowFee > 0, "Borrow error:borrow amount is very small")
        amountOfCollateralNeededUSD = dataProvider.calculateCollateralNeededUSD(_reserve, _amount, borrowFee,
                                                                                userBorrowBalanceUSD,
                                                                               userTotalFeesUSD, currentLTV)

        # revert("Reached here")
        self._require(amountOfCollateralNeededUSD <= userCollateralBalanceUSD,
                      "Borrow error:Insufficient collateral to cover new borrow")
        borrowData = core.updateStateOnBorrow(_reserve, self.msg.sender, _amount, borrowFee)
        core.transferToUser(_reserve, self.msg.sender, _amount)
        # self.Borrow(_reserve, self.msg.sender, _amount, borrowData['currentBorrowRate'], borrowFee,borrowData['balanceIncrease'], self.block.timestamp)

    @payable
    @external
    def repay(self, _reserve: Address, _amount: int):
        """
        repays a borrow on the specific reserve, for the specified amount (or for the whole amount, if -1 is send as params for _amount).
        :param _reserve:the address of the reserve
        :param _amount:the amount to repay,should be -1 if the user wants to repay everything
        :return:
        """
        pass

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
        pass

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
