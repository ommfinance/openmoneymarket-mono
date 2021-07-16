from .utils.checks import *

class AddressDetails(TypedDict):
    name: str
    address: Address


# An interface to set address method
class AddressInterface(InterfaceScore):
    @interface
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        pass


class AddressProvider(IconScoreBase):
    USDs = "usds"
    sICX = "sICX"
    IUSDC = "iusdc"
    oICX = "oICX"
    oUSDs = "ousds"
    oIUSDC = "oiusdc"
    dICX = "dICX"
    dUSDs = "dusds"
    dIUSDC = "diusdc"
    LENDING_POOL = "lendingPool"
    LENDING_POOL_DATA_PROVIDER = "lendingPoolDataProvider"
    STAKING = "staking"
    DELEGATION = "delegation"
    OMM_TOKEN = "ommToken"
    REWARDS = "rewards"
    PRICE_ORACLE = "priceOracle"
    LENDING_POOL_CORE = "lendingPoolCore"
    LIQUIDATION_MANAGER = "liquidationManager"
    FEE_PROVIDER = "feeProvider"
    BRIDGE_OTOKEN = "bridgeOToken"
    GOVERNANCE = "governance"
    ADDRESS_PROVIDER = "addressProvider"
    RESERVE = "reserve"
    WORKER_TOKEN = "workerToken"
    DAO_FUND = "daoFund"


    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._addresses = DictDB("address", db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmAddressProvider"

    @only_owner
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for addressDetail in _addressDetails:
            self._addresses[addressDetail["name"]] = addressDetail["address"]

    @external(readonly=True)
    def getAddress(self, name: str) -> Address:
        return self._addresses[name]

    @external(readonly=True)
    def getReserveAddresses(self) -> dict:
        return {
            "USDS": self.getAddress(self.USDs),
            "sICX": self.getAddress(self.sICX),
            "IUSDC": self.getAddress(self.IUSDC),
        }

    @external(readonly=True)
    def getAllAddresses(self) -> dict:
        return {
            "collateral": {
                "USDS": self.getAddress(self.USDs),
                "sICX": self.getAddress(self.sICX),
                "IUSDC": self.getAddress(self.IUSDC),
            },
            "oTokens": {
                "oUSDS": self.getAddress(self.oUSDs),
                "oICX": self.getAddress(self.oICX),
                "oIUSDC": self.getAddress(self.oIUSDC),
            },
            "dTokens": {
                "dUSDS": self.getAddress(self.dUSDs),
                "dICX": self.getAddress(self.dICX),
                "dIUSDC": self.getAddress(self.dIUSDC),
            },
            "systemContract": {
                "LendingPool": self.getAddress(self.LENDING_POOL),
                "LendingPoolDataProvider": self.getAddress(self.LENDING_POOL_DATA_PROVIDER),
                "Staking": self.getAddress(self.STAKING),
                "Delegation": self.getAddress(self.DELEGATION),
                "OmmToken": self.getAddress(self.OMM_TOKEN),
                "Rewards": self.getAddress(self.REWARDS),
                "PriceOracle": self.getAddress(self.PRICE_ORACLE),
            }
        }

    @only_owner
    @external
    def setSCOREAddresses(self) -> None:
        self.setLendingPoolAddresses()
        self.setLendingPoolCoreAddresses()
        self.setLiquidationManagerAddresses()
        self.setOmmTokenAddresses()
        self.setoICXAddresses()
        self.setoUSDsAddresses()
        self.setoIUSDCAddresses()
        self.setDelegationAddresses()
        self.setRewardAddresses()
     

    @only_owner
    @external
    def setLendingPoolAddresses(self) -> None:
        lendingPoolAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL_CORE, "address": self._addresses[self.LENDING_POOL_CORE]},
            {"name": self.LIQUIDATION_MANAGER, "address": self._addresses[self.LIQUIDATION_MANAGER]},
            {"name": self.sICX, "address": self._addresses[self.sICX]},
            {"name": self.oICX, "address": self._addresses[self.oICX]},
            {"name": self.STAKING, "address": self._addresses[self.STAKING]},
            {"name": self.LENDING_POOL_DATA_PROVIDER, "address": self._addresses[self.LENDING_POOL_DATA_PROVIDER]},
            {"name": self.FEE_PROVIDER, "address": self._addresses[self.FEE_PROVIDER]},
            {"name": self.REWARDS, "address": self._addresses[self.REWARDS]},
            {"name": self.BRIDGE_OTOKEN, "address": self._addresses[self.BRIDGE_OTOKEN]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address},
            {"name": self.OMM_TOKEN, "address": self._addresses[self.OMM_TOKEN]}]

        lendingPool = self.create_interface_score(self._addresses[self.LENDING_POOL], AddressInterface)
        lendingPool.setAddresses(lendingPoolAddressDetails)

    @only_owner
    @external
    def setLendingPoolCoreAddresses(self) -> None:
        lendingPoolCoreAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL, "address": self._addresses[self.LENDING_POOL]},
            {"name": self.LIQUIDATION_MANAGER, "address": self._addresses[self.LIQUIDATION_MANAGER]},
            {"name": self.STAKING, "address": self._addresses[self.STAKING]},
            {"name": self.FEE_PROVIDER, "address": self._addresses[self.FEE_PROVIDER]},
            {"name": self.DELEGATION, "address": self._addresses[self.DELEGATION]},
            {"name": self.GOVERNANCE, "address": self._addresses[self.GOVERNANCE]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address},
            {"name": self.OMM_TOKEN, "address": self._addresses[self.OMM_TOKEN]}]

        lendingPoolCore = self.create_interface_score(self._addresses[self.LENDING_POOL_CORE], AddressInterface)
        lendingPoolCore.setAddresses(lendingPoolCoreAddressDetails)

    @only_owner
    @external
    def setLendingPoolCoreAddresses(self) -> None:
        lendingPoolCoreAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL, "address": self._addresses[self.LENDING_POOL]},
            {"name": self.LIQUIDATION_MANAGER, "address": self._addresses[self.LIQUIDATION_MANAGER]},
            {"name": self.STAKING, "address": self._addresses[self.STAKING]},
            {"name": self.FEE_PROVIDER, "address": self._addresses[self.FEE_PROVIDER]},
            {"name": self.DELEGATION, "address": self._addresses[self.DELEGATION]},
            {"name": self.GOVERNANCE, "address": self._addresses[self.GOVERNANCE]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address},
            {"name": self.OMM_TOKEN, "address": self._addresses[self.OMM_TOKEN]}
        ]

        lendingPoolCore = self.create_interface_score(self._addresses[self.LENDING_POOL_CORE], AddressInterface)
        lendingPoolCore.setAddresses(lendingPoolCoreAddressDetails)

    @only_owner
    @external
    def setLiquidationManagerAddresses(self) -> None:
        liquidationManagerAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL_DATA_PROVIDER, "address": self._addresses[self.LENDING_POOL_DATA_PROVIDER]},
            {"name": self.LENDING_POOL_CORE, "address": self._addresses[self.LENDING_POOL_CORE]},
            {"name": self.STAKING, "address": self._addresses[self.STAKING]},
            {"name": self.FEE_PROVIDER, "address": self._addresses[self.FEE_PROVIDER]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address},
            {"name": self.PRICE_ORACLE, "address": self._addresses[self.PRICE_ORACLE]}]

        liquidationManager = self.create_interface_score(self._addresses[self.LIQUIDATION_MANAGER], AddressInterface)
        liquidationManager.setAddresses(liquidationManagerAddressDetails)

    @only_owner
    @external
    def setOmmTokenAddresses(self) -> None:
        ommTokenAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL, "address": self._addresses[self.LENDING_POOL]},
            {"name": self.DELEGATION, "address": self._addresses[self.DELEGATION]},
            {"name": self.REWARDS, "address": self._addresses[self.REWARDS]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address}
        ]

        ommToken = self.create_interface_score(self._addresses[self.OMM_TOKEN], AddressInterface)
        ommToken.setAddresses(ommTokenAddressDetails)

    @only_owner
    @external
    def setoICXAddresses(self) -> None:
        oICXAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL_CORE, "address": self._addresses[self.LENDING_POOL_CORE]},
            {"name": self.LIQUIDATION_MANAGER, "address": self._addresses[self.LIQUIDATION_MANAGER]},
            {"name": self.RESERVE, "address": self._addresses[self.sICX]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address},
            {"name": self.LENDING_POOL_DATA_PROVIDER, "address": self.LENDING_POOL_DATA_PROVIDER},
            {"name": self.LENDING_POOL, "address": self.LENDING_POOL},
            {"name": self.REWARDS, "address": self.REWARDS}
        ]

        oICX = self.create_interface_score(self._addresses[self.oICX], AddressInterface)
        oICX.setAddresses(oICXAddressDetails)

    @only_owner
    @external
    def setoUSDsAddresses(self) -> None:
        oUSDsAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL_CORE, "address": self._addresses[self.LENDING_POOL_CORE]},
            {"name": self.LIQUIDATION_MANAGER, "address": self._addresses[self.LIQUIDATION_MANAGER]},
            {"name": self.RESERVE, "address": self._addresses[self.USDs]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address},
            {"name": self.LENDING_POOL_DATA_PROVIDER, "address": self.LENDING_POOL_DATA_PROVIDER},
            {"name": self.LENDING_POOL, "address": self.LENDING_POOL},
            {"name": self.REWARDS, "address": self.REWARDS}
        ]

        oUSDs = self.create_interface_score(self._addresses[self.oUSDs], AddressInterface)
        oUSDs.setAddresses(oUSDsAddressDetails)

    @only_owner
    @external
    def setoIUSDCAddresses(self) -> None:
        oIUSDCAddressDetails: List[AddressDetails] = [
            {"name": self.LENDING_POOL_CORE, "address": self._addresses[self.LENDING_POOL_CORE]},
            {"name": self.LIQUIDATION_MANAGER, "address": self._addresses[self.LIQUIDATION_MANAGER]},
            {"name": self.RESERVE, "address": self._addresses[self.IUSDC]},
            {"name": self.ADDRESS_PROVIDER, "address": self.address},
            {"name": self.LENDING_POOL_DATA_PROVIDER, "address": self.LENDING_POOL_DATA_PROVIDER},
            {"name": self.LENDING_POOL, "address": self.LENDING_POOL},
            {"name": self.REWARDS, "address": self.REWARDS}
        ]

        oIUSDC = self.create_interface_score(self._addresses[self.oIUSDC], AddressInterface)
        oIUSDC.setAddresses(oIUSDCAddressDetails)

    @only_owner
    @external  
    def setDelegationAddresses(self) -> None:
        delegationAddressDetails: AddressDetails = [{"name": self.LENDING_POOL_CORE, "address": self._addresses[self.LENDING_POOL_CORE]},
                                                {"name": self.OMM_TOKEN, "address": self._addresses[self.OMM_TOKEN]},
                                                {"name": self.ADDRESS_PROVIDER, "address": self.address},
                                                ]

        delegation = self.create_interface_score(self._addresses[self.DELEGATION], AddressInterface)
        delegation.setAddresses(daoFundAddressDetails)

    @only_owner
    @external  
    def setRewardAddresses(self) -> None:
        rewardAddressDetails: AddressDetails = [{"name": self.LENDING_POOL_DATA_PROVIDER, "address": self._addresses[self.LENDING_POOL_DATA_PROVIDER]},
                                                {"name": self.OMM_TOKEN, "address": self._addresses[self.OMM_TOKEN]},
                                                {"name": self.WORKER_TOKEN, "address": self._addresses[self.WORKER_TOKEN]},
                                                {"name": self.DAO_FUND, "address": self._addresses[self.DAO_FUND]},



                                                
                                                ]

        reward = self.create_interface_score(self._addresses[self.REWARD], AddressInterface)
        reward.setAddresses(rewardAddressDetails)
    

   


   






        

        
