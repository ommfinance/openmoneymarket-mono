from iconsdk.wallet.wallet import KeyWallet
from .test_integrate_omm_utils import OmmUtils
from ..actions.steps import Steps
from ..actions.lp_staking_cases import ACTIONS as LP_STAKING_CASE
    
EXA = 10 ** 18
ID = 2

class OMMLPStakingCases(OmmUtils):
    def setUp(self):
        super().setUp()

    def test_01_staking_cases(self):
        self._execute(LP_STAKING_CASE)

    def initialize_user(self, name: str):
        self.users = {
            "admin": self.deployer_wallet
        }
        user = KeyWallet.create()
        self.send_icx(self.deployer_wallet, user.get_address(), 50 * EXA)
        self._mintLpTokens(self.deployer_wallet, user.get_address(), ID)
        
        self.users[name] = user

    def _execute(self, task):
        print("\n", task.get("description"))
        self.balance = {
            "before": {
                "user1": {},
                "stakedLp":{}
            },
            "after": {
                "user1": {},
                "stakedLp": {}
            }
        }

        self.initialize_user("user1")
        for case in task.get("transaction"):
            _step = case.get("_step")
            self.user = case.get("user")
            self._user = self.users.get(self.user)
            self._amount = case.get("amount")
            _success = case.get("expectedResult")
            print(f"#################################{_step} by {self.user}####################################")
            
            if _step == Steps.STAKE_LP:
                self._set_balances("before")
                tx_res = self._stakeLp(self._user, self._amount, ID)
                self._check_tx_result(tx_res, case)

            elif _step == Steps.UNSTAKE_LP:  
                self._set_balances("before")
                tx_res = self._unstakeLp(self._user, self._amount, ID)
                self._check_tx_result(tx_res, case)
                self._unstake_test(_success)     

    def _check_tx_result(self, tx_result, case):
        if (tx_result['status'] == 0): 
            print("SCORE MESSAGE: ", tx_result['failure']['message'])
            if case.get('revertMessage') != None:
                print("EXPECTED MESSAGE: ", case['revertMessage'])

        self.assertEqual(tx_result['status'], case['expectedResult'])
        self._set_balances("after")

    def _set_balances(self, key: str):
        self.balance[key]["user1"]["icx"] = self.get_balance(self._user.get_address())
        self.balance[key]["user1"]["lpToken"] = self._lp_balance(self._user.get_address()) 
        self.balance[key]["stakedLp"]["lpToken"] = self._lp_balance(self.contracts["stakedLp"])

    def _lp_balance(self, _usr):
        lp_balance = self.call_tx(
                to = self.contracts['lpToken'],
                method = "balanceOf",
                params = {'_owner': _usr, '_id': ID}
            )
        return int(lp_balance,0)

   
    def _stake_test(self, _success: int):
        lp_before_user = self.balance["before"]["user1"]["lpToken"] 
        lp_after_user = self.balance["after"]["user1"]["lpToken"] 
        lp_before_contract = self.balance["before"]["stakedLp"]["lpToken"]
        lp_after_contract = self.balance["after"]["stakedLp"]["lpToken"]

        if _success == 1:
            self.assertEqual(lp_before_user, lp_after_user + self._amount)
            self.assertEqual(lp_before_contract, lp_after_contract - self._amount)

    def _unstake_test(self, _success: int):
        lp_before_user = self.balance["before"]["user1"]["lpToken"] 
        lp_after_user = self.balance["after"]["user1"]["lpToken"] 
        lp_before_contract = self.balance["before"]["stakedLp"]["lpToken"]
        lp_after_contract = self.balance["after"]["stakedLp"]["lpToken"]

        if _success == 1:
            self.assertEqual(lp_before_user, lp_after_user - self._amount)
            self.assertEqual(lp_before_contract, lp_after_contract + self._amount)