from iconservice import *

class FeeBurnDataAttributes(TypedDict):
    reserveName: str
    reserveAddress: Address
    totalAmount: int
    daoFundPercentage: int
    lastBurnBlockHeight: int
    blockHeightLimit: int
    route: str
    isActive: bool
    totalOMMBought: int
    totalAmountSwapped: int
    totalAmountToDaoFund: int

class FeeBurnData(object):

    def __init__(self, db: IconScoreDatabase) -> None:
        self.reserveName = VarDB('reserveName', db, str)
        self.reserveAddress = VarDB('reserveAddress', db, Address)
        self.totalAmount = VarDB('totalAmount', db, int)
        self.daoFundPercentage = VarDB('daoFundPercentage', db, int)
        self.lastBurnBlockHeight = VarDB('lastBurnBlockHeight', db, int)
        self.blockHeightLimit = VarDB('blockHeightLimit', db, int)
        self.route = VarDB('route', db, str)
        self.isActive = VarDB('isActive', db, bool)
        self.totalOMMBought = VarDB('totalOMMBought', db, int)
        self.totalAmountSwapped = VarDB('totalAmountSwapped', db, int)
        self.totalAmountToDaoFund = VarDB('totalAmountToDaoFund', db, int)


class FeeBurnDataDB:

    def __init__(self, db: IconScoreDatabase):
        self._db = db
        self._items = {}

    def __getitem__(self, prefix: bytes) -> FeeBurnData:
        if prefix not in self._items:
            sub_db = self._db.get_sub_db(prefix)
            self._items[prefix] = FeeBurnData(sub_db)

        return self._items[prefix]

    def __setitem__(self, key, value):
        revert('illegal access')


def addReserveFeeBurnData(prefix: bytes, _fee: 'FeeBurnDataDB', feeData: 'FeeBurnDataObject'):
    _fee[prefix].reserveName.set(feeData.reserveName)
    _fee[prefix].reserveAddress.set(feeData.reserveAddress)
    _fee[prefix].totalAmount.set(feeData.totalAmount)
    _fee[prefix].daoFundPercentage.set(feeData.daoFundPercentage)
    _fee[prefix].lastBurnBlockHeight.set(feeData.lastBurnBlockHeight)
    _fee[prefix].blockHeightLimit.set(feeData.blockHeightLimit)
    _fee[prefix].route.set(feeData.route)
    _fee[prefix].isActive.set(feeData.isActive)
    _fee[prefix].totalOMMBought.set(feeData.totalOMMBought)
    _fee[prefix].totalAmountSwapped.set(feeData.totalAmountSwapped)
    _fee[prefix].totalAmountToDaoFund.set(feeData.totalAmountToDaoFund)

def getFeeBurnData(prefix: bytes, _fee: 'FeeBurnDataDB') -> dict:
    reserveName = _fee[prefix].reserveName.get()
    reserveAddress = _fee[prefix].reserveAddress.get()
    totalAmount = _fee[prefix].totalAmount.get()
    daoFundPercentage = _fee[prefix].daoFundPercentage.get()
    lastBurnBlockHeight = _fee[prefix].lastBurnBlockHeight.get()
    blockHeightLimit = _fee[prefix].blockHeightLimit.get()
    route = _fee[prefix].route.get()
    isActive = _fee[prefix].isActive.get()
    totalOMMBought = _fee[prefix].totalOMMBought.get()
    totalAmountSwapped = _fee[prefix].totalAmountSwapped.get()
    totalAmountToDaoFund = _fee[prefix].totalAmountToDaoFund.get()
    return {
        'reserveName': reserveName,
        'reserveAddress': reserveAddress,
        'totalAmount': totalAmount,
        'daoFundPercentage': daoFundPercentage,
        'lastBurnBlockHeight': lastBurnBlockHeight,
        'blockHeightLimit': blockHeightLimit,
        'route': route,
        'isActive': isActive,
        'totalOMMBought': totalOMMBought,
        'totalAmountSwapped': totalAmountSwapped,
        'totalAmountToDaoFund': totalAmountToDaoFund
    }


def createFeeBurnDataObject(feeBurnData: 'FeeBurnDataAttributes') -> 'FeeBurnDataObject':
    return FeeBurnDataObject(
        reserveName=feeBurnData['reserveName'],
        reserveAddress=feeBurnData['reserveAddress'],
        totalAmount=feeBurnData['totalAmount'],
        daoFundPercentage=feeBurnData['daoFundPercentage'],
        lastBurnBlockHeight=feeBurnData['lastBurnBlockHeight'],
        blockHeightLimit=feeBurnData['blockHeightLimit'],
        route=feeBurnData['route'],
        isActive=feeBurnData['isActive'],
        totalOMMBought=feeBurnData['totalOMMBought'],
        totalAmountSwapped=feeBurnData['totalAmountSwapped'],
        totalAmountToDaoFund=feeBurnData['totalAmountToDaoFund']
    )


class FeeBurnDataObject(object):

    def __init__(self, **kwargs) -> None:
        self.reserveName = kwargs.get('reserveName')
        self.reserveAddress = kwargs.get('reserveAddress')
        self.totalAmount = kwargs.get('totalAmount')
        self.daoFundPercentage = kwargs.get('daoFundPercentage')
        self.lastBurnBlockHeight = kwargs.get('lastBurnBlockHeight')
        self.blockHeightLimit = kwargs.get('blockHeightLimit')
        self.route = kwargs.get('route')
        self.isActive = kwargs.get('isActive')
        self.totalOMMBought = kwargs.get('totalOMMBought')
        self.totalAmountSwapped = kwargs.get('totalAmountSwapped')
        self.totalAmountToDaoFund = kwargs.get('totalAmountToDaoFund')
