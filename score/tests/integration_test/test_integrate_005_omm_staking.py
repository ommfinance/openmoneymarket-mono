from iconsdk.wallet.wallet import KeyWallet
from .test_integrate_omm_utils import OmmUtils
from ..actions.steps import Steps
from ..actions.omm_staking_cases import ACTIONS as OMM_STAKING_CASE
    
EXA = 10 ** 18

class OMMStakingCases(OmmUtils):
    def setUp(self):
        super().setUp()

    def test_01_omm_staking_cases(self):
        self._execute(OMM_STAKING_CASE)

    def initialize_user(self, name: str):
        self.users = {
            "admin": self.deployer_wallet
        }
        user = KeyWallet.create()
        self.send_icx(self.deployer_wallet, user.get_address(), 1500 * EXA)
        self._transferUSDS(self.deployer_wallet, user.get_address(), 1500 * EXA)        
        self.users[name] = user

    def _execute(self, task):
        print("\n", task.get("description"))
        self.balance = {
            "before": {
                "user1": {},
                "ommToken":{}
            },
            "after": {
                "user1": {},
                "ommToken": {}
            }
        }

        self.initialize_user("user1")
        self.send_tx(
                from_=self.deployer_wallet,
                to=self.contracts['ommToken'],
                method="mintTo",
                params={"_to": self.users["user1"].get_address(), "_amount": 1000 * EXA}
            )
        for case in task.get("transaction"):
            _step = case.get("_step")
            self.user = case.get("user")
            self._user = self.users.get(self.user)
            self._amount = case.get("amount")
            _success = case.get("expectedResult")
            print(f"#################################{_step} by {self.user}####################################")
            
            if _step == Steps.STAKE_OMM:
                self._set_balances("before")
                tx_res = self._stakeOMM(self._user, self._amount)
                self._check_tx_result(tx_res, case)
                self._stake_test(_success, case.get('addedStake'))

            if _step == Steps.TRANSFER_OMM:
                tx_res = self._transferOMM(self._user, self.deployer_wallet.get_address(), self._amount)
                self._check_tx_result(tx_res, case)

            elif _step == Steps.UNSTAKE_OMM:  
                self._set_balances("before")
                tx_res = self._unstakeOMM(self._user, self._amount)
                self._check_tx_result(tx_res, case)
                self._unstake_test(_success)     

            elif _step == Steps.DEPOSIT_USDS:
                tx_res = self._depositUSDS(self._user, self._amount)
                self._check_tx_result(tx_res, case)

    def _check_tx_result(self, tx_result, case):
        if (tx_result['status'] == 0): 
            print("SCORE MESSAGE: ", tx_result['failure']['message'])
            if case.get('revertMessage') != None:
                print("EXPECTED MESSAGE: ", case['revertMessage'])

        if case.get("remarks"):
            print(case.get("remarks"))

        self.assertEqual(tx_result['status'], case['expectedResult'])
        self._set_balances("after")
        self._test_fee_sharing(case.get("feeShared"))

    def _set_balances(self, key: str):
        self.balance[key]["user1"]["icx"] = self.get_balance(self._user.get_address())
        self.balance[key]["user1"]["totalOmmToken"] = self._omm_total_balance(self._user.get_address())
        self.balance[key]["user1"]["stakedOmmToken"] = self._omm_staked_balance(self._user.get_address())       
        self.balance[key]["user1"]["ommToken"] = self._omm_available_balance(self._user.get_address()) 

    def _omm_available_balance(self, _usr):
        lp_balance = self.call_tx(
                to = self.contracts['ommToken'],
                method = "available_balanceOf",
                params = {'_owner': _usr}
            )
        return int(lp_balance,0)

    def _omm_staked_balance(self, _usr):
        lp_balance = self.call_tx(
                to = self.contracts['ommToken'],
                method = "staked_balanceOf",
                params = {'_owner': _usr}
            )
        return int(lp_balance,0)

    def _omm_total_balance(self, _usr):
        lp_balance = self.call_tx(
                to = self.contracts['ommToken'],
                method = "balanceOf",
                params = {'_owner': _usr}
            )
        return (int(lp_balance,0))

    def _test_fee_sharing(self, feeShared):
        icx_amt_before = self.balance["before"]["user1"]["icx"]
        icx_amt_after = self.balance["after"]["user1"]["icx"]
        if feeShared == 1:
            self.assertEqual(icx_amt_after, icx_amt_before)
            print("100% FEE SHARED BY CONTRACT")
        else:
            self.assertGreater(icx_amt_before, icx_amt_after)
   
    def _stake_test(self, _success: int, _added: int = None):
        total_omm_before_user = self.balance["before"]["user1"]["totalOmmToken"] 
        total_omm_after_user = self.balance["after"]["user1"]["totalOmmToken"] 
        staked_omm_before_user = self.balance["before"]["user1"]["stakedOmmToken"] 
        staked_omm_after_user = self.balance["after"]["user1"]["stakedOmmToken"] 
        omm_before_user = self.balance["before"]["user1"]["ommToken"] 
        omm_after_user = self.balance["after"]["user1"]["ommToken"] 

        if _success == 1:
            self.assertEqual(total_omm_after_user, total_omm_before_user)
            if _added is None:
                self.assertEqual(staked_omm_before_user + self._amount, staked_omm_after_user)
                self.assertEqual(omm_before_user, omm_after_user + self._amount)
            else:
                self.assertEqual(staked_omm_before_user + _added, staked_omm_after_user)
                self.assertEqual(omm_before_user, omm_after_user + _added)

    def _unstake_test(self, _success: int):
        total_omm_before_user = self.balance["before"]["user1"]["totalOmmToken"] 
        total_omm_after_user = self.balance["after"]["user1"]["totalOmmToken"] 
        staked_omm_before_user = self.balance["before"]["user1"]["stakedOmmToken"] 
        staked_omm_after_user = self.balance["after"]["user1"]["stakedOmmToken"] 
        omm_before_user = self.balance["before"]["user1"]["ommToken"] 
        omm_after_user = self.balance["after"]["user1"]["ommToken"]

        if _success == 1:
            self.assertEqual(total_omm_after_user, total_omm_before_user)
            self.assertEqual(staked_omm_before_user - self._amount, staked_omm_after_user)
            self.assertEqual(omm_before_user, omm_after_user - self._amount)