from iconsdk.wallet.wallet import KeyWallet
from .test_integrate_omm_utils import OmmUtils
from ..actions.steps import Steps
from pprint import pprint
from ..actions.delegations import ACTIONS as DELEGATIONS

EXA = 10 ** 18

class OMMDelegationTest(OmmUtils):
    def setUp(self):
        super().setUp()

    def test_01_update_delegations(self):
        self._execute(DELEGATIONS)

    def initialize_user(self, name: str):
        self.users = {
            "admin": self.deployer_wallet
        }
        user = KeyWallet.create()
        self.send_icx(self.deployer_wallet, user.get_address(), 50 * EXA)
        self._mint_omm(user.get_address())
        self.users[name] = user

    def _mint_omm(self, addr):
        self.send_tx(
                from_=self.deployer_wallet,
                to=self.contracts['ommToken'],
                method="mintTo",
                params={"_to": addr, "_amount": 1000 * EXA}
            )

    def _execute(self, task):
        print("\n", task.get("description"))
        
        self.delegations = {
            "before": {},
            "after": {}
        }

        self.initialize_user("user1")
        for case in task.get("transaction"):
            _step = case.get("_step")
            self.user = case.get("user")
            self._user = self.users.get(self.user)
            _addr = self._user.get_address()
            _delegation = case.get('_delegations')
            _amount = case.get("amount")

            print(f"#################################{_step} by {self.user}####################################")


            if _step == Steps.STAKE_OMM:
                tx_res = self._stakeOMM(self._user, _amount)
                self._check_tx_result(tx_res, case)
                self._set_delegation_data("after",  _addr)
                self._check_default_delegations()

            elif _step == Steps.UPDATE_DELEGATIONS:
                self._set_delegation_data("before", _addr)
                tx_res = self._updateDelegations(self._user, _delegation)
                self._check_tx_result(tx_res, case)
                self._set_delegation_data("after", _addr)
                for i in range(len(_delegation)):
                    _delegation[i]['_votes_in_per'] = hex(int(_delegation[i]['_votes_in_per']))
                self.assertEqual(self.delegations['after'], _delegation)

            elif _step == Steps.CLEAR_DELEGATIONS:
                tx_res = self._clearDelegations(self._user)
                self._check_tx_result(tx_res, case)
                self._set_delegation_data("after", _addr)
                self._check_default_delegations()                

    def _set_delegation_data(self, key, address):
        self.delegations[key] = self.call_tx(
                to=self.contracts['delegation'],
                method="getUserDelegationDetails",
                params={'_user': address}
            )

    def _check_tx_result(self, tx_result, case):
        if (tx_result['status'] == 0): 
            print("SCORE MESSAGE: ", tx_result['failure']['message'])
            if case.get('revertMessage') != None:
                print("EXPECTED MESSAGE: ", case['revertMessage'])

        self.assertEqual(tx_result['status'], case['expectedResult'])

    def _clearDelegations(self, _from):
        return self.send_tx(
                from_=_from,
                to=self.contracts['delegation'],
                method="clearPrevious",
                params={'_user': _from.get_address()}
            )

    def _updateDelegations(self, _from, _delegation):
        return self.send_tx(
                from_=_from,
                to=self.contracts['delegation'],
                method="updateDelegations",
                params={'_delegations': _delegation, '_user': None}
            )

    def _check_default_delegations(self):
        default = [
            {
                "_address": "hxec79e9c1c882632688f8c8f9a07832bcabe8be8f",
                "_votes_in_per": "0x3782dace9d90000"
            },
            {
                "_address": "hxd3be921dfe193cd49ed7494a53743044e3376cd3",
                "_votes_in_per": "0x3782dace9d90000"
            },
            {
                "_address": "hx9e7509f86ea3ba5c139161d6e92a3982659e9f30",
                "_votes_in_per": "0x3782dace9d90000"
            },
            {
                "_address": "hxaad52424d4aec9dac7d9f6796da527f471269d2c",
                "_votes_in_per": "0x3782dace9d90000"
            }
        ]

        self.assertEqual(default, self.delegations['after'])