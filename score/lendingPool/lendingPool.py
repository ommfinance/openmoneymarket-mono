from iconservice import *

TAG = 'LendingPool'
BATCH_SIZE = 100


# An interface to oToken
class OTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def mintOnDeposit(self, _user: Address, _amount: int) -> None:
        pass


# An interface to reserves
class ReserveInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


# An interface for sicx
class StakingInterface(InterfaceScore):
    @interface
    def addCollateral(self, _to: Address, _data: bytes = None) -> None:
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
    def transferToUser(self, _reserve: Address, _user: Address, _amount: int, _data: bytes) -> None:
        pass

    @interface
    def getUserBorrowBalances(self, _reserve: Address, _user: Address):
        pass

    @interface
    def updateStateOnRepay(self, _reserve: Address, _user: Address, _paybackAmountMinusFees: int,
                           _originationFeeRepaid: int, _balanceIncrease: int, _repaidWholeLoan: bool):
        pass

    @interface
    def updateStateOnRedeem(self, _reserve: Address, _user: Address, _amountRedeemed: int,
                            _userRedeemEverything: bool) -> None:
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


# An interface to fee provider
class LiquidationManagerInterface(InterfaceScore):
    @interface
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int) -> str:
        pass

class RewardInterface(InterfaceScore):
    @interface
    def distribute(self) -> None:


class LendingPool(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCore', db, value_type=Address)
        self._dataProviderAddress = VarDB('lendingPoolDataProvider', db, value_type=Address)
        self._borrowWallets = ArrayDB('borrowWallets', db, value_type=Address)
        self._depositWallets = ArrayDB('depositWallets', db, value_type=Address)
        self._feeProviderAddress = VarDB('feeProvider', db, value_type=Address)
        self._sIcxAddress = VarDB('SICXAddress', db, value_type=Address)
        self._oIcxAddress = VarDB('oicxAddress', db, value_type=Address)
        self._stakingAddress = VarDB('stakingAddress', db, value_type=Address)
        self._rewardAddress = VarDB('rewardAddress', db, value_type=Address)
        self._liquidationManagerAddress = VarDB('liquidationManagerAddress', db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def PrintData(self, _topic: str, _d1: int, _d2: int, _d3: int):
        pass

    @eventlog(indexed=3)
    def Deposit(self, _reserve: Address, _sender: Address, _amount: int, _timestamp: int):
        pass

    @eventlog(indexed=3)
    def Borrow(self, _reserve: Address, _user: Address, _amount: int, _borrowRate: int, _borrowFee: int,
               _borrowBalanceIncrease: int, _timestamp: int):
        pass

    @eventlog(indexed=3)
    def RedeemUnderlying(self, _reserve: Address, _user: Address, _amount: int, _timestamp: int):
        pass

    @eventlog(indexed=3)
    def Repay(self, _reserve: Address, _user: Address, _paybackAmount: int, _originationFee: int,
              _borrowBalanceIncrease: int, _timestamp: int):
        pass

    @external
    def setLendingPoolCoreAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._lendingPoolCoreAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolCoreAddress(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @external(readonly=True)
    def getLiquidationManagerAddress(self) -> Address:
        return self._liquidationManagerAddress.get()

    @external
    def setLiquidationManagerAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._liquidationManagerAddress.set(_address)

    @external
    def setSICXAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._sIcxAddress.set(_address)

    @external(readonly=True)
    def getSICXAddress(self) -> Address:
        return self._sIcxAddress.get()

    @external
    def setOICXAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._oIcxAddress.set(_address)

    @external(readonly=True)
    def getOICXAddress(self) -> Address:
        return self._oIcxAddress.get()

    @external
    def setStakingAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._stakingAddress.set(_address)

    @external(readonly=True)
    def getStakingAddress(self) -> Address:
        return self._stakingAddress.get()

    @external
    def setRewardAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._rewardAddress.set(_address)

    @external(readonly=True)
    def getRewardAddress(self) -> Address:
        return self._rewardAddress.get()

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

    @external(readonly=True)
    def getBorrowWallets(self,  _index: int) -> list:
        wallets = []
        for i,wallet in enumerate(self._borrowWallets):
            if i < _index * BATCH_SIZE:
                continue
            if i >= (_index+1) * BATCH_SIZE:
                break
            wallets.append(wallet)

        return wallets

    @external(readonly=True)
    def getDepositWallets(self,  _index: int) -> list:
        wallets = []
        for i,wallet in enumerate(self._depositWallets):
            if i < _index * BATCH_SIZE:
                continue
            if i >= (_index+1) * BATCH_SIZE:
                break
            wallets.append(wallet)

        return wallets

    @payable
    @external
    def deposit(self, _amount: int):
        if self.msg.value != _amount:
            revert(f'Amount param doesnt match with the icx sent to the Lending Pool')

        # add_collateral must be a method in staking contract
        # self.getSICXAddress() must be replaced by self.getStakingAddress()
        staking = self.create_interface_score(self.getStakingAddress(), StakingInterface)

        # _amount will now be equal to equivalent amt of sICX
        _amount = staking.icx(self.msg.value).addCollateral(self._lendingPoolCoreAddress.get())
        _reserve = self._sIcxAddress.get()

        self._deposit(_reserve, _amount)

    def _deposit(self, _reserve: Address, _amount: int):
        """
        deposits the underlying asset to the reserve
        :param _reserve:the address of the reserve
        :param _amount:the amount to be deposited
        :return:
        """
        if self.tx.origin not in self._depositWallets:
            self._depositWallets.put(self.tx.origin)
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserve = self.create_interface_score(_reserve, ReserveInterface)
        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()
        reserveData = core.getReserveData(_reserve)
        oTokenAddress = reserveData['oTokenAddress']
        oToken = self.create_interface_score(oTokenAddress, OTokenInterface)
        isFirstDeposit = False
        if oToken.balanceOf(self.tx.origin) == 0:
            isFirstDeposit = True

        core.updateStateOnDeposit(_reserve, self.tx.origin, _amount, isFirstDeposit)
        oToken.mintOnDeposit(self.tx.origin, _amount)
        if _reserve != self._sIcxAddress.get():
            reserve.transfer(self._lendingPoolCoreAddress.get(), _amount)

        self.Deposit(_reserve, self.tx.origin, _amount, self.block.timestamp)

    @external
    def redeemUnderlying(self, _reserve: Address, _user: Address, _amount: int, _oTokenbalanceAfterRedeem: int,
                         _waitForUnstaking: bool = False):
        """
        redeems the underlying amount of assets requested by the _user.This method is called from the oToken contract
        :param _reserve:the address of the reserve
        :param _user:the address of the user requesting the redeem
        :param _amount:the amount to be deposited, should be -1 if the user wants to redeem everything
        :param _oTokenbalanceAfterRedeem:the remaining balance of _user after the redeem is successful
        :return:
        """

        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        if core.getReserveAvailableLiquidity(_reserve) < _amount:
            revert(f'There is not enough liquidity available to redeem')

        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()

        core.updateStateOnRedeem(_reserve, _user, _amount, _oTokenbalanceAfterRedeem == 0)
        if _waitForUnstaking:
            self._require(self.msg.sender == self._oIcxAddress.get(),
                          "Redeem with wait for unstaking failed: Invalid token")
            transferData = "{\"method\": \"unstake\"}".encode("utf-8")
            core.transferToUser(_reserve, self._stakingAddress.get(), _amount, transferData)
            self.RedeemUnderlying(_reserve, _user, _amount, self.block.timestamp)
            return

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
        if self.tx.origin not in self._borrowWallets:
            self._borrowWallets.put(self.tx.origin)
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        dataProvider = self.create_interface_score(self._dataProviderAddress.get(), DataProviderInterface)
        feeProvider = self.create_interface_score(self._feeProviderAddress.get(), FeeProviderInterface)

        self._require(core.isReserveBorrowingEnabled(_reserve), "Borrow error:borrowing not enabled in  the reserve")

        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()

        availableLiquidity = core.getReserveAvailableLiquidity(_reserve)
        self.PrintData("available liquidity at pool line 245", availableLiquidity, 0, 0)

        self._require(availableLiquidity >= _amount, "Borrow error:Not enough available liquidity in the reserve")

        userData = dataProvider.getUserAccountData(self.msg.sender)
        userCollateralBalanceUSD = userData['totalCollateralBalanceUSD']
        userBorrowBalanceUSD = userData['totalBorrowBalanceUSD']
        userTotalFeesUSD = userData['totalFeesUSD']
        currentLTV = userData['currentLtv']
        currentLiquidationThreshold = userData['currentLiquidationThreshold']
        healthFactorBelowThreshold = userData['healthFactorBelowThreshold']
        self.PrintData("data at pool line 256", userCollateralBalanceUSD, userBorrowBalanceUSD, userTotalFeesUSD)

        self._require(userCollateralBalanceUSD > 0, "Borrow error:The user dont have any collateral")
        self._require(not healthFactorBelowThreshold, "Borrow error:Health factor is below threshold")

        borrowFee = feeProvider.calculateOriginationFee(self.msg.sender, _amount)

        self._require(borrowFee > 0, "Borrow error:borrow amount is very small")
        amountOfCollateralNeededUSD = dataProvider.calculateCollateralNeededUSD(_reserve, _amount, borrowFee,
                                                                                userBorrowBalanceUSD,
                                                                                userTotalFeesUSD, currentLTV)

        self.PrintData("amout of collateral needed USD pool line 268", amountOfCollateralNeededUSD, 0, 0)
        self._require(amountOfCollateralNeededUSD <= userCollateralBalanceUSD,
                      "Borrow error:Insufficient collateral to cover new borrow")
        borrowData = core.updateStateOnBorrow(_reserve, self.msg.sender, _amount, borrowFee)
        core.transferToUser(_reserve, self.msg.sender, _amount)
        self.Borrow(_reserve, self.msg.sender, _amount, borrowData['currentBorrowRate'], borrowFee,
                    borrowData['balanceIncrease'], self.block.timestamp)

    @external
    def repay(self, _reserve: Address, _amount: int):
        """
        repays a borrow on the specific reserve, for the specified amount (or for the whole amount, if -1 is send as params for _amount).
        :param _reserve:the address of the reserve
        :param _amount:the amount to repay,should be -1 if the user wants to repay everything
        :return:
        """
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserve = self.create_interface_score(_reserve, ReserveInterface)
        borrowData = core.getUserBorrowBalances(_reserve, self.tx.origin)
        userBasicReserveData = core.getUserBasicReserveData(_reserve, self.tx.origin)

        self._require(borrowData['compoundedBorrowBalance'] > 0, 'The user does not have any borrow pending')
        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()

        paybackAmount = borrowData['compoundedBorrowBalance'] + userBasicReserveData['originationFee']

        if _amount != -1 and _amount < paybackAmount:
            paybackAmount = _amount

        if paybackAmount <= userBasicReserveData['originationFee']:
            core.updateStateOnRepay(_reserve, self.tx.origin, 0, paybackAmount, borrowData['borrowBalanceIncrease'],
                                    False)
            # core.transferToFeeCollectionAddress
            reserve.transfer(self._feeProviderAddress.get(), paybackAmount)

            self.Repay(_reserve, self.tx.origin, 0, paybackAmount, borrowData['borrowBalanceIncrease'],
                       self.block.timestamp)
            return

        paybackAmountMinusFees = paybackAmount - userBasicReserveData['originationFee']
        core.updateStateOnRepay(_reserve, self.tx.origin, paybackAmountMinusFees,
                                userBasicReserveData['originationFee'], borrowData['borrowBalanceIncrease'],
                                borrowData['compoundedBorrowBalance'] == paybackAmountMinusFees)

        if userBasicReserveData['originationFee'] > 0:
            # core.transferToFeeCollectionAddress
            reserve.transfer(self._feeProviderAddress.get(), userBasicReserveData['originationFee'])

        reserve.transfer(self._lendingPoolCoreAddress.get(), paybackAmountMinusFees)
        self.Repay(_reserve, self.tx.origin, paybackAmountMinusFees, userBasicReserveData['originationFee'],
                   borrowData['borrowBalanceIncrease'], self.block.timestamp)

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
        liquidationManager = self.create_interface_score(self.getLiquidationManagerAddress(),
                                                         LiquidationManagerInterface)
        core = self.create_interface_score(self.getLendingPoolCoreAddress(), CoreInterface)
        liquidation = liquidationManager.liquidationCall(_collateral, _reserve, _user, _purchaseAmount)
        principalCurrency = self.create_interface_score(_reserve, ReserveInterface)
        core.transferToUser(_collateral, self.tx.origin, liquidation['maxCollateralToLiquidate'])
        principalCurrency.transfer(self.getLendingPoolCoreAddress(), liquidation['actualAmountToLiquidate'])
        if _purchaseAmount > liquidation['actualAmountToLiquidate']:
            principalCurrency.transfer(self.tx.origin, _purchaseAmount - liquidation['actualAmountToLiquidate'])

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        try:
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            revert(f'Invalid data: {_data}. Exception: {e}')
        if set(d.keys()) != set(["method", "params"]):
            revert('Invalid parameters.')
        if d["method"] == "deposit":
            self._deposit(self.msg.sender, d["params"].get("amount", -1))
        elif d["method"] == "repay":
            self.repay(self.msg.sender, d["params"].get("amount", -1))
        elif d["method"] == "liquidationCall":
            self.liquidationCall(Address.from_string(d["params"].get("_collateral")),
                                 Address.from_string(d["params"].get("_reserve")),
                                 Address.from_string(d["params"].get("_user")),
                                 d["params"].get("_purchaseAmount"))
        else:
            revert(f'No valid method called, data: {_data}')
