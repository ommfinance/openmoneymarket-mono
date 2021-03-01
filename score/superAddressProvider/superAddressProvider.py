from iconservice import *
from .utils.checks import *
TAG = 'SuperAddressProvider'

class Environments(TypedDict):
    addressProvider : Address
    envName : str
    pklName : str




class SuperAddressProvider(IconScoreBase):
    ENVIRONMENTS = 'envs'
    ID = 'id'


    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._env = DictDB(self.ENVIRONMENTS, db, value_type=str,depth=2)
        self._id = ArrayDB(self.ID, db, value_type=str)
        


    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @only_owner
    @external
    def addEnv(self, _env: Environments) -> None:
        newId = str(len(self.getIdList()) + 1 )
        self._id.put(newId)
        self._env[newId]['addProv'] = str(_env ['addressProvider'])
        self._env[newId]['name'] = _env ['envName']
        self._env[newId]['pkl'] = _env['pklName']

    
    @external
    def getIdList(self) -> list:
        return [item for item in self._id]


    @external(readonly=True)
    def getEnv(self) -> dict:
        response = {}
        idList = self.getIdList()
        for item in idList:
            ID = str(item)
            envDetails = {
                    'addressProvider':self._env[ID]['addProv'],
                    'environmentName':self._env[ID]['name'],
                    'pklFileName':self._env[ID]['pkl']
                    }
            response[ID] = envDetails

        return response
