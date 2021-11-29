from .utils.checks import *
from .utils.math import *
from .addresses import *
from .FeeBurnData import *

TAG = 'Fee Provider'
FEE_BURN_DB_PREFIX = b'feeBurnData'


class FeeProvider(Addresses):
    ORIGINATION_FEE_PERCENT = 'originationFeePercent'
    TOTAL_OMM_BURNT = 'totalOmmBurnt'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._originationFeePercent = VarDB(self.ORIGINATION_FEE_PERCENT, db, value_type=int)
        self.feeBurnData = FeeBurnDataDB(db)
        self._totalOmmBurnt = VarDB(self.TOTAL_OMM_BURNT, db, value_type=int)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def FeeReceived(self, _from: Address, _value: int, _data: bytes, _sender: Address):
        pass

    @eventlog(indexed=3)
    def FeeBurned(self, _reserve: Address, omm_received: int, _amount_to_burn: int, _amount_to_dao_fund: int):
        pass    

    @only_owner
    @external
    def setLoanOriginationFeePercentage(self, _percentage: int) -> None:
        self._originationFeePercent.set(_percentage)

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

    @external(readonly=True)
    def calculateOriginationFee(self, _amount: int) -> int:
        return exaMul(_amount, self.getLoanOriginationFeePercentage())

    @external(readonly=True)
    def getLoanOriginationFeePercentage(self) -> int:
        return self._originationFeePercent.get()

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        self.FeeReceived(_from, _value, _data, self.msg.sender)

    @only_governance
    @external
    def transferFund(self, _token: Address, _value: int, _to: Address):
        token = self.create_interface_score(_token, TokenInterface)
        token.transfer(_to, _value)

    @external
    @only_governance
    def updateDaoFundPercentage(self, _reserve: Address, _daoFundPercentage: int):
        self._require(self.is_reserve_valid(_reserve), "Invalid reserve")
        prefix = self.feeBurnDataPrefix(_reserve)
        self._require(0 <= _daoFundPercentage <= EXA,
                      "Percentage to DAO fund should be between 0 and 100%")

        self.feeBurnData[prefix].daoFundPercentage.set(_daoFundPercentage)

    @external
    @only_governance
    def updateBlockHeightLimit(self, _reserve: Address, _blockHeightLimit: int):
        self._require(self.is_reserve_valid(_reserve), "Invalid reserve")
        prefix = self.feeBurnDataPrefix(_reserve)
        self._require(_blockHeightLimit > 0,
                      f"Block Height Limit should be greater than zero")
        self.feeBurnData[prefix].blockHeightLimit.set(_blockHeightLimit)

    @external
    @only_governance
    def updateRoute(self, _reserve: Address, _route: List[Address]):
        self._require(self.is_reserve_valid(_reserve), "Invalid reserve")
        prefix = self.feeBurnDataPrefix(_reserve)

        self._require(_route[-1] == self._addresses[OMM_TOKEN], 'Last address in route must be OMM Token.')

        route = json_dumps([str(address) for address in _route])
        self.feeBurnData[prefix].route.set(route)

    @external
    @only_governance
    def updateIsActive(self, _reserve: Address, _isActive: bool):
        self._require(self.is_reserve_valid(_reserve), "Invalid reserve")
        prefix = self.feeBurnDataPrefix(_reserve)
        self.feeBurnData[prefix].isActive.set(_isActive)

    @external
    @only_governance
    def updateTotalAmount(self, _reserve: Address, _totalAmount: int):
        self._require(self.is_reserve_valid(_reserve), "Invalid reserve")
        prefix = self.feeBurnDataPrefix(_reserve)
        self._require(_totalAmount > 0, "Total amount should be greater than zero")
        self.feeBurnData[prefix].totalAmount.set(_totalAmount)

    @external(readonly=True)
    def getFeeBurnData(self, _reserve: Address) -> dict:
        if self.is_reserve_valid(_reserve):
            prefix = self.feeBurnDataPrefix(_reserve)
            response = getFeeBurnData(prefix, self.feeBurnData)
            return response
        else:
            return {}

    @external(readonly=True)
    def getTotalOmmBurnt(self) -> int:
        """
        Returns total amount of OMM Tokens burnt using fees from fee provider
        """
        return self._totalOmmBurnt.get()

    @external
    @only_governance
    def addFeeBurnData(self, _reserve: FeeBurnDataAttributes):
        fee_object = createFeeBurnDataObject(_reserve)

        _reserveAddress = fee_object.reserveAddress
        _daoFundPercentage = fee_object.daoFundPercentage

        self._require(0 <= _daoFundPercentage <= EXA,
                      "Percent to DAO Fund should be between 0 and 100%")
        self._require(fee_object.totalAmount > 0,
                      "Max amount should be greater than zero")
        self._require(fee_object.blockHeightLimit > 0,
                      "Block Height Limit should be greater than zero")

        try:
            route = json_loads(fee_object.route)
        except Exception as e:
            revert(f"Invalid route: {fee_object.route}")

        self._require(Address.from_string(
            route[-1]) == self._addresses[OMM_TOKEN], f'Last address in route must be OMM Token.')

        prefix = self.feeBurnDataPrefix(_reserveAddress)
        addReserveFeeBurnData(prefix, self.feeBurnData, fee_object)

    @external
    @only_governance
    def burnFee(self, _reserve: Address):
        self._burnFee(_reserve)

    def _burnFee(self, _reserve: Address):
        self._require(self.is_reserve_valid(_reserve), f"Invalid reserve: {_reserve}")

        fee_burn_data = self.getFeeBurnData(_reserve)
        totalAmount = fee_burn_data.get('totalAmount')

        self._require(fee_burn_data.get('isActive'),
                      "Reserve not active for fee burning")
        self._require(self.block_height - fee_burn_data.get('lastBurnBlockHeight') >=
                      fee_burn_data.get('blockHeightLimit'),
                      f"Burned recently. Try again after sometime.")

        omm_addr = self._addresses[OMM_TOKEN]
        router_addr = self._addresses[ROUTER]

        omm = self.create_interface_score(omm_addr, OMMInterface)
        reserve = self.create_interface_score(_reserve, TokenInterface)
        reserve_balance = reserve.balanceOf(self.address)

        total_amount = min(reserve_balance, totalAmount)
        self._require(total_amount > 0,
                      f"Out of balance for this reserve: {_reserve}")

        dao_fund_percentage = fee_burn_data.get('daoFundPercentage')
        amount_to_dao_fund = exaMul(dao_fund_percentage, total_amount)
        amount_to_burn = total_amount - amount_to_dao_fund

        if _reserve == omm_addr:
            omm_received = amount_to_burn
        else:
            try:
                route = json_loads(fee_burn_data.get('route'))
            except Exception as e:
                revert(f"{TAG}:Invalid route: {fee_burn_data.get('route')}")

            data = json_dumps({
                'method': '_swap',
                'params': {
                    'toToken': str(omm_addr),
                    'path': route
                }
            }).encode('utf-8')

            omm_before = omm.balanceOf(self.address)

            # swap using balanced router
            reserve.transfer(router_addr, amount_to_burn, data)
            omm_after = omm.balanceOf(self.address)
            omm_received = omm_after - omm_before

        # burn all recieved OMM from the swap
        omm.burn(omm_received)
        # send to dao fund
        reserve.transfer(
            self._addresses[DAO_FUND], amount_to_dao_fund, b'From fee provider')

        self._totalOmmBurnt.set(omm_received+self._totalOmmBurnt.get())

        total_amount_swapped = fee_burn_data.get('totalAmountSwapped') + amount_to_burn
        total_omm_burnt = fee_burn_data.get('totalOMMBurnt') + omm_received
        total_amount_to_dao_fund = fee_burn_data.get('totalAmountToDaoFund') + amount_to_dao_fund
        self._update_after_omm_burn(_reserve, total_amount_swapped, total_omm_burnt, total_amount_to_dao_fund)

        self.FeeBurned(_reserve, omm_received,
                       amount_to_burn, amount_to_dao_fund)

    def _update_after_omm_burn(self, _reserve: Address, _total_amount_swapped: int, _total_omm_burnt: int, _amount_to_dao_fund: int):
        prefix = self.feeBurnDataPrefix(_reserve)
        self.feeBurnData[prefix].lastBurnBlockHeight.set(self.block_height)
        self.feeBurnData[prefix].totalOMMBurnt.set(_total_omm_burnt)
        self.feeBurnData[prefix].totalAmountSwapped.set(_total_amount_swapped)
        self.feeBurnData[prefix].totalAmountToDaoFund.set(_amount_to_dao_fund)

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(f'{TAG}: {_message}')

    def feeBurnDataPrefix(self, _reserve: Address) -> bytes:
        return b'|'.join([FEE_BURN_DB_PREFIX, str(_reserve).encode()])

    def is_reserve_valid(self, _reserve: Address) -> bool:
        core = self.create_interface_score(
            self._addresses[LENDING_POOL_CORE], CoreInterface)
        reserve_addresses = core.getReserves()
        return _reserve in reserve_addresses
