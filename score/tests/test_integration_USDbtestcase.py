import os
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.icon_service import IconService
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
from iconsdk.exception import JSONRPCException
import json
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.wallet.wallet import KeyWallet
from lendingPoolCore.Math import *
import time

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
DEPLOY = ['addressProvider', 'feeProvider', 'lendingPool', 'lendingPoolCore',
          'lendingPoolDataProvider', 'oToken', 'priceOracle', 'sample_token']


class TestIntegrationDepositUSDb(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"

    SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()
        self.contracts = {}
        self.icon_service = None
        self.test_account2 = KeyWallet.create()

        # Reserve configurations
        self.feePercentage = 25 * 10 ** 14
        self.USDbRate = 1 * 10 ** 18
        self.liquidationBonus = 10
        self.decimals = 18
        self.baseLTVasCollateral = 6 * 10 ** 17
        self.liquidationThreshold = 65 * 10 ** 16

        # Reserve constants
        self.optimalUtilizationRate = 6 * 10 ** 17
        self.baseBorrowRate = 1 * 10 ** 16
        self.slopeRate1 = 4 * 10 ** 16
        self.slopeRate2 = 5 * 10 ** 17

        # Initial values
        self.initialBorrowRate = 1 * 10 ** 16
        self.initialLiquidityCumulativeIndex = 1 * 10 ** 18
        self.initialBorrowCumulativeIndex = 1 * 10 ** 18

        # deploy SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + address
            self.contracts[address] = self._deploy_score()['scoreAddress']
        self._setVariablesAndInterfaces()
        
        #Test Case 1
        #test_account2 deposits 1 Mil from his 500 Mil 
        self.userTestFundAmount = 500000000 * 10 ** 18
        self._transferTestFundToUser(self.userTestFundAmount)
        self.depositAmount1 = 1000000 * 10 ** 18
        self._deposit(self.depositAmount1)

        """
        #Test Case 2, fails as expected
        #test_account2 try borrowing more than collateral
        self.borrowAmount = 1000001 * 10 ** 18 
        self._borrowFail(self.borrowAmount) 
        """

        #Test Case 3
        #Borrowing 600K
        self.borrowAmount = 600000 * 10 ** 18 
        self._borrow(self.borrowAmount) 
        #The USBb Otoken price of user increases after 10 second sleep time so Interest is accuring.
        #time.sleep(10)

        """
        #Test Case 4
        #Borrow additional amount, fails as expected
        self.borrowAmount = 1 * 10 ** 18
        self._borrowFail(self.borrowAmount)
        """
        
        """
        #Test Case 5 redeem fails
        self.redeemAmount = 100000 * 10 ** 18
        self._redeem(self.redeemAmount)
        """
        
        #Test Case 6 deposting 100k
        self.depositAmount2 = 100000 * 10 ** 18
        self._deposit(self.depositAmount2)

        #Tets Case 7 repay 100k
        self.repayAmount = 100000 * 10 ** 18
        self._repay(self.repayAmount)

        #Test Case 8 withdraw 100k
        self.redeemAmount = 100000 * 10 ** 18
        self._redeem(self.redeemAmount)

    def _setVariablesAndInterfaces(self):
        settings = [{'contract': 'lendingPool', 'method': 'setLendingPoolCoreAddress',
                     'params': {'_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'lendingPool', 'method': 'setUSDbAddress',
                     'params': {'_address': self.contracts['sample_token']}},
                    {'contract': 'lendingPool', 'method': 'setDataProvider', 'params': {
                        '_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'lendingPool', 'method': 'setFeeProvider',
                     'params': {'_address': self.contracts['feeProvider']}},
                    {'contract': 'feeProvider', 'method': 'setLoanOriginationFeePercentage',
                     'params': {'_percentage': self.feePercentage}},
                    {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params': {
                        '_reserveAddress': self.contracts['sample_token'], '_sym': "USDb"}},
                    {'contract': 'lendingPoolDataProvider', 'method': 'setLendingPoolCoreAddress',
                     'params': {'_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'lendingPoolDataProvider', 'method': 'setOracleAddress',
                     'params': {'_address': self.contracts['priceOracle']}},
                    {'contract': 'oToken', 'method': 'setCoreAddress', 'params': {
                        '_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'oToken', 'method': 'setReserveAddress',
                     'params': {'_address': self.contracts['sample_token']}},
                    {'contract': 'oToken', 'method': 'setDataProviderAddress', 'params': {
                        '_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'oToken', 'method': 'setLendingPoolAddress',
                     'params': {'_address': self.contracts['lendingPool']}},
                    {'contract': 'priceOracle', 'method': 'set_reference_data',
                     'params': {'_base': 'USDb', '_quote': 'USD', '_rate': self.USDbRate}},
                    {'contract': 'addressProvider', 'method': 'setLendingPool',
                     'params': {'_address': self.contracts['lendingPool']}},
                    {'contract': 'addressProvider', 'method': 'setLendingPoolDataProvider',
                     'params': {'_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'addressProvider', 'method': 'setUSDb',
                     'params': {'_address': self.contracts['sample_token']}},
                    {'contract': 'addressProvider', 'method': 'setoUSDb',
                     'params': {'_address': self.contracts['oToken']}},
                    {'contract': 'lendingPoolCore', 'method': 'setReserveConstants', 'params': {"_constants": [
                        {"reserve": self.contracts['sample_token'],
                         "optimalUtilizationRate": str(self.optimalUtilizationRate),
                         "baseBorrowRate": str(self.baseBorrowRate), "slopeRate1": str(self.slopeRate1),
                         "slopeRate2": str(self.slopeRate2)}]}}]

        for sett in settings:
            # print(sett)
            transaction = CallTransactionBuilder() \
                .from_(self._test1.get_address()) \
                .to(self.contracts[sett['contract']]) \
                .value(0) \
                .step_limit(10000000) \
                .nid(3) \
                .nonce(100) \
                .method(sett['method']) \
                .params(sett['params']) \
                .build()
            signed_transaction = SignedTransaction(transaction, self._test1)
            tx_result = self.process_transaction(signed_transaction)
            self.assertTrue('status' in tx_result)
            self.assertEqual(1, tx_result['status'])

        # Initializing  a reserve
        params = {"_reserve": {"reserveAddress": self.contracts['sample_token'],
                               "oTokenAddress": self.contracts['oToken'],
                               "totalBorrows": "0",
                               "lastUpdateTimestamp": "0",
                               "liquidityRate": "0",
                               "borrowRate": "0",
                               "liquidityCumulativeIndex": f"1{'0' * 18}",
                               "borrowCumulativeIndex": f"1{'0' * 18}",
                               "baseLTVasCollateral": str(self.baseLTVasCollateral),
                               "liquidationThreshold": str(self.liquidationThreshold),
                               "liquidationBonus": str(self.liquidationBonus),
                               "decimals": str(self.decimals),
                               "borrowingEnabled": "1",
                               "usageAsCollateralEnabled": "1",
                               "isFreezed": "0",
                               "isActive": "1"}}

        call_transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("addReserveData") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(call_transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _transferTestFundToUser(self, _testFund: int):
        # Transferring 500 Mill USdb to  test_account2
        params = {"_to": self.test_account2.get_address(),"_value": _testFund}
        call_transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(call_transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _deposit(self, _depositAmount: int):

        # calling deposit from test_account2
        depositData = {'method': 'deposit', 'params': {'amount': _depositAmount}}
        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _depositAmount, "_data": data}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account2.get_address()) \
            .to(self.contracts['sample_token']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, self.test_account2)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    #Used for Test Case 2
    def _borrowFail(self, _borrowAmount: int):
        #calling borrow where _borrowAmount> liquidity
        params = {"_reserve": self.contracts['sample_token'], "_amount": _borrowAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account2.get_address()) \
            .to(self.contracts['lendingPool']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("borrow") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, self.test_account2)
        tx_result = self.process_transaction(signed_transaction)
        #test_Second_BorrowFail
        self.assertEqual(0, tx_result['status'])

    def _borrow(self, _borrowAmount: int):
        params = {"_reserve": self.contracts['sample_token'], "_amount": _borrowAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account2.get_address()) \
            .to(self.contracts['lendingPool']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("borrow") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, self.test_account2)
        tx_result = self.process_transaction(signed_transaction)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('status' in tx_result)

    def _redeem(self, _redeemAmount: int):
        #calling redeem in oToken
        params = {"_amount": _redeemAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account2.get_address()) \
            .to(self.contracts['oToken']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("redeem") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(call_transaction, self.test_account2)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])  
        #print(tx_result)  

    def _repay(self, _repayAmount: int):
        depositData = {'method': 'repay', 'params': {'amount': _repayAmount}}
        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _repayAmount, "_data": data}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account2.get_address()) \
            .to(self.contracts['sample_token']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, self.test_account2)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, _type: str = 'install') -> dict:
        # Generates an instance of transaction for deploying SCORE.
        if _type == 'install':
            if "sample_token" in self.SCORE_PROJECT:
                params = {'_initialSupply': 500000000, '_decimals': 18}
            elif "oToken" in self.SCORE_PROJECT:
                params = {"_name": "BridgeUSDInterestToken",
                          "_symbol": "oUSDb"}
            else:
                params = {}
        else:
            params = {}

        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
            .params(params) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction)

        # check transaction result
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def test_score_update(self):
        # update SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + address
            SCORE_PROJECT = os.path.abspath(
                os.path.join(DIR_PATH, '..')) + "/" + address
            tx_result = self._deploy_score(self.contracts[address], 'update')
            self.assertEqual(
                self.contracts[address], tx_result['scoreAddress'])
    """
    def test_First_DepositTest(self):
        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveData = self.process_call(_call)
        print('userReserveData', userReserveData)

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser = self.process_call(_call)
        print('balanceOfUser', int(balanceOfUser, 16))

        self.assertEqual(int(balanceOfUser, 16), (self.userTestFundAmount - self.depositAmount1))
        self.assertEqual(userReserveData['currentOTokenBalance'], self.depositAmount1)
        #even though there is no borrowing yet but the borrow rate will be equal to the base borrow rate in this case i.e 10 ** 16
        self.assertEqual(userReserveData['borrowRate'], 10 ** 16)
        self.assertEqual(userReserveData['liquidityRate'], 0)
    """
    
    """
    def test_Third_BorrowTest(self):
        #time.sleep(20)
        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveData = self.process_call(_call)
        print('userReserveData', userReserveData)

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser = self.process_call(_call) 
        print('balanceOfUser', int(balanceOfUser, 16))
        self.assertEqual(int(balanceOfUser, 16), (self.userTestFundAmount - self.depositAmount1 + self.borrowAmount))
        #interest increase with time is left to calculate.
        #self.assertEqual(userReserveData['currentOTokenBalance'], self.depositAmount1)

        #Test Case 3.1 
        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveData = self.process_call(_call)
        print('reserveData:::', reserveData)

        params = {'_reserve': self.contracts['sample_token'], '_availableLiquidity': (self.depositAmount1 - self.borrowAmount) ,'_totalBorrows': self.borrowAmount}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        rates = self.process_call(_call)
        #print('rates:::', rates)

        #Check User Account Data
        self.assertEqual(reserveData['availableLiquidity'], (self.depositAmount1 - self.borrowAmount))
        self.assertEqual(reserveData['baseLTVasCollateral'], self.baseLTVasCollateral)
        #Need Subham Dai to verify the baseLTVasCollateral test
        self.assertEqual(reserveData['baseLTVasCollateral'], self.baseLTVasCollateral)
        self.assertEqual(reserveData['borrowRate'], rates['borrowRate'])
        self.assertEqual(reserveData['liquidityRate'], rates['liquidityRate'])

        #Test Case 3.2
        #Get user account data
        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        userAccountData = self.process_call(_call)
        #print('userAccountData', userAccountData)

        #Get origination fee
        params = {'_user': self.test_account2.get_address(), '_amount': self.borrowAmount}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFee = self.process_call(_call)
        #print('originationFee', int(originationFee, 16))

        #Get healthfactor
        params = {'_collateralBalanceUSD': exaMul((self.depositAmount1), self.USDbRate),
                 '_borrowBalanceUSD': exaMul(self.borrowAmount, self.USDbRate),
                 '_totalFeesUSD': exaMul(int(originationFee, 16), self.USDbRate),
                 '_liquidationThreshold': userAccountData['currentLiquidationThreshold']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactor = self.process_call(_call)
        #print('healthFactor', int(healthFactor, 16))

        self.assertEqual(reserveData['liquidationThreshold'], self.liquidationThreshold)
        self.assertEqual(reserveData['baseLTVasCollateral'], self.baseLTVasCollateral)
        self.assertEqual(userAccountData['healthFactor'], int(healthFactor, 16))
        self.assertEqual(userAccountData['totalFeesUSD'], int(originationFee, 16))
    """

    """
    def test_Sixth_DepositTest(self):
        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveData = self.process_call(_call)
        print('userReserveData', userReserveData)

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser = self.process_call(_call)
        print('balanceOfUser', int(balanceOfUser, 16))

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveData = self.process_call(_call)
        print('reserveData:::', reserveData)

        self.assertEqual(userReserveData['currentOTokenBalance'], (self.depositAmount1 + self.depositAmount2))
        self.assertEqual(int(balanceOfUser, 16), (self.userTestFundAmount - self.depositAmount1 + self.borrowAmount - self.depositAmount2))
    """

    """
    def test_Seventh_RepayTest(self):
        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveData = self.process_call(_call)
        print('userReserveData', userReserveData)

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser = self.process_call(_call)
        print('balanceOfUser', int(balanceOfUser, 16))

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveData = self.process_call(_call)
        print('reserveData:::', reserveData)

        params = {'_user': self.test_account2.get_address(), '_amount': self.borrowAmount}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFee = self.process_call(_call)
        print('originationFee', int(originationFee, 16))

        params = {'_reserve': self.contracts['sample_token'], '_availableLiquidity': (self.depositAmount1 - self.borrowAmount + self.depositAmount2 + self.repayAmount  - int(originationFee, 16)) ,'_totalBorrows': (self.borrowAmount - self.repayAmount + int(originationFee, 16)) }
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        rates = self.process_call(_call)
        print('rates:::', rates)
    """

    def test_Eigth_WithdrawTest(self):
        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveData = self.process_call(_call)
        print('userReserveData', userReserveData)

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser = self.process_call(_call)
        print('balanceOfUser', int(balanceOfUser, 16))

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveData = self.process_call(_call)
        print('reserveData:::', reserveData)

        params = {'_user': self.test_account2.get_address(), '_amount': self.borrowAmount}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFee = self.process_call(_call)
        print('originationFee', int(originationFee, 16))

        params = {'_reserve': self.contracts['sample_token'], '_availableLiquidity': (self.depositAmount1 - self.borrowAmount + self.depositAmount2 + self.repayAmount - self.redeemAmount - int(originationFee, 16)) ,'_totalBorrows': (self.borrowAmount - (self.redeemAmount - int(originationFee, 16))) }
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        rates = self.process_call(_call)
        print('rates:::', rates)

        self.assertEqual(reserveData['availableLiquidity'], (self.depositAmount1 - self.borrowAmount - self.redeemAmount + self.depositAmount2 + self.repayAmount - int(originationFee, 16)))
        #self.assertEqual(reserveData['totalLiquidity'], (self.depositAmount1 - self.redeemAmount + self.depositAmount2 )) #accuredinterest will fail asserEqual
        #self.assertEqual(reserveData['totalBorrows'], (self.borrowAmount - self.repayAmount + int(originationFee, 16)))  #accuredinterest will fail asserEqual
        self.assertEqual(reserveData['borrowRate'], rates['borrowRate'])
        self.assertEqual(reserveData['liquidityRate'], rates['liquidityRate'])
        self.assertEqual(int(balanceOfUser, 16), (self.userTestFundAmount - self.depositAmount1 + self.borrowAmount - self.depositAmount2 - self.repayAmount + self.redeemAmount ))

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        userAccountData = self.process_call(_call)
        print('userAccountData', userAccountData)


    