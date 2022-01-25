from iconservice import *


class AddressDetails(TypedDict):
    name: str
    address: Address


class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


class PrepICXDelegations(TypedDict):
    _address: Address
    _votes_in_per: int
    _votes_in_icx: int


class TotalStaked(TypedDict):
    decimals: int
    totalStaked: int


class SystemInterface(InterfaceScore):
    @interface
    def getPRep(self, address: Address) -> dict:
        pass


class OmmTokenInterface(InterfaceScore):
    @interface
    def details_balanceOf(self, _owner: Address) -> dict:
        pass


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def updatePrepDelegations(self, _delegations: List[PrepDelegations]):
        pass


class GovernanceContractInterface(InterfaceScore):
    @interface
    def getPRep(self, address: Address) -> dict:
        pass
