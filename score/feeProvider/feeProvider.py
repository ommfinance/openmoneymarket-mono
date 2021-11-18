from .utils.checks import *
from .utils.math import *
from .addresses import *

TAG = 'Fee Provider'


class FeeProvider(Addresses):
    ORIGINATION_FEE_PERCENT = 'originationFeePercent'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._originationFeePercent = VarDB(self.ORIGINATION_FEE_PERCENT, db, value_type=int)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def FeeReceived(self, _from: Address, _value: int, _data: bytes,_sender:Address):
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
        self.FeeReceived(_from, _value, _data,self.msg.sender)

    @only_governance
    @external
    def transferFund(self, _token: Address, _value: int, _to: Address):
        token = self.create_interface_score(_token, TokenInterface)
        token.transfer(_to, _value)

    @external(readonly=True)
    def getReserveBalances(self):
        """
        Returns balance of all the supported reserves for this contract
        """
        address_provider = self.create_interface_score(
            self._addressProvider.get(), AddressProviderInterface)
        reserve_address = address_provider.getReserveAddresses()
        balances = {}
        for name, address in reserve_address.items():
            reserve = self.create_interface_score(address, TokenInterface)
            balances[name] = reserve.balanceOf(self.address)
        return balances

    @external(readonly=True)
    def getReserveBalance(self, _reserve: Address):
        """
        Return balance of specific reserve for this contract

        :param _reserve: Address of reserve of which balance is to be queried
        """
        reserve = self.create_interface_score(_reserve, TokenInterface)
        return reserve.balanceOf(self.address)