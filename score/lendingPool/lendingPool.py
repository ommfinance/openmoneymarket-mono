from .utils.checks import *
from .utils.math import *

BATCH_SIZE = 50
TERM_LENGTH = 43120

# ADDRESSES
sICX = "sICX"
oICX = "oICX"
LENDING_POOL_DATA_PROVIDER = "lendingPoolDataProvider"
STAKING = "staking"
OMM_TOKEN = "ommToken"
BRIDGE_OTOKEN = "bridgeOToken"
REWARDS = "rewards"
LENDING_POOL_CORE = "lendingPoolCore"
FEE_PROVIDER = "feeProvider"
LIQUIDATION_MANAGER = "liquidationManager"


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
    def distribute(self):
        pass

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
    def updateStateOnDeposit(self, _reserve: Address, _user: Address, _amount: int, _isFirstDeposit: bool) -> None:
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


class LendingPool(IconScoreBase):
    BORROW_WALLETS = 'borrowWallets'
    DEPOSIT_WALLETS = 'depositWallets'
    BORROW_INDEX = 'borrowIndex'
    DEPOSIT_INDEX = 'depositIndex'
    FEE_SHARING_USERS = 'feeSharingUsers'
    FEE_SHARING_TXN_LIMIT = 'feeSharingTxnLimit'
    BRIDGE_FEE_THRESHOLD = "bridgeFeeThreshold"
    ADDRESSES = "addresses"
    CONTRACTS = "contracts"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._addresses = DictDB(self.ADDRESSES, db, value_type=Address)
        self._contracts = ArrayDB(self.CONTRACTS, db, value_type=str)
        self._borrowWallets = ArrayDB(self.BORROW_WALLETS, db, value_type=Address)
        self._depositWallets = ArrayDB(self.DEPOSIT_WALLETS, db, value_type=Address)
        self._borrowIndex = DictDB(self.BORROW_INDEX, db, value_type=int)
        self._depositIndex = DictDB(self.DEPOSIT_INDEX, db, value_type=int)
        self._feeSharingUsers = DictDB(self.FEE_SHARING_USERS, db, value_type=int, depth=2)
        self._feeSharingTxnLimit = VarDB(self.FEE_SHARING_TXN_LIMIT, db, value_type=int)
        self._bridgeFeeThreshold = VarDB(self.BRIDGE_FEE_THRESHOLD, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._bridgeFeeThreshold.set(0)

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

    @origin_owner
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for contracts in _addressDetails:
            if contracts['name'] not in self._contracts:
                self._contracts.put(contracts['name'])
            self._addresses[contracts['name']] = contracts['address']

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return {item: self._addresses[item] for item in self._contracts}

    @external(readonly=True)
    def getAddress(self, _name: str) -> Address:
        return self._addresses[_name]

    @external(readonly=True)
    def name(self) -> str:
        return "OmmLendingPool"

    @only_owner
    @external
    def setBridgeFeeThreshold(self, _amount: int) -> None:
        self._bridgeFeeThreshold.set(_amount)

    @external(readonly=True)
    def getBridgeFeeThreshold(self) -> int:
        return self._bridgeFeeThreshold.get()

    @external(readonly=True)
    def getBorrowWallets(self, _index: int) -> list:
        return self._get_array_items(self._borrowWallets, _index)

    @external(readonly=True)
    def getDepositWallets(self, _index: int) -> list:
        return self._get_array_items(self._depositWallets, _index)

    @only_owner
    @external
    def setFeeSharingTxnLimit(self, _limit: int) -> None:
        self._feeSharingTxnLimit.set(_limit)

    @external(readonly=True)
    def getFeeSharingTxnLimit(self) -> int:
        return self._feeSharingTxnLimit.get()

    def _userBridgeDepositStatus(self, _user: Address) -> bool:
        bridgeOtoken = self.create_interface_score(self.getAddress(BRIDGE_OTOKEN), OTokenInterface)
        return bridgeOtoken.balanceOf(_user) > self._bridgeFeeThreshold.get()

    def _enableFeeSharing(self):
        if not self._feeSharingUsers[self.msg.sender]['startHeight']:
            self._feeSharingUsers[self.msg.sender]['startHeight'] = self.block_height
        if self._feeSharingUsers[self.msg.sender]['startHeight'] + TERM_LENGTH > self.block_height:
            if self._feeSharingUsers[self.msg.sender]['txnCount'] < self._feeSharingTxnLimit.get():
                self._feeSharingUsers[self.msg.sender]['txnCount'] += 1
                self.set_fee_sharing_proportion(100)
        else:
            self._feeSharingUsers[self.msg.sender]['startHeight'] = self.block_height
            self._feeSharingUsers[self.msg.sender]['txnCount'] = 1
            self.set_fee_sharing_proportion(100)

    @payable
    @external
    def deposit(self, _amount: int):
        if self.msg.value != _amount:
            revert(
                f'{TAG}: Amount in param {_amount} doesnt match with the icx sent {self.msg.value} to the Lending Pool')

        staking = self.create_interface_score(self.getAddress(STAKING), StakingInterface)

        rate = staking.getTodayRate()

        # getting equivalent sicx amount for the icx
        _amount = EXA * self.msg.value // rate
        _reserve = self.getAddress(sICX)
        self._deposit(_reserve, _amount, self.msg.sender)

    def _deposit(self, _reserve: Address, _amount: int, _sender: Address):
        """
        deposits the underlying asset to the reserve
        :param _reserve:the address of the reserve
        :param _amount:the amount to be deposited
        :return:
        """
        # checking for active and unfreezed reserve,deposit is allowed only for active and unfreezed reserve
        if self._userBridgeDepositStatus(self.msg.sender):
            self._enableFeeSharing()
        lendingPoolCoreAddress = self.getAddress(LENDING_POOL_CORE)
        core = self.create_interface_score(lendingPoolCoreAddress, CoreInterface)
        reserveData = core.getReserveData(_reserve)
        self._require(reserveData['isActive'], "Reserve is not active,deposit unsuccessful")
        self._require(not reserveData['isFreezed'], "Reserve is frozen,deposit unsuccessful")

        if not self._depositIndex[_sender]:
            # add new entry
            self._depositWallets.put(_sender)
            self._depositIndex[_sender] = len(self._depositWallets)

        reserve = self.create_interface_score(_reserve, ReserveInterface)
        staking = self.create_interface_score(self.getAddress(STAKING), StakingInterface)
        reward = self.create_interface_score(self.getAddress(REWARDS), RewardInterface)
        reward.distribute()
        oTokenAddress = reserveData['oTokenAddress']

        oToken = self.create_interface_score(oTokenAddress, OTokenInterface)
        core.updateStateOnDeposit(_reserve, _sender, _amount, oToken.balanceOf(_sender) == 0)

        oToken.mintOnDeposit(_sender, _amount)
        if _reserve != self.getAddress(sICX):
            reserve.transfer(lendingPoolCoreAddress, _amount)
        else:
            # icx sent to staking contract and equivalent sicx received to lendingPoolCore
            _amount = staking.icx(self.msg.value).stakeICX(lendingPoolCoreAddress)
        # self._updateSnapshot(_reserve, _sender)

        self.Deposit(_reserve, _sender, _amount, self.now())

    @external
    def redeem(self, _oToken: Address, _amount: int, _waitForUnstaking: bool = False) -> None:
        if self._userBridgeDepositStatus(self.msg.sender):
            self._enableFeeSharing()
        oToken = self.create_interface_score(_oToken, OTokenInterface)
        redeemParams = oToken.redeem(self.msg.sender, _amount)
        self.redeemUnderlying(redeemParams['reserve'], self.msg.sender, _oToken, redeemParams['amountToRedeem'],
                              redeemParams['oTokenRemaining'], _waitForUnstaking)

    @external
    def claimRewards(self):
        if self._userBridgeDepositStatus(self.msg.sender):
            self._enableFeeSharing()
        rewards = self.create_interface_score(self.getAddress(REWARDS), RewardInterface)
        rewards.claimRewards(self.msg.sender)

    @external
    def stake(self, _value: int):
        if self._userBridgeDepositStatus(self.msg.sender):
            self._enableFeeSharing()
        ommToken = self.create_interface_score(self.getAddress(OMM_TOKEN), OmmTokenInterface)
        ommToken.stake(_value, self.msg.sender)

    @external
    def unstake(self, _value: int):
        if self._userBridgeDepositStatus(self.msg.sender):
            self._enableFeeSharing()
        ommToken = self.create_interface_score(self.getAddress(OMM_TOKEN), OmmTokenInterface)
        ommToken.unstake(_value, self.msg.sender)

    def redeemUnderlying(self, _reserve: Address, _user: Address, _oToken: Address, _amount: int,
                         _oTokenbalanceAfterRedeem: int,
                         _waitForUnstaking: bool = False):
        """
        redeems the underlying amount of assets requested by the _user.This method is called from the oToken contract
        :param _reserve:the address of the reserve
        :param _user:the address of the user requesting the redeem
        :param _amount:the amount to be deposited, should be -1 if the user wants to redeem everything
        :param _oTokenbalanceAfterRedeem:the remaining balance of _user after the redeem is successful
        :param _waitForUnstaking:
        :return:
        """

        # checking for active reserve,redeem  is allowed only for active reserves
        lendingPoolCoreAddress = self.getAddress(LENDING_POOL_CORE)
        core = self.create_interface_score(lendingPoolCoreAddress, CoreInterface)
        reserveData = core.getReserveData(_reserve)
        self._require(reserveData['isActive'], "Reserve is not active,withdraw unsuccessful")
        # if self.msg.sender != reserveData['oTokenAddress']:
        #     revert(f'{TAG}: {self.msg.sender} is unauthorized to call, only otoken can invoke the method')

        reserveAvailableLiquidity = core.getReserveAvailableLiquidity(_reserve)
        if reserveAvailableLiquidity < _amount:
            revert(f'{TAG}: Amount {_amount} is more than available liquidity {reserveAvailableLiquidity}')

        reward = self.create_interface_score(self.getAddress(REWARDS), RewardInterface)
        reward.distribute()

        core.updateStateOnRedeem(_reserve, _user, _amount, _oTokenbalanceAfterRedeem == 0)
        if _waitForUnstaking:
            self._require(_oToken == self.getAddress(oICX),
                          "Redeem with wait for unstaking failed: Invalid token")
            transferData = {"method": "unstake", "user": str(_user)}
            transferDataBytes = json_dumps(transferData).encode("utf-8")
            core.transferToUser(_reserve, self.getAddress(STAKING), _amount, transferDataBytes)
        else:
            core.transferToUser(_reserve, _user, _amount)

        # self._updateSnapshot(_reserve, _user)

        self.RedeemUnderlying(_reserve, _user, _amount, self.now())

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(f'{TAG}: {_message}')

    @external
    def borrow(self, _reserve: Address, _amount: int):
        """
        allows users to borrow _amount of _reserve asset as a loan ,provided that the borrower has already deposited enough amount of collateral
        :param _reserve:the address of the reserve
        :param _amount:the amount to be borrowed
        :return:
        """
        # checking for active and unfreezed reserve,borrow is allowed only for active and unfreezed reserve
        lendingPoolCoreAddress = self.getAddress(LENDING_POOL_CORE)
        core = self.create_interface_score(lendingPoolCoreAddress, CoreInterface)
        reserveData = core.getReserveData(_reserve)
        if self._userBridgeDepositStatus(self.msg.sender):
            self._enableFeeSharing()
        self._require(reserveData['isActive'], "Reserve is not active,borrow unsuccessful")
        self._require(not reserveData['isFreezed'], "Reserve is frozen,borrow unsuccessful")

        self._require(core.isReserveBorrowingEnabled(_reserve), "Borrow error:borrowing not enabled in the reserve")
        if not self._borrowIndex[self.msg.sender]:
            # add new entry
            self._borrowWallets.put(self.msg.sender)
            self._borrowIndex[self.msg.sender] = len(self._borrowWallets)
        dataProviderAddress = self.getAddress(LENDING_POOL_DATA_PROVIDER)
        dataProvider = self.create_interface_score(dataProviderAddress, DataProviderInterface)
        reward = self.create_interface_score(self.getAddress(REWARDS), RewardInterface)
        reward.distribute()
        availableLiquidity = core.getReserveAvailableLiquidity(_reserve)

        self._require(availableLiquidity >= _amount, "Borrow error:Not enough available liquidity in the reserve")

        userData = dataProvider.getUserAccountData(self.msg.sender)
        userCollateralBalanceUSD = userData['totalCollateralBalanceUSD']
        userBorrowBalanceUSD = userData['totalBorrowBalanceUSD']
        userTotalFeesUSD = userData['totalFeesUSD']
        currentLTV = userData['currentLtv']
        healthFactorBelowThreshold = userData['healthFactorBelowThreshold']

        self._require(userCollateralBalanceUSD > 0, "Borrow error:The user does not have any collateral")
        self._require(not healthFactorBelowThreshold, "Borrow error:Health factor is below threshold")
        feeProviderAddress = self.getAddress(FEE_PROVIDER)
        feeProvider = self.create_interface_score(feeProviderAddress, FeeProviderInterface)
        borrowFee = feeProvider.calculateOriginationFee(_amount)

        self._require(borrowFee > 0, "Borrow error:borrow amount is very small")
        amountOfCollateralNeededUSD = dataProvider.calculateCollateralNeededUSD(_reserve, _amount, borrowFee,
                                                                                userBorrowBalanceUSD,
                                                                                userTotalFeesUSD, currentLTV)

        self._require(amountOfCollateralNeededUSD <= userCollateralBalanceUSD,
                      "Borrow error:Insufficient collateral to cover new borrow")

        borrowData: dict = core.updateStateOnBorrow(_reserve, self.msg.sender, _amount, borrowFee)
        core.transferToUser(_reserve, self.msg.sender, _amount)
        # self._updateSnapshot(_reserve, self.msg.sender)
        self.Borrow(_reserve, self.msg.sender, _amount, borrowData['currentBorrowRate'], borrowFee,
                    borrowData['balanceIncrease'], self.now())

    def _repay(self, _reserve: Address, _amount: int, _sender: Address):
        """
        repays a borrow on the specific reserve, for the specified amount (or for the whole amount, if -1 is send as params for _amount).
        :param _reserve:the address of the reserve
        :param _amount:the amount to repay,should be -1 if the user wants to repay everything
        :return:
        """

        # checking for an inactive reserve,repay is allowed for only active reserve
        lendingPoolCoreAddress = self.getAddress(LENDING_POOL_CORE)
        core = self.create_interface_score(lendingPoolCoreAddress, CoreInterface)
        reserveData = core.getReserveData(_reserve)
        self._require(reserveData['isActive'], "Reserve is not active,repay unsuccessful")

        reserve = self.create_interface_score(_reserve, ReserveInterface)
        borrowData: dict = core.getUserBorrowBalances(_reserve, _sender)
        userBasicReserveData: dict = core.getUserBasicReserveData(_reserve, _sender)
        self._require(borrowData['compoundedBorrowBalance'] > 0, 'The user does not have any borrow pending')

        reward = self.create_interface_score(self.getAddress(REWARDS), RewardInterface)
        reward.distribute()

        paybackAmount = borrowData['compoundedBorrowBalance'] + userBasicReserveData['originationFee']
        returnAmount = 0
        if _amount < paybackAmount:
            paybackAmount = _amount
        else:
            returnAmount = _amount - paybackAmount

        if paybackAmount <= userBasicReserveData['originationFee']:
            core.updateStateOnRepay(_reserve, _sender, 0, paybackAmount, borrowData['borrowBalanceIncrease'],
                                    False)
            # transfer to feeProvider
            feeProviderAddress = self.getAddress(FEE_PROVIDER)
            reserve.transfer(feeProviderAddress, paybackAmount)

            self.Repay(_reserve, _sender, 0, paybackAmount, borrowData['borrowBalanceIncrease'],
                       self.now())

            # self._updateSnapshot(_reserve, _sender)
            return

        paybackAmountMinusFees = paybackAmount - userBasicReserveData['originationFee']
        core.updateStateOnRepay(_reserve, _sender, paybackAmountMinusFees,
                                userBasicReserveData['originationFee'], borrowData['borrowBalanceIncrease'],
                                borrowData['compoundedBorrowBalance'] == paybackAmountMinusFees)

        if userBasicReserveData['originationFee'] > 0:
            # fee transfer to feeProvider
            feeProviderAddress = self.getAddress(FEE_PROVIDER)
            reserve.transfer(feeProviderAddress, userBasicReserveData['originationFee'])

        reserve.transfer(lendingPoolCoreAddress, paybackAmountMinusFees)
        # self._updateSnapshot(_reserve, _sender)
        # transfer excess amount back to the user
        if returnAmount > 0:
            reserve.transfer(_sender, returnAmount)
        self.Repay(_reserve, _sender, paybackAmountMinusFees, userBasicReserveData['originationFee'],
                   borrowData['borrowBalanceIncrease'], self.now())

    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int,
                        _sender: Address):
        """
        liquidates an undercollateralized loan
        :param _collateral:the address of the collateral to be liquidated
        :param _reserve:the address of the reserve
        :param _user:the address of the borrower
        :param _purchaseAmount:the amount to liquidate
        :param _sender:
        :return:
        """
        # checking for an inactive reserve,liquidation is allowed only if both reserves are active
        lendingPoolCoreAddress = self.getAddress(LENDING_POOL_CORE)
        core = self.create_interface_score(lendingPoolCoreAddress, CoreInterface)
        reserveData = core.getReserveData(_reserve)
        collateralData = core.getReserveData(_collateral)
        self._require(reserveData['isActive'], "Borrow reserve is not active,liquidation unsuccessful")
        self._require(collateralData['isActive'], "Collateral reserve is not active,liquidation unsuccessful")

        liquidationManager = self.create_interface_score(self.getAddress(LIQUIDATION_MANAGER),
                                                         LiquidationManagerInterface)
        core = self.create_interface_score(lendingPoolCoreAddress, CoreInterface)
        liquidation = liquidationManager.liquidationCall(_collateral, _reserve, _user, _purchaseAmount)
        principalCurrency = self.create_interface_score(_reserve, ReserveInterface)
        core.transferToUser(_collateral, _sender, liquidation['maxCollateralToLiquidate'])
        principalCurrency.transfer(lendingPoolCoreAddress, liquidation['actualAmountToLiquidate'])
        if _purchaseAmount > liquidation['actualAmountToLiquidate']:
            principalCurrency.transfer(_sender, _purchaseAmount - liquidation['actualAmountToLiquidate'])

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        d = None
        try:
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            revert(f'{TAG}: Invalid data: {_data}. Exception: {e}')
        if set(d.keys()) != {"method", "params"}:
            revert(f'{TAG}: Invalid parameters.')
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
            revert(f'{TAG}: No valid method called, data: {_data}')

    @staticmethod
    def _get_array_items(arraydb, index: int = 0) -> list:
        length = len(arraydb)
        start = index * BATCH_SIZE

        if start >= length:
            return []

        end = start + BATCH_SIZE
        end = length if end > length else end
        return [arraydb[i] for i in range(start, end)]
