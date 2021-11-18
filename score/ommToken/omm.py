from iconservice import *

from .interfaces import TotalStaked, SupplyDetails
from .tokens.IRC2mintable import IRC2Mintable
from .tokens.IRC2burnable import IRC2Burnable

TOKEN_NAME = 'Omm Token'
SYMBOL_NAME = 'OMM'


class AssetConfig(TypedDict):
    _id: int
    asset: Address
    distPercentage: int
    assetName: str
    rewardEntity: str


class OmmToken(IRC2Mintable, IRC2Burnable):

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider, TOKEN_NAME, SYMBOL_NAME)

    @external(readonly=True)
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        return {
            "decimals": self.decimals(),
            "principalUserBalance": self.staked_balanceOf(_user),
            "principalTotalSupply": self.total_staked_balance()
        }

    @external(readonly=True)
    def getTotalStaked(self) -> TotalStaked:
        """
        return total staked balance for reward distribution
        :return: total staked balance and its precision
        """
        return {
            "decimals": self.decimals(),
            "totalStaked": self.total_staked_balance()
        }

    @external(readonly=True)
    def stakedBalanceOfAt(self, _owner: Address, _timestamp: int) -> int:
        if not self._is_snapshot_exists(_owner) and _timestamp >= self._snapshot_started_at.get():
            return self.staked_balanceOf(_owner)
        return super().stakedBalanceOfAt(_owner, _timestamp)
