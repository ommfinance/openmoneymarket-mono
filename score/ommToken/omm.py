from .tokens.IRC2mintable import IRC2Mintable
from iconservice import *

from .utils.checks import only_owner

TOKEN_NAME = 'OmmToken'
SYMBOL_NAME = 'OMM'


class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int


class AssetConfig(TypedDict):
    _id: int
    asset: Address
    distPercentage: int
    assetName: str
    mapping: str


class RewardDistributionInterface(InterfaceScore):
    @interface
    def configureLPEmission(self, _assetConfig: List[AssetConfig]) -> None:
        pass


class OmmToken(IRC2Mintable):

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)

    @external(readonly=True)
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        return {
            "principalUserBalance": self.staked_balanceOf(_user),
            "principalTotalSupply": self.total_staked_balance()
        }

    @external(readonly=True)
    def getTotalStaked(self) -> int:
        """
        return total staked balance for reward distribution
        :return: total staked balance
        """
        return self.total_staked_balance()

    @only_owner
    @external
    def addPool(self, _distPercentage: int, assetName: str = "OMM") -> None:
        reward = self.create_interface_score(self._addresses["rewards"], RewardDistributionInterface)
        _config = {
            "_id": -1,
            "asset": self.address,
            "distPercentage": _distPercentage,
            "assetName": assetName,
            "mapping": "liquidityProvider",
        }
        reward.configureLPEmission([_config])
