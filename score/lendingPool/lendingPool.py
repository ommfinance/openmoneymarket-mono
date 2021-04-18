from iconservice import *
from .utils.checks import *

TAG = 'LendingPool'
BATCH_SIZE = 100


class UserSnapshotData(TypedDict):
    principalOTokenBalance: int
    principalBorrowBalance: int
    userLiquidityCumulativeIndex: int
    userBorrowCumulativeIndex: int


class ReserveSnapshotData(TypedDict):
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex: int
    lastUpdateTimestamp: int
    price:int


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
    def stakeICX(self, _to: Address, _data: bytes = None) -> int:
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

    @interface
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass


# An interface to fee provider
class FeeProviderInterface(InterfaceScore):
    @interface
    def calculateOriginationFee(self, _user: Address, _amount: int) -> int:
        pass


# An interface to fee provider
class LiquidationManagerInterface(InterfaceScore):
    @interface
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int) -> str:
        pass


# An interface to Rewards
class RewardInterface(InterfaceScore):
    @interface
    def distribute(self) -> None:
        pass


# An interface to Snapshot
class SnapshotInterface(InterfaceScore):
    @interface
    def updateUserSnapshot(self, _user: Address, _reserve: Address, _userData: UserSnapshotData) -> None:
        pass

    @interface
    def updateReserveSnapshot(self, _reserve: Address, _reserveData: ReserveSnapshotData) -> None:
        pass


class LendingPool(IconScoreBase):
    LENDING_POOL_CORE = 'lendingPoolCore'
    LENDING_POOL_DATA_PROVIDER = 'lendingPoolDataProvider'
    BORROW_WALLETS = 'borrowWallets'
    DEPOSIT_WALLETS = 'depositWallets'
    FEE_PROVIDER = 'feeProvider'
    sICX_ADDRESS = 'sICXAddress'
    oICX_ADDRESS = 'oicxAddress'
    STAKING_ADDRESS = 'stakingAddress'
    REWARD_ADDRESS = 'rewardAddress'
    LIQUIDATION_MANAGER_ADDRESS = 'liquidationManagerAddress'
    SNAPSHOT = 'snapshot'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._lendingPoolCoreAddress = VarDB(self.LENDING_POOL_CORE, db, value_type=Address)
        self._dataProvider = VarDB(self.LENDING_POOL_DATA_PROVIDER, db, value_type=Address)
        self._borrowWallets = ArrayDB(self.BORROW_WALLETS, db, value_type=Address)
        self._depositWallets = ArrayDB(self.DEPOSIT_WALLETS, db, value_type=Address)
        self._feeProviderAddress = VarDB(self.FEE_PROVIDER, db, value_type=Address)
        self._sIcxAddress = VarDB(self.sICX_ADDRESS, db, value_type=Address)
        self._oIcxAddress = VarDB(self.oICX_ADDRESS, db, value_type=Address)
        self._stakingAddress = VarDB(self.STAKING_ADDRESS, db, value_type=Address)
        self._rewardAddress = VarDB(self.REWARD_ADDRESS, db, value_type=Address)
        self._snapshot = VarDB(self.SNAPSHOT, db, value_type=Address)
        self._liquidationManagerAddress = VarDB(self.LIQUIDATION_MANAGER_ADDRESS, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

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

    @only_owner
    @external
    def setLendingPoolCore(self, _address: Address) -> None:
        self._lendingPoolCoreAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmLendingPool"

    @only_owner
    @external
    def setLiquidationManager(self, _address: Address) -> None:
        self._liquidationManagerAddress.set(_address)

    @external(readonly=True)
    def getLiquidationManager(self) -> Address:
        return self._liquidationManagerAddress.get()

    @only_owner
    @external
    def setSICX(self, _address: Address) -> None:
        self._sIcxAddress.set(_address)

    @external(readonly=True)
    def getSICX(self) -> Address:
        return self._sIcxAddress.get()

    @only_owner
    @external
    def setOICX(self, _address: Address) -> None:
        self._oIcxAddress.set(_address)

    @external(readonly=True)
    def getOICX(self) -> Address:
        return self._oIcxAddress.get()

    @only_owner
    @external
    def setStaking(self, _address: Address) -> None:
        self._stakingAddress.set(_address)

    @external(readonly=True)
    def getStaking(self) -> Address:
        return self._stakingAddress.get()

    @only_owner
    @external
    def setReward(self, _address: Address) -> None:
        self._rewardAddress.set(_address)

    @external(readonly=True)
    def getReward(self) -> Address:
        return self._rewardAddress.get()

    @only_owner
    @external
    def setLendingPoolDataProvider(self, _address: Address) -> None:
        self._dataProvider.set(_address)

    @external(readonly=True)
    def getLendingPoolDataProvider(self) -> Address:
        return self._dataProvider.get()

    @only_owner
    @external
    def setFeeProvider(self, _address: Address) -> None:
        self._feeProviderAddress.set(_address)

    @external(readonly=True)
    def getFeeProvider(self) -> Address:
        return self._feeProviderAddress.get()

    @only_owner
    @external
    def setSnapshot(self, _address: Address):
        self._snapshot.set(_address)

    @external(readonly=True)
    def getSnapshot(self) -> Address:
        return self._snapshot.get()

    @external(readonly=True)
    def getBorrowWallets(self, _index: int) -> list:
        return self._get_array_items(self._borrowWallets, _index)
        
    @external(readonly=True)
    def getDepositWallets(self, _index: int) -> list:
        return self._get_array_items(self._depositWallets, _index)

    @payable
    @external
    def deposit(self, _amount: int):
        if self.msg.value != _amount:
            revert(f'Amount param doesnt match with the icx sent to the Lending Pool')

        # add_collateral must be a method in staking contract
        # self.getSICXAddress() must be replaced by self.getStakingAddress()
        staking = self.create_interface_score(self.getStaking(), StakingInterface)

        # _amount will now be equal to equivalent amt of sICX
        _amount = staking.icx(self.msg.value).stakeICX(self._lendingPoolCoreAddress.get())
        _reserve = self._sIcxAddress.get()
        self._deposit(_reserve, _amount, self.msg.sender)

    def _deposit(self, _reserve: Address, _amount: int, _sender: Address):
        """
        deposits the underlying asset to the reserve
        :param _reserve:the address of the reserve
        :param _amount:the amount to be deposited
        :return:
        """
        if _sender not in self._depositWallets:
            self._depositWallets.put(_sender)
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserve = self.create_interface_score(_reserve, ReserveInterface)
        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()
        reserveData = core.getReserveData(_reserve)
        oTokenAddress = reserveData['oTokenAddress']

        oToken = self.create_interface_score(oTokenAddress, OTokenInterface)
        isFirstDeposit = False
        if oToken.balanceOf(_sender) == 0:
            isFirstDeposit = True
        core.updateStateOnDeposit(_reserve, _sender, _amount, isFirstDeposit)

        oToken.mintOnDeposit(_sender, _amount)
        if _reserve != self._sIcxAddress.get():
            reserve.transfer(self._lendingPoolCoreAddress.get(), _amount)

        self._updateSnapshot(_reserve, _sender)

        self.Deposit(_reserve, _sender, _amount, self.block.timestamp)

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
        reserveData = core.getReserveData(_reserve)
        if self.msg.sender != reserveData['oTokenAddress']:
            revert(f'{TAG}'
                   f'{self.msg.sender} is unauthorized to call,only otoken can invoke the method')
        if core.getReserveAvailableLiquidity(_reserve) < _amount:
            revert(f'There is not enough liquidity available to redeem')

        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()

        core.updateStateOnRedeem(_reserve, _user, _amount, _oTokenbalanceAfterRedeem == 0)
        if _waitForUnstaking:
            self._require(self.msg.sender == self._oIcxAddress.get(),
                          "Redeem with wait for unstaking failed: Invalid token")
            transferData = {"method":"unstake","user":str(_user)}          
            transferDataBytes = json_dumps(transferData).encode("utf-8")
            core.transferToUser(_reserve, self._stakingAddress.get(), _amount, transferDataBytes)
            self.RedeemUnderlying(_reserve, _user, _amount, self.block.timestamp)
            return

        core.transferToUser(_reserve, _user, _amount)

        self._updateSnapshot(_reserve, _user)
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
        if self.msg.sender not in self._borrowWallets:
            self._borrowWallets.put(self.msg.sender)
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        dataProvider = self.create_interface_score(self._dataProvider.get(), DataProviderInterface)
        feeProvider = self.create_interface_score(self._feeProviderAddress.get(), FeeProviderInterface)

        self._require(core.isReserveBorrowingEnabled(_reserve), "Borrow error:borrowing not enabled in  the reserve")

        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()

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

        borrowFee = feeProvider.calculateOriginationFee(_amount)

        self._require(borrowFee > 0, "Borrow error:borrow amount is very small")
        amountOfCollateralNeededUSD = dataProvider.calculateCollateralNeededUSD(_reserve, _amount, borrowFee,
                                                                                userBorrowBalanceUSD,
                                                                                userTotalFeesUSD, currentLTV)

        self._require(amountOfCollateralNeededUSD <= userCollateralBalanceUSD,
                      "Borrow error:Insufficient collateral to cover new borrow")

        borrowData = core.updateStateOnBorrow(_reserve, self.msg.sender, _amount, borrowFee)

        core.transferToUser(_reserve, self.msg.sender, _amount)
        self._updateSnapshot(_reserve, self.msg.sender)
        self.Borrow(_reserve, self.msg.sender, _amount, borrowData['currentBorrowRate'], borrowFee,
                    borrowData['balanceIncrease'], self.block.timestamp)

    def _repay(self, _reserve: Address, _amount: int, _sender: Address):
        """
        repays a borrow on the specific reserve, for the specified amount (or for the whole amount, if -1 is send as params for _amount).
        :param _reserve:the address of the reserve
        :param _amount:the amount to repay,should be -1 if the user wants to repay everything
        :return:
        """
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserve = self.create_interface_score(_reserve, ReserveInterface)
        borrowData = core.getUserBorrowBalances(_reserve, _sender)
        userBasicReserveData = core.getUserBasicReserveData(_reserve, _sender)

        self._require(borrowData['compoundedBorrowBalance'] > 0, 'The user does not have any borrow pending')
        reward = self.create_interface_score(self._rewardAddress.get(), RewardInterface)
        reward.distribute()

        paybackAmount = borrowData['compoundedBorrowBalance'] + userBasicReserveData['originationFee']
        returnAmount = 0 
        if  _amount < paybackAmount:
            paybackAmount = _amount
        else :
            returnAmount = _amount - paybackAmount

        if paybackAmount <= userBasicReserveData['originationFee']:
            core.updateStateOnRepay(_reserve, _sender, 0, paybackAmount, borrowData['borrowBalanceIncrease'],
                                    False)
            # core.transferToFeeCollectionAddress
            reserve.transfer(self._feeProviderAddress.get(), paybackAmount)

            self.Repay(_reserve, _sender, 0, paybackAmount, borrowData['borrowBalanceIncrease'],
                       self.block.timestamp)
            return

        paybackAmountMinusFees = paybackAmount - userBasicReserveData['originationFee']
        core.updateStateOnRepay(_reserve, _sender, paybackAmountMinusFees,
                                userBasicReserveData['originationFee'], borrowData['borrowBalanceIncrease'],
                                borrowData['compoundedBorrowBalance'] == paybackAmountMinusFees)

        if userBasicReserveData['originationFee'] > 0:
            # core.transferToFeeCollectionAddress
            reserve.transfer(self._feeProviderAddress.get(), userBasicReserveData['originationFee'])

        reserve.transfer(self._lendingPoolCoreAddress.get(), paybackAmountMinusFees)
        self._updateSnapshot(_reserve, _sender)
        # transfer excess amount back to the user
        if returnAmount > 0 :
            reserve.transfer(_sender,returnAmount)
        self.Repay(_reserve, _sender, paybackAmountMinusFees, userBasicReserveData['originationFee'],
                   borrowData['borrowBalanceIncrease'], self.block.timestamp)

    @payable
    @external
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int, _sender: Address):
        """
        liquidates an undercollateralized loan
        :param _collateral:the address of the collateral to be liquidated
        :param _reserve:the address of the reserve
        :param _user:the address of the borrower
        :param _purchaseAmount:the amount to liquidate
        :return:
        """
        liquidationManager = self.create_interface_score(self.getLiquidationManager(),
                                                         LiquidationManagerInterface)
        core = self.create_interface_score(self.getLendingPoolCore(), CoreInterface)
        liquidation = liquidationManager.liquidationCall(_collateral, _reserve, _user, _purchaseAmount)
        principalCurrency = self.create_interface_score(_reserve, ReserveInterface)
        core.transferToUser(_collateral, _sender, liquidation['maxCollateralToLiquidate'])
        principalCurrency.transfer(self.getLendingPoolCore(), liquidation['actualAmountToLiquidate'])
        if _purchaseAmount > liquidation['actualAmountToLiquidate']:
            principalCurrency.transfer(_sender, _purchaseAmount - liquidation['actualAmountToLiquidate'])

        self._updateSnapshot(_reserve, _user)
        self._updateSnapshot(_collateral)

    def _updateSnapshot(self, _reserve: Address, _user: Address = None):
        dataProvider = self.create_interface_score(self._dataProvider.get(), DataProviderInterface)
        snapshot = self.create_interface_score(self._snapshot.get(), SnapshotInterface)

        if _user:
            userReserve = dataProvider.getUserReserveData(_reserve, _user)
            userData: UserSnapshotData = {
                'principalOTokenBalance': userReserve['principalOTokenBalance'],
                'principalBorrowBalance': userReserve['principalBorrowBalance'],
                'userLiquidityCumulativeIndex': userReserve['userLiquidityCumulativeIndex'],
                'userBorrowCumulativeIndex': userReserve['userBorrowCumulativeIndex']
            }
            snapshot.updateUserSnapshot(_user, _reserve, userData)

        reserve = dataProvider.getReserveData(_reserve)
        reserveData: ReserveSnapshotData = {
            'liquidityRate': reserve['liquidityRate'],
            'borrowRate': reserve['borrowRate'],
            'liquidityCumulativeIndex': reserve['liquidityCumulativeIndex'],
            'borrowCumulativeIndex': reserve['borrowCumulativeIndex'],
            'lastUpdateTimestamp': reserve['lastUpdateTimestamp'],
            'price': reserve['exchangePrice']

        }

        snapshot.updateReserveSnapshot(_reserve, reserveData)


    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        try:
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            revert(f'Invalid data: {_data}. Exception: {e}')
        if set(d.keys()) != set(["method", "params"]):
            revert('Invalid parameters.')
        if d["method"] == "deposit":
            self._deposit(self.msg.sender, d["params"].get("amount", -1), _from)
        elif d["method"] == "repay":
            self._repay(self.msg.sender, d["params"].get("amount", -1), _from)
        elif d["method"] == "liquidationCall":
            self.liquidationCall(Address.from_string(d["params"].get("_collateral")),
                                 Address.from_string(d["params"].get("_reserve")),
                                 Address.from_string(d["params"].get("_user")),
                                 d["params"].get("_purchaseAmount"), _from)
        else:
            revert(f'No valid method called, data: {_data}')


    def _get_array_items(self, arraydb, index: int = 0) -> list:
        items = []
        length = len(arraydb)
        start = index * BATCH_SIZE

        if start >= length:
            return items

        end = start + BATCH_SIZE
        end = length if end > length else end

        for idx in range(start, end):
            items.append(arraydb[idx])

        return items