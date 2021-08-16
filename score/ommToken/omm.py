from iconservice import *

from .interfaces import TotalStaked, SupplyDetails
from .tokens.IRC2mintable import IRC2Mintable

TOKEN_NAME = 'OmmToken'
SYMBOL_NAME = 'OMM'


class AssetConfig(TypedDict):
    _id: int
    asset: Address
    distPercentage: int
    assetName: str
    rewardEntity: str


class RewardDistributionInterface(InterfaceScore):
    @interface
    def configureLPEmission(self, _assetConfig: List[AssetConfig]) -> None:
        pass


class OmmToken(IRC2Mintable):

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
