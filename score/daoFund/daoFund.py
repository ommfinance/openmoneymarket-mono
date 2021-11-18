from .utils.checks import *
from .addresses import *

TAG = 'Dao Fund Manager'


# This contract manages the fund for Dao operations

class DaoFund(Addresses):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=1)
    def FundReceived(self, _amount: int, _reserve: Address):
        pass

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

    @only_governance
    @external
    def transferOmm(self, _value: int, _address: Address):
        omm = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        omm.transfer(_address, _value)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes = None) -> None:
        self.FundReceived(_value, self.msg.sender)

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
