from iconservice import *
from .utils.checks import *

TAG = 'SuperAddressProvider'


class Environments(TypedDict):
    addressProvider: Address
    envName: str
    pklName: str


class SuperAddressProvider(IconScoreBase):
    ENVIRONMENTS = 'envs'
    ID = 'id'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._env = DictDB(self.ENVIRONMENTS, db, value_type=str, depth=2)
        self._id = ArrayDB(self.ID, db, value_type=str)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmSuperAddressProvider"

    @only_owner
    @external
    def addEnv(self, _env: Environments) -> None:
        new_id = str(len(self._id) + 1)
        self._id.put(new_id)
        self._env[new_id]['addProv'] = str(_env['addressProvider'])
        self._env[new_id]['name'] = _env['envName']
        self._env[new_id]['pkl'] = _env['pklName']

    @external(readonly=True)
    def getIdList(self) -> list:
        return [item for item in self._id]

    @external(readonly=True)
    def getEnv(self) -> dict:
        response = {}
        _id_list = self.getIdList()
        for item in _id_list:
            _id = str(item)
            response[_id] = {
                'addressProvider': self._env[_id]['addProv'],
                'environmentName': self._env[_id]['name'],
                'pklFileName': self._env[_id]['pkl']
            }
        return response
