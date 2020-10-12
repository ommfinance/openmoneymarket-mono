from iconservice import *

TAG = 'LendingPoolConfigurator'


class LendingPoolConfigurator(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def initReserve(self, _reserve: Address, _underlyingAssetDecimals: int):
        """
        initializes a reserve
        :param _reserve:the address of reserve to be initialized
        :param _underlyingAssetDecimals:the decimals of the reserve underlying asset
        :return:
        """

    @external
    def initReserveWithData(self, _reserve: Address, _underlyingAssetDecimals: int, _oTokenName: str,
                            _oTokenSymbol: str):
        """
        initializes a reserve using aTokenData provided externally (useful if the underlying ERC20 contract doesn't expose name or decimals)
        :param _reserve: the address of reserve to be initialized
        :param _underlyingAssetDecimals: the decimals of the reserve underlying asset
        :param _oTokenName: the name of  oToken
        :param _oTokenSymbol:the symbol of oToken
        :return:
        """

    @external
    def removeLastAddedReserve(self, _reserveToRemove: Address):
        """
        removes the last added reserve
        :param _reserveToRemove: the address of the reserve to remove
        :return:
        """

    @external
    def enableBorrowingOnReserve(self, _reserve: Address):
        """
        enables the borrow from _reserve
        :param _reserve:address of the reserve
        :return:
        """

    @external
    def disableBorrowingOnReserve(self, _reserve: Address):
        """
        disables the borrow from _reserve
        :param _reserve:address of the reserve
        :return:
        """

    @external
    def enableReserveAsCollateral(self, _reserve: Address, _baseLTVasCollateral: int, _liquidationThreshold: int,
                                  _liquidationBonus: int):
        """
        enables borrow from a reserve
        :param _reserve:address of the reserve
        :param _baseLTVasCollateral:the loan to value of asset when used as collateral
        :param _liquidationThreshold:the threshold at which loans using this asset as collateral will be considered undercollateralized
        :param _liquidationBonus:the bonus liquidators receive to liquidate the asset
        :return:
        """

    @external
    def disableReserveAsCollateral(self, _reserve: Address):
        """
        disables borrow from a reserve
        :param _reserve: address of the reserve
        :return:
        """

    @external
    def activateReserve(self, _reserve: Address):
        """
        activates a reserve
        :param _reserve:address of the reserve
        :return:
        """

    @external
    def deactiveReserve(self, _reserve: Address):
        """
        deactivates a reserve
        :param _reserve:address of the reserve
        :return:
        """

    @external
    def freezeReserve(self, _reserve: Address):
        """
        freezes a reserve
        :param _reserve: address of the reserve
        :return:
        """

    @external
    def unfreezeReserve(self, _reserve: Address):
        """
        unfreezes a reserve
        :param _reserve: address of the reserve
        :return:
        """

    @external
    def setReserveBaseLTVasCollateral(self, _reserve: Address, _ltv: int):
        """
        sets/updates  the loan to value of a reserve
        :param _reserve:address of the reserve
        :param _ltv:the value of ltv to set
        :return:
        """

    @external
    def setReserveLiquidationThreshold(self, _reserve: Address, _threshold: int):
        """
        updates the liquidation threshold of the reserve
        :param _reserve:address of the reserve
        :param _threshold:the value liquidation threshold to set
        :return:
        """

    @external
    def setReserveLiquidationBonus(self, _reserve: Address, _bonus: int):
        """
        updates the liquidation bonus of the reserve
        :param _reserve: address of the reserve
        :param _bonus: the value for liquidation bonus
        :return:
        """

    @external
    def setReserveDecimals(self, _reserve: Address, _decimals: int):
        """
        updates the reserve decimals
        :param _reserve:address of the reserve
        :param _decimals:the new number of  decimals
        :return:
        """

    @external
    def refreshLendingPoolCoreConfiguration(self):
        """
        refreshes the lending pool core configuration to update the cached address
        :return:
        """
