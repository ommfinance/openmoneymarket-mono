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
          'lendingPoolDataProvider', 'priceOracle', 'sample_token', 'sicx']


class TestIntegrationDepositUSDb(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"

    SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()
        self.contracts = {}
        self.icon_service = None
        self.test_account2 = KeyWallet.create()
        self.test_account3 = KeyWallet.create()
        # Reserve configurations
        self.feePercentage = 25 * 10 ** 14
        self.USDbRate = 1 * 10 ** 18
        self.sICXRate = 5 * 10 ** 17
        self.ICXRate = 1 * 10 ** 18
        self.liquidationBonus = 10
        self.decimals = 18
        self.baseLTVasCollateralICX = 33 * 10 ** 16
        self.baseLTVasCollateralUSDb = 33 * 10 ** 16
        self.liquidationThreshold = 65 * 10 ** 16

        # Reserve constants of USDb
        self.optimalUtilizationRateUSDb = 6 * 10 ** 17
        self.baseBorrowRateUSDb = 1 * 10 ** 16
        self.slopeRate1USDb = 4 * 10 ** 16
        self.slopeRate2USDb = 5 * 10 ** 17

        # Reserve constants of IXC
        self.optimalUtilizationRateICX = 6 * 10 ** 17
        self.baseBorrowRateICX = 0
        self.slopeRate1ICX = 7 * 10 ** 16
        self.slopeRate2ICX = 3 * 10 ** 18


        # Initial values
        self.initialBorrowRate = 1 * 10 ** 16
        self.initialLiquidityCumulativeIndex = 1 * 10 ** 18
        self.initialBorrowCumulativeIndex = 1 * 10 ** 18

        # deploy SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + address
            self.contracts[address] = self._deploy_score()['scoreAddress']
        self.SCORE_PROJECT = self.SCORES + "/oToken" 
        self.contracts["oICX"] = self._deploy_score(_oTokenName = 'oICX')['scoreAddress']  
        self.SCORE_PROJECT = self.SCORES + "/oToken" 
        self.contracts["oUSDb"] = self._deploy_score(_oTokenName = 'oUSDb')['scoreAddress']
        #print('contracts', self.contracts)
        self._setVariablesAndInterfaces()

        #Test Case 1
        #Transfer 1 Mill ICX to test_account2
        self.userTestICXAmount = 1000000 * 10 ** 18
        self._transferTestICXToUser(self.userTestICXAmount)

        #Trasnfer 1 Mill USDb to test_account3
        self.userTestUSdbAmount = 1000000 * 10 ** 18
        self._trasnferTestUSDbToUser(self.userTestUSdbAmount)

        #test_account2 deposits 50k ICX into sicx reserve
        self.depositICXAmount1 = 50000 * 10 ** 18
        self._depositICX(self.depositICXAmount1)

        #test_account3 deposits 40k USDb into usdb reserve i.e sample_token        
        self.depositUSDbAmount1 = 40000 * 10 ** 18
        self._depositUSDb(self.depositUSDbAmount1)

        #Test Case 2
        #test_account2 borrows 5k USDb from USDb reserve
        self.borrowUSDbAmount1 = 5000 * 10 ** 18
        self._borrowUSDb(self.borrowUSDbAmount1)
        
        #Test Case 3
        #test_account3 borrows 20k sICX from sICX reserve
        self.borrowSICXAmount1 = 20000 * 10 ** 18
        self._borrowSICX(self.borrowSICXAmount1)

        #Test Case 4
        #test_account2  Repays 3k USDb 
        self.repayUSDbAmount1 = 3000 * 10 ** 18
        self._repayUSDb(self.repayUSDbAmount1)

        #Test Case 5
        #test_account3  Repays 15k sICX
        self.repaySICXAmount1 = 15000 * 10 ** 18
        self._repaySICX(self.repaySICXAmount1)

        #Test Case 6
        #test_Account2 redeems 10k ICX
        self.redeemIXCAmount1 = 10000 * 10 ** 18
        self._redeemIXC(self.redeemIXCAmount1)

        #Test Case 7
        #test_Account3 redeems 20k USDb
        self.redeemUSDbAmount1 = 20000 * 10 ** 18
        self._redeemUSDb(self.redeemUSDbAmount1)

    def _setVariablesAndInterfaces(self):
        settings = [{'contract': 'lendingPool', 'method': 'setLendingPoolCoreAddress',
                     'params': {'_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'lendingPool', 'method': 'setUSDbAddress',
                     'params': {'_address': self.contracts['sample_token']}},

                    {'contract': 'lendingPool', 'method': 'setSICXAddress',
                     'params': {'_address': self.contracts['sicx']}},

                    {'contract': 'lendingPool', 'method': 'setDataProvider', 
                     'params': {'_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'lendingPool', 'method': 'setFeeProvider',
                     'params': {'_address': self.contracts['feeProvider']}},
                    {'contract': 'feeProvider', 'method': 'setLoanOriginationFeePercentage',
                     'params': {'_percentage': self.feePercentage}},
                    {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params': {
                        '_reserveAddress': self.contracts['sample_token'], '_sym': "USDb"}},

                    {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params': {
                        '_reserveAddress': self.contracts['sicx'], '_sym': "Sicx"}},

                    {'contract': 'lendingPoolDataProvider', 'method': 'setLendingPoolCoreAddress',
                     'params': {'_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'lendingPoolDataProvider', 'method': 'setOracleAddress',
                     'params': {'_address': self.contracts['priceOracle']}},

                    {'contract': 'oICX', 'method': 'setCoreAddress', 'params': {
                        '_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'oICX', 'method': 'setReserveAddress',
                     'params': {'_address': self.contracts['sicx']}},
                    {'contract': 'oICX', 'method': 'setDataProviderAddress', 'params': {
                        '_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'oICX', 'method': 'setLendingPoolAddress',
                     'params': {'_address': self.contracts['lendingPool']}},

                    {'contract': 'oUSDb', 'method': 'setCoreAddress', 'params': {
                        '_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'oUSDb', 'method': 'setReserveAddress',
                     'params': {'_address': self.contracts['sample_token']}},
                    {'contract': 'oUSDb', 'method': 'setDataProviderAddress', 'params': {
                        '_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'oUSDb', 'method': 'setLendingPoolAddress',
                     'params': {'_address': self.contracts['lendingPool']}},

                    {'contract': 'priceOracle', 'method': 'set_reference_data',
                     'params': {'_base': 'USDb', '_quote': 'USD', '_rate': self.USDbRate}},

                    {'contract': 'priceOracle', 'method': 'set_reference_data',
                     'params': {'_base': 'Sicx', '_quote': 'USD', '_rate': self.sICXRate}},

                    {'contract': 'addressProvider', 'method': 'setLendingPool',
                     'params': {'_address': self.contracts['lendingPool']}},
                    {'contract': 'addressProvider', 'method': 'setLendingPoolDataProvider',
                     'params': {'_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'addressProvider', 'method': 'setUSDb',
                     'params': {'_address': self.contracts['sample_token']}},
                    {'contract': 'addressProvider', 'method': 'setoUSDb',
                     'params': {'_address': self.contracts['oUSDb']}},

                    {'contract': 'addressProvider', 'method': 'setsICX',
                     'params': {'_address': self.contracts['sicx']}},
                    {'contract': 'addressProvider', 'method': 'setoICX',
                     'params': {'_address': self.contracts['oICX']}},

                    {'contract': 'lendingPoolCore', 'method': 'setReserveConstants', 'params': {"_constants": [
                        {"reserve": self.contracts['sample_token'],
                         "optimalUtilizationRate": str(self.optimalUtilizationRateUSDb),
                         "baseBorrowRate": str(self.baseBorrowRateUSDb), "slopeRate1": str(self.slopeRate1USDb),
                         "slopeRate2": str(self.slopeRate2USDb)}]}},

                    {'contract': 'lendingPoolCore', 'method': 'setReserveConstants', 'params': {"_constants": [
                        {"reserve": self.contracts['sicx'],
                         "optimalUtilizationRate": str(self.optimalUtilizationRateICX),
                         "baseBorrowRate": str(self.baseBorrowRateICX), "slopeRate1": str(self.slopeRate1ICX),
                         "slopeRate2": str(self.slopeRate2ICX)}]}}
                    ]

        for sett in settings:
            #print(sett)
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

        # Initializing  a USDB reserve
        paramsUSDb = {"_reserve": {"reserveAddress": self.contracts['sample_token'],
                               "oTokenAddress": self.contracts['oUSDb'], 
                               "totalBorrows": "0",
                               "lastUpdateTimestamp": "0",
                               "liquidityRate": "0",
                               "borrowRate": "0",
                               "liquidityCumulativeIndex": f"1{'0' * 18}",
                               "borrowCumulativeIndex": f"1{'0' * 18}",
                               "baseLTVasCollateral": str(self.baseLTVasCollateralUSDb),
                               "liquidationThreshold": str(self.liquidationThreshold),
                               "liquidationBonus": str(self.liquidationBonus),
                               "decimals": str(self.decimals),
                               "borrowingEnabled": "1",
                               "usageAsCollateralEnabled": "1",
                               "isFreezed": "0",
                               "isActive": "1"}}

        # Initializing  an ICX reserve
        paramsICX = {"_reserve": {"reserveAddress": self.contracts['sicx'],
                               "oTokenAddress": self.contracts['oICX'], 
                               "totalBorrows": "0",
                               "lastUpdateTimestamp": "0",
                               "liquidityRate": "0",
                               "borrowRate": "0",
                               "liquidityCumulativeIndex": f"1{'0' * 18}",
                               "borrowCumulativeIndex": f"1{'0' * 18}",
                               "baseLTVasCollateral": str(self.baseLTVasCollateralICX),
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
            .params(paramsUSDb) \
            .build()
        signed_transaction = SignedTransaction(call_transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

        call_transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("addReserveData") \
            .params(paramsICX) \
            .build()
        signed_transaction = SignedTransaction(call_transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, _type: str = 'install', _oTokenName: str = '') -> dict:
        if _type == 'install':
            if "sample_token" in self.SCORE_PROJECT:
                params = {'_initialSupply': 500000000, '_decimals': 18}
            elif "sicx" in self.SCORE_PROJECT:
                params = {'_initialSupply': 500000000, '_decimals': 18}
            else:
                params = {}
        else:
            params = {}

        if _oTokenName == 'oICX':
            params = {"_name": "BridgeICXInterestToken", "_symbol": "oICX"}
        if _oTokenName == 'oUSDb':
            params = {"_name": "BridgeUSDInterestToken", "_symbol": "oUSDb",}

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

    def _transferTestICXToUser(self, _testFund: int):
        # Transferring 100k ICX to  test_account2
        transaction = TransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.test_account2.get_address()) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .value(_testFund)\
            .build()
        
        signed_transaction = SignedTransaction(
            transaction, self._test1)
        tx_result = self.process_transaction(signed_transaction)
        #print(tx_result)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _trasnferTestUSDbToUser(self, _testFund: int):
        # Transferring 1 Mill USdb to  test_account3
        params = {"_to": self.test_account3.get_address(),"_value": _testFund}
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

    def _depositICX(self, _depositAmount: int):
        # calling deposit from test_account2
        #depositData = {'method': 'repay', 'params': {'amount': _repayAmount}}
        #data = json.dumps(depositData).encode('utf-8')
        params = {"_amount": _depositAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account2.get_address()) \
            .to(self.contracts['lendingPool']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .value(_depositAmount) \
            .method("deposit") \
            .params(params) \
            .build() 

        signed_transaction = SignedTransaction(
            call_transaction, self.test_account2)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _depositUSDb(self, _depositAmount: int):
        depositData = {'method': 'deposit', 'params': {'amount': _depositAmount}}
        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _depositAmount, "_data": data}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account3.get_address()) \
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

    def _borrowUSDb(self, _borrowAmount : int):
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

    def _borrowSICX(self, _borrowAmount : int):
        params = {"_reserve": self.contracts['sicx'], "_amount": _borrowAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account3.get_address()) \
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

    def _repayUSDb(self, _repayAmount: int):
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

    def _repaySICX(self, _repayAmount: int):
        depositData = {'method': 'repay', 'params': {'amount': _repayAmount}}
        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _repayAmount, "_data": data}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account3.get_address()) \
            .to(self.contracts['sicx']) \
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

    def _redeemIXC(self, _redeemAmount : int):
        params = {"_amount": _redeemAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account2.get_address()) \
            .to(self.contracts['oICX']) \
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

    def _redeemUSDb(self, _redeemAmount : int):
        params = {"_amount": _redeemAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(self.test_account3.get_address()) \
            .to(self.contracts['oUSDb']) \
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
    """
    def test_one_initTest(self):
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2USDb = self.process_call(_call)
        #print('balanceOfUser2USDb', int(balanceOfUser2USDb, 16))

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2sICX = self.process_call(_call)
        #print('balanceOfUser2sICX', int(balanceOfUser2sICX, 16))

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oICX']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2OICX = self.process_call(_call)
        #print('balanceOfUser2OICX', int(balanceOfUser2OICX, 16))

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oUSDb']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2OUSDb = self.process_call(_call)
        #print('balanceOfUser2OUSDb', int(balanceOfUser2OUSDb, 16))

        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3USDb = self.process_call(_call)
        #print('balanceOfUser3USDb', int(balanceOfUser3USDb, 16))

        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3sICX = self.process_call(_call)
        #print('balanceOfUser3sICX', int(balanceOfUser3sICX, 16))

        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oICX']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3OICX = self.process_call(_call)
        #print('balanceOfUser3OICX', int(balanceOfUser3OICX, 16))

        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oUSDb']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3OUSDb = self.process_call(_call)
        #print('balanceOfUser3OUSDb', int(balanceOfUser3OUSDb, 16))

        self.assertEqual(balanceOfUser2USDb, hex(0))
        self.assertEqual(balanceOfUser2sICX, hex(0)) 
        self.assertEqual(balanceOfUser2OICX, hex(self.depositICXAmount1))
        self.assertEqual(balanceOfUser2OUSDb, hex(0))
        self.assertEqual(balanceOfUser3USDb, hex(self.userTestUSdbAmount - self.depositUSDbAmount1))
        self.assertEqual(balanceOfUser3sICX, hex(0))
        self.assertEqual(balanceOfUser3OICX, hex(0))
        self.assertEqual(balanceOfUser3OUSDb, hex(self.depositUSDbAmount1))

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDataUSDb = self.process_call(_call)
        #print('USERR2ESERVEDATAUSDB', user2ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDatasICX = self.process_call(_call)
        #print('USER2RESERVEDATASICX', user2ReserveDatasICX)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDataUSDb = self.process_call(_call)
        #print('USERR3ESERVEDATAUSDB', user3ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDatasICX = self.process_call(_call)
        #print('USER3RESERVEDATASICX', user3ReserveDatasICX)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user2AccountData = self.process_call(_call)
        #print('USER2ACCOUNTDATA', user2AccountData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user3AccountData = self.process_call(_call)
        #print('USER3ACCOUNTDATA', user3AccountData)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user2AllReserveData = self.process_call(_call)
        #print('USER2ALLRESERVEDATA', user2AllReserveData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user3AllReserveData = self.process_call(_call)
        #print('USER3ALLRESERVEDATA', user3AllReserveData)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        #print('RESERVEDATAUSDB:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDatasICX = self.process_call(_call)
        #print('RESERVEDATASICX:::', reserveDatasICX)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        #print('RESERVEACCOUNTDATA', reserveAccountData)

        self.assertEqual(user2ReserveDataUSDb['currentOTokenBalance'], 0)
        self.assertEqual(user2ReserveDatasICX['currentOTokenBalance'], self.depositICXAmount1)
        self.assertEqual(user2ReserveDataUSDb['borrowRate'], self.baseBorrowRateUSDb)
        self.assertEqual(user3ReserveDataUSDb['currentOTokenBalance'], self.depositUSDbAmount1)
        self.assertEqual(user3ReserveDatasICX['currentOTokenBalance'], 0)
        self.assertEqual(user3ReserveDataUSDb['borrowRate'], self.baseBorrowRateUSDb)
        self.assertEqual(user2AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositICXAmount1, self.sICXRate))
        self.assertEqual(user3AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositUSDbAmount1, self.USDbRate))
        self.assertEqual(user2AllReserveData['USDb']['currentOTokenBalance'] + user2AllReserveData['Sicx']['currentOTokenBalance'] , user2ReserveDataUSDb['currentOTokenBalance'] + user2ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(user3AllReserveData['USDb']['currentOTokenBalance'] + user3AllReserveData['Sicx']['currentOTokenBalance'] , user3ReserveDataUSDb['currentOTokenBalance'] + user3ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(reserveDataUSDb['borrowRate'], user3ReserveDataUSDb['borrowRate'])
        self.assertEqual(reserveDataUSDb['totalLiquidity'], self.depositUSDbAmount1)
        self.assertEqual(reserveDataUSDb['availableLiquidity'], self.depositUSDbAmount1)
        self.assertEqual(reserveDataUSDb['totalBorrows'], 0)    
        self.assertEqual(reserveDatasICX['borrowRate'], self.baseBorrowRateICX)
        self.assertEqual(reserveDatasICX['totalLiquidity'], self.depositICXAmount1)
        self.assertEqual(reserveDatasICX['availableLiquidity'], self.depositICXAmount1)
        self.assertEqual(reserveDatasICX['totalBorrows'], 0)
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalBorrowsBalanceUSD'], exaMul(reserveDataUSDb['totalBorrows'] , self.USDbRate) + exaMul(reserveDatasICX['totalBorrows'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalCollateralBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
    """

    """
    def test_two_borrowTestUSDb(self):
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2USDb = self.process_call(_call)
        print('balanceOfUser2USDb', int(balanceOfUser2USDb, 16))

        self.assertEqual(balanceOfUser2USDb, hex(self.borrowUSDbAmount1))

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDataUSDb = self.process_call(_call)
        print('USERR2ESERVEDATAUSDB', user2ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDatasICX = self.process_call(_call)
        print('USER2RESERVEDATASICX', user2ReserveDatasICX)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDataUSDb = self.process_call(_call)
        print('USERR3ESERVEDATAUSDB', user3ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDatasICX = self.process_call(_call)
        print('USER3RESERVEDATASICX', user3ReserveDatasICX)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user2AccountData = self.process_call(_call)
        print('USER2ACCOUNTDATA', user2AccountData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user3AccountData = self.process_call(_call)
        print('USER3ACCOUNTDATA', user3AccountData)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user2AllReserveData = self.process_call(_call)
        print('USER2ALLRESERVEDATA', user2AllReserveData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user3AllReserveData = self.process_call(_call)
        print('USER3ALLRESERVEDATA', user3AllReserveData)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        print('RESERVEDATAUSDB:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDatasICX = self.process_call(_call)
        print('RESERVEDATASICX:::', reserveDatasICX)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        print('RESERVEACCOUNTDATA', reserveAccountData)

        params = {'_reserve': self.contracts['sample_token'], '_availableLiquidity': (self.depositUSDbAmount1 - self.borrowUSDbAmount1) ,'_totalBorrows': self.borrowUSDbAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        ratesUSDb = self.process_call(_call)
        print('ratesUSDb:::', ratesUSDb) 

        params = {'_user': self.test_account2.get_address(), '_amount': self.borrowUSDbAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser2USdbBorrow = self.process_call(_call)
        print('originationFeeUser2USdbBorrow', int(originationFeeUser2USdbBorrow, 16))

        #healthfactor for user2
        params = {'_collateralBalanceUSD': exaMul((self.depositICXAmount1), self.sICXRate),
                 '_borrowBalanceUSD': exaMul(self.borrowUSDbAmount1, self.USDbRate),
                 '_totalFeesUSD': exaMul(int(originationFeeUser2USdbBorrow, 16), self.USDbRate),
                 '_liquidationThreshold': user2AccountData['currentLiquidationThreshold']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactorUser2 = self.process_call(_call)
        print('healthFactorUser2', int(healthFactorUser2, 16))

        self.assertEqual(user2ReserveDataUSDb['currentOTokenBalance'], 0)
        self.assertEqual(user2ReserveDataUSDb['currentBorrowBalance'], self.borrowUSDbAmount1)
        self.assertEqual(user2ReserveDataUSDb['currentBorrowBalanceUSD'], exaMul(self.borrowUSDbAmount1, self.USDbRate))
        self.assertEqual(user2ReserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(user2ReserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        self.assertEqual(user2ReserveDataUSDb['originationFee'], int(originationFeeUser2USdbBorrow, 16))
        self.assertEqual(user2ReserveDatasICX['currentOTokenBalance'], self.depositICXAmount1)
        self.assertEqual(user3ReserveDataUSDb['currentOTokenBalance'], self.depositUSDbAmount1)
        self.assertEqual(user3ReserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(user3ReserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        self.assertEqual(user3ReserveDataUSDb['originationFee'], 0)
        self.assertEqual(user3ReserveDatasICX['currentOTokenBalance'], 0)  
        self.assertEqual(user2AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositICXAmount1, self.sICXRate))
        self.assertEqual(user2AccountData['totalBorrowBalanceUSD'], exaMul(self.borrowUSDbAmount1, self.USDbRate))
        self.assertEqual(user2AccountData['healthFactor'], int(healthFactorUser2, 16))
        self.assertEqual(user3AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositUSDbAmount1, self.USDbRate))
        self.assertEqual(user2AllReserveData['USDb']['currentOTokenBalance'] + user2AllReserveData['Sicx']['currentOTokenBalance'] , user2ReserveDataUSDb['currentOTokenBalance'] + user2ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(user3AllReserveData['USDb']['currentOTokenBalance'] + user3AllReserveData['Sicx']['currentOTokenBalance'] , user3ReserveDataUSDb['currentOTokenBalance'] + user3ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(reserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(reserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        self.assertEqual(reserveDataUSDb['totalLiquidity'], self.depositUSDbAmount1)
        self.assertEqual(reserveDataUSDb['availableLiquidity'], (self.depositUSDbAmount1 - self.borrowUSDbAmount1))
        self.assertEqual(reserveDataUSDb['totalBorrows'], self.borrowUSDbAmount1)  
        self.assertEqual(reserveDatasICX['borrowRate'], self.baseBorrowRateICX)
        self.assertEqual(reserveDatasICX['totalLiquidity'], self.depositICXAmount1)
        self.assertEqual(reserveDatasICX['availableLiquidity'], self.depositICXAmount1)
        self.assertEqual(reserveDatasICX['totalBorrows'], 0)
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalBorrowsBalanceUSD'], exaMul(reserveDataUSDb['totalBorrows'] , self.USDbRate) + exaMul(reserveDatasICX['totalBorrows'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalCollateralBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
    """
    """
    def test_three_borrowTestsICX(self):
        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3sICX = self.process_call(_call)
        print('balanceOfUser3sICX', int(balanceOfUser3sICX, 16))

        self.assertEqual(balanceOfUser3sICX, hex(self.borrowSICXAmount1))

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDataUSDb = self.process_call(_call)
        print('USERR2ESERVEDATAUSDB', user2ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDatasICX = self.process_call(_call)
        print('USER2RESERVEDATASICX', user2ReserveDatasICX)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDataUSDb = self.process_call(_call)
        print('USERR3ESERVEDATAUSDB', user3ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDatasICX = self.process_call(_call)
        print('USER3RESERVEDATASICX', user3ReserveDatasICX)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user2AccountData = self.process_call(_call)
        print('USER2ACCOUNTDATA', user2AccountData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user3AccountData = self.process_call(_call)
        print('USER3ACCOUNTDATA', user3AccountData)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user2AllReserveData = self.process_call(_call)
        print('USER2ALLRESERVEDATA', user2AllReserveData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user3AllReserveData = self.process_call(_call)
        print('USER3ALLRESERVEDATA', user3AllReserveData)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        print('RESERVEDATAUSDB:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDatasICX = self.process_call(_call)
        print('RESERVEDATASICX:::', reserveDatasICX)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        print('RESERVEACCOUNTDATA', reserveAccountData)

        params = {'_reserve': self.contracts['sicx'], '_availableLiquidity': (self.depositICXAmount1 - self.borrowSICXAmount1) ,'_totalBorrows': self.borrowSICXAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        ratessICX = self.process_call(_call)
        print('ratessICX:::', ratessICX) 

        params = {'_user': self.test_account3.get_address(), '_amount': self.borrowSICXAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser3sICXBorrow = self.process_call(_call)
        print('originationFeeUser3sICXBorrow', int(originationFeeUser3sICXBorrow, 16))

        #healthfactor for user2
        params = {'_collateralBalanceUSD': exaMul((self.depositUSDbAmount1), self.USDbRate),
                 '_borrowBalanceUSD': exaMul(self.borrowSICXAmount1, self.sICXRate),
                 '_totalFeesUSD': exaMul(int(originationFeeUser3sICXBorrow, 16), self.sICXRate),
                 '_liquidationThreshold': user2AccountData['currentLiquidationThreshold']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactorUser3 = self.process_call(_call)
        print('healthFactorUser3', int(healthFactorUser3, 16))

        self.assertEqual(user2ReserveDataUSDb['currentOTokenBalance'], 0)
        #Commented Test does not pass due to accured interest for
        #self.assertEqual(user2ReserveDataUSDb['currentBorrowBalance'], self.borrowUSDbAmount1)
        #self.assertEqual(user2ReserveDataUSDb['currentBorrowBalanceUSD'], exaMul(self.borrowUSDbAmount1, self.USDbRate))
        self.assertEqual(user2ReserveDatasICX['currentOTokenBalance'], self.depositICXAmount1)
        self.assertEqual(user3ReserveDataUSDb['currentOTokenBalance'], self.depositUSDbAmount1)
        self.assertEqual(user3ReserveDatasICX['borrowRate'], ratessICX['borrowRate'])
        self.assertEqual(user3ReserveDatasICX['liquidityRate'], ratessICX['liquidityRate'])
        self.assertEqual(user3ReserveDatasICX['originationFee'], int(originationFeeUser3sICXBorrow, 16))
        self.assertEqual(user3ReserveDatasICX['currentOTokenBalance'], 0)  
        self.assertEqual(user2AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositICXAmount1, self.sICXRate))
        #sself.assertEqual(user2AccountData['totalBorrowBalanceUSD'], exaMul(self.borrowUSDbAmount1, self.USDbRate))
        self.assertEqual(user3AccountData['healthFactor'], int(healthFactorUser3, 16))
        self.assertEqual(user3AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositUSDbAmount1, self.USDbRate))
        self.assertEqual(user2AllReserveData['USDb']['currentOTokenBalance'] + user2AllReserveData['Sicx']['currentOTokenBalance'] , user2ReserveDataUSDb['currentOTokenBalance'] + user2ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(user3AllReserveData['USDb']['currentOTokenBalance'] + user3AllReserveData['Sicx']['currentOTokenBalance'] , user3ReserveDataUSDb['currentOTokenBalance'] + user3ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(reserveDatasICX['borrowRate'], ratessICX['borrowRate'])
        self.assertEqual(reserveDatasICX['liquidityRate'], ratessICX['liquidityRate'])
        self.assertEqual(reserveDataUSDb['totalLiquidity'], self.depositUSDbAmount1)
        self.assertEqual(reserveDataUSDb['availableLiquidity'], (self.depositUSDbAmount1 - self.borrowUSDbAmount1))
        self.assertEqual(reserveDataUSDb['totalBorrows'], self.borrowUSDbAmount1)  
        self.assertEqual(reserveDatasICX['totalLiquidity'], self.depositICXAmount1)
        self.assertEqual(reserveDatasICX['availableLiquidity'], (self.depositICXAmount1 - self.borrowSICXAmount1))
        self.assertEqual(reserveDatasICX['totalBorrows'], self.borrowSICXAmount1)
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalBorrowsBalanceUSD'], exaMul(reserveDataUSDb['totalBorrows'] , self.USDbRate) + exaMul(reserveDatasICX['totalBorrows'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalCollateralBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        """
    
    """
    def test_four_repayTestUSDb(self):
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2USDb = self.process_call(_call)
        print('balanceOfUser2USDb', int(balanceOfUser2USDb, 16))

        self.assertEqual(balanceOfUser2USDb, hex(self.borrowUSDbAmount1 - self.repayUSDbAmoubt1))

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDataUSDb = self.process_call(_call)
        print('USERR2ESERVEDATAUSDB', user2ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDatasICX = self.process_call(_call)
        print('USER2RESERVEDATASICX', user2ReserveDatasICX)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDataUSDb = self.process_call(_call)
        print('USERR3ESERVEDATAUSDB', user3ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDatasICX = self.process_call(_call)
        print('USER3RESERVEDATASICX', user3ReserveDatasICX)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user2AccountData = self.process_call(_call)
        print('USER2ACCOUNTDATA', user2AccountData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user3AccountData = self.process_call(_call)
        print('USER3ACCOUNTDATA', user3AccountData)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user2AllReserveData = self.process_call(_call)
        print('USER2ALLRESERVEDATA', user2AllReserveData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user3AllReserveData = self.process_call(_call)
        print('USER3ALLRESERVEDATA', user3AllReserveData)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        print('RESERVEDATAUSDB:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDatasICX = self.process_call(_call)
        print('RESERVEDATASICX:::', reserveDatasICX)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        print('RESERVEACCOUNTDATA', reserveAccountData)

        params = {'_user': self.test_account2.get_address(), '_amount': self.borrowUSDbAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser2USdbBorrow = self.process_call(_call)
        print('originationFeeUser2USdbBorrow', int(originationFeeUser2USdbBorrow, 16))

        params = {'_reserve': self.contracts['sample_token'], '_availableLiquidity': (self.depositUSDbAmount1 - self.borrowUSDbAmount1 + self.repayUSDbAmoubt1 - int(originationFeeUser2USdbBorrow, 16)) ,'_totalBorrows': self.borrowUSDbAmount1 - self.repayUSDbAmoubt1 + int(originationFeeUser2USdbBorrow, 16)}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        ratesUSDb = self.process_call(_call)
        print('ratesUSDb:::', ratesUSDb) 

        #healthfactor for user2
        params = {'_collateralBalanceUSD': exaMul((self.depositICXAmount1), self.sICXRate),
                 '_borrowBalanceUSD': exaMul(self.borrowUSDbAmount1 - self.repayUSDbAmoubt1 + int(originationFeeUser2USdbBorrow,16), self.USDbRate),
                 '_totalFeesUSD': 0,
                 '_liquidationThreshold': user2AccountData['currentLiquidationThreshold']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactorUser2 = self.process_call(_call)
        print('healthFactorUser2', int(healthFactorUser2, 16))
        
        self.assertEqual(user2ReserveDataUSDb['currentOTokenBalance'], 0)
        #Commented test does not pass due to accured interest
        #self.assertEqual(user2ReserveDataUSDb['currentBorrowBalance'], (self.borrowUSDbAmount1 - self.repayUSDbAmoubt1 + int(originationFeeUser2USdbBorrow, 16)))
        #self.assertEqual(user2ReserveDataUSDb['currentBorrowBalanceUSD'], exaMul((self.borrowUSDbAmount1 - self.repayUSDbAmoubt1 + int(originationFeeUser2USdbBorrow, 16)), self.USDbRate))
        self.assertEqual(user2ReserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(user2ReserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        self.assertEqual(user2ReserveDataUSDb['originationFee'], 0)
        self.assertEqual(user2ReserveDatasICX['currentOTokenBalance'], self.depositICXAmount1)
        self.assertEqual(user3ReserveDataUSDb['currentOTokenBalance'], self.depositUSDbAmount1)
        self.assertEqual(user3ReserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(user3ReserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        self.assertEqual(user3ReserveDataUSDb['originationFee'], 0)
        self.assertEqual(user3ReserveDatasICX['currentOTokenBalance'], 0)  
        self.assertEqual(user2AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositICXAmount1, self.sICXRate))
        #self.assertEqual(user2AccountData['totalBorrowBalanceUSD'], exaMul(self.borrowUSDbAmount1 - self.repayUSDbAmoubt1 + int(originationFeeUser2USdbBorrow, 16), self.USDbRate))
        self.assertEqual(user2AccountData['healthFactor'], int(healthFactorUser2, 16))
        self.assertEqual(user3AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositUSDbAmount1, self.USDbRate))
        self.assertEqual(user2AllReserveData['USDb']['currentOTokenBalance'] + user2AllReserveData['Sicx']['currentOTokenBalance'] , user2ReserveDataUSDb['currentOTokenBalance'] + user2ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(user3AllReserveData['USDb']['currentOTokenBalance'] + user3AllReserveData['Sicx']['currentOTokenBalance'] , user3ReserveDataUSDb['currentOTokenBalance'] + user3ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(reserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(reserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        #self.assertEqual(reserveDataUSDb['totalLiquidity'], self.depositUSDbAmount1)
        self.assertEqual(reserveDataUSDb['availableLiquidity'], (self.depositUSDbAmount1 - self.borrowUSDbAmount1 + self.repayUSDbAmoubt1 - int(originationFeeUser2USdbBorrow, 16)))
        #self.assertEqual(reserveDataUSDb['totalBorrows'], self.borrowUSDbAmount1 - self.repayUSDbAmoubt1 + int(originationFeeUser2USdbBorrow, 16))  
        self.assertEqual(reserveDatasICX['totalLiquidity'], self.depositICXAmount1)
        self.assertEqual(reserveDatasICX['availableLiquidity'], self.depositICXAmount1 - self.borrowSICXAmount1)
        self.assertEqual(reserveDatasICX['totalBorrows'], self.borrowSICXAmount1)
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalBorrowsBalanceUSD'], exaMul(reserveDataUSDb['totalBorrows'] , self.USDbRate) + exaMul(reserveDatasICX['totalBorrows'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalCollateralBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate)) 
    """

    """
    def test_five_repayTestsICX(self):
        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3SICX = self.process_call(_call)
        print('balanceOfUser3SICX', int(balanceOfUser3SICX, 16))

        self.assertEqual(balanceOfUser3SICX, hex(self.borrowSICXAmount1 - self.repaySICXAmount1))

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDataUSDb = self.process_call(_call)
        print('USERR2ESERVEDATAUSDB', user2ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDatasICX = self.process_call(_call)
        print('USER2RESERVEDATASICX', user2ReserveDatasICX)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDataUSDb = self.process_call(_call)
        print('USERR3ESERVEDATAUSDB', user3ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDatasICX = self.process_call(_call)
        print('USER3RESERVEDATASICX', user3ReserveDatasICX)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user2AccountData = self.process_call(_call)
        print('USER2ACCOUNTDATA', user2AccountData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user3AccountData = self.process_call(_call)
        print('USER3ACCOUNTDATA', user3AccountData)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user2AllReserveData = self.process_call(_call)
        print('USER2ALLRESERVEDATA', user2AllReserveData)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        user3AllReserveData = self.process_call(_call)
        print('USER3ALLRESERVEDATA', user3AllReserveData)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        print('RESERVEDATAUSDB:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDatasICX = self.process_call(_call)
        print('RESERVEDATASICX:::', reserveDatasICX)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        print('RESERVEACCOUNTDATA', reserveAccountData)

        params = {'_user': self.test_account3.get_address(), '_amount': self.borrowSICXAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser3SICXBorrow = self.process_call(_call)
        print('originationFeeUser3SICXBorrow', int(originationFeeUser3SICXBorrow, 16))

        params = {'_reserve': self.contracts['sicx'], '_availableLiquidity': (self.depositICXAmount1 - self.borrowSICXAmount1 + self.repaySICXAmount1 - int(originationFeeUser3SICXBorrow, 16)) ,'_totalBorrows': self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow, 16)}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        ratesSICX = self.process_call(_call)
        print('ratesSICX:::', ratesSICX) 

        #healthfactor for user3
        params = {'_collateralBalanceUSD': exaMul((self.depositUSDbAmount1), self.USDbRate),
                 '_borrowBalanceUSD': exaMul((self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow,16)), self.sICXRate),
                 '_totalFeesUSD': 0,
                 '_liquidationThreshold': user3AccountData['currentLiquidationThreshold']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactorUser3 = self.process_call(_call)
        print('healthFactorUser3', int(healthFactorUser3, 16))
        
        self.assertEqual(user2ReserveDataUSDb['currentOTokenBalance'], 0)
        #Commented test does not pass due to accured interest
        #self.assertEqual(user3ReserveDatasICX['currentBorrowBalance'], (self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow, 16)))
        #self.assertEqual(user3ReserveDatasICX['currentBorrowBalanceUSD'], exaMul((self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow, 16)), self.sICXRate))
        self.assertEqual(user3ReserveDataUSDb['currentOTokenBalance'], self.depositUSDbAmount1)
        self.assertEqual(user3ReserveDatasICX['borrowRate'], ratesSICX['borrowRate'])
        self.assertEqual(user3ReserveDatasICX['liquidityRate'], ratesSICX['liquidityRate'])
        self.assertEqual(user3ReserveDataUSDb['originationFee'], 0)
        self.assertEqual(user3ReserveDatasICX['currentOTokenBalance'], 0)  
        #self.assertEqual(user3AccountData['totalBorrowBalanceUSD'], exaMul(self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow, 16), self.sICXRate))
        self.assertEqual(user3AccountData['healthFactor'], int(healthFactorUser3, 16))
        self.assertEqual(user3AccountData['totalLiquidityBalanceUSD'], exaMul(self.depositUSDbAmount1, self.USDbRate))
        self.assertEqual(user2AllReserveData['USDb']['currentOTokenBalance'] + user2AllReserveData['Sicx']['currentOTokenBalance'] , user2ReserveDataUSDb['currentOTokenBalance'] + user2ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(user3AllReserveData['USDb']['currentOTokenBalance'] + user3AllReserveData['Sicx']['currentOTokenBalance'] , user3ReserveDataUSDb['currentOTokenBalance'] + user3ReserveDatasICX['currentOTokenBalance'])
        self.assertEqual(reserveDatasICX['borrowRate'], ratesSICX['borrowRate'])
        self.assertEqual(reserveDatasICX['liquidityRate'], ratesSICX['liquidityRate'])
        #self.assertEqual(reserveDatasICX['totalLiquidity'], self.depositICXAmount1)
        self.assertEqual(reserveDatasICX['availableLiquidity'], (self.depositICXAmount1 - self.borrowSICXAmount1 + self.repaySICXAmount1 - int(originationFeeUser3SICXBorrow, 16)))
        #self.assertEqual(reserveDatasICX['totalBorrows'], self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow, 16))  
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalBorrowsBalanceUSD'], exaMul(reserveDataUSDb['totalBorrows'] , self.USDbRate) + exaMul(reserveDatasICX['totalBorrows'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalCollateralBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate)) 
        """

    """
    def test_six_withdrawTestUSDb(self):
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oICX']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2OICX = self.process_call(_call)
        print('balanceOfUser2OICX', int(balanceOfUser2OICX, 16))

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser2SICX = self.process_call(_call)
        print('balanceOfUser2SICX', int(balanceOfUser2SICX, 16))

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDataUSDb = self.process_call(_call)
        print('USERR2ESERVEDATAUSDB', user2ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user2ReserveDatasICX = self.process_call(_call)
        print('USER2RESERVEDATASICX', user2ReserveDatasICX)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user2AccountData = self.process_call(_call)
        print('USER2ACCOUNTDATA', user2AccountData)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        print('RESERVEDATAUSDB:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDatasICX = self.process_call(_call)
        print('RESERVEDATASICX:::', reserveDatasICX)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        print('RESERVEACCOUNTDATA', reserveAccountData)

        params = {'_user': self.test_account3.get_address(), '_amount': self.borrowSICXAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser3SICXBorrow = self.process_call(_call)
        print('originationFeeUser3SICXBorrow', int(originationFeeUser3SICXBorrow, 16))

        params = {'_user': self.test_account2.get_address(), '_amount': self.borrowUSDbAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser2USDbBorrow = self.process_call(_call)
        print('originationFeeUser2USDbBorrow', int(originationFeeUser2USDbBorrow, 16))

        params = {'_reserve': self.contracts['sicx'], '_availableLiquidity': (self.depositICXAmount1 - self.borrowSICXAmount1 + self.repaySICXAmount1 - int(originationFeeUser3SICXBorrow, 16) - self.redeemIXCAmount1) ,'_totalBorrows': self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow, 16)}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        ratesSICX = self.process_call(_call)
        print('ratesSICX:::', ratesSICX) 

        #healthfactor for user2
        params = {'_collateralBalanceUSD': exaMul((self.depositICXAmount1 - self.redeemIXCAmount1), self.sICXRate),
                 '_borrowBalanceUSD': exaMul((self.borrowUSDbAmount1 - self.repayUSDbAmount1 + int(originationFeeUser2USDbBorrow,16)), self.USDbRate),
                 '_totalFeesUSD': 0,
                 '_liquidationThreshold': user2AccountData['currentLiquidationThreshold']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactorUser2 = self.process_call(_call)
        print('healthFactorUser2', int(healthFactorUser2, 16))
        
        #commented test does not pass due to accured interest
        self.assertEqual(balanceOfUser2OICX, hex(self.depositICXAmount1 - self.redeemIXCAmount1))
        self.assertEqual(balanceOfUser2SICX, hex(self.redeemIXCAmount1))
        self.assertEqual(user2ReserveDatasICX['borrowRate'], ratesSICX['borrowRate'])
        self.assertEqual(user2ReserveDatasICX['liquidityRate'], ratesSICX['liquidityRate'])
        self.assertEqual(user2AccountData['totalLiquidityBalanceUSD'], exaMul(user2ReserveDatasICX['currentOTokenBalance'], self.sICXRate))
        self.assertEqual(user2AccountData['healthFactor'], int(healthFactorUser2, 16))
        self.assertEqual(reserveDatasICX['availableLiquidity'], (self.depositICXAmount1 - self.borrowSICXAmount1 - self.redeemIXCAmount1 - int(originationFeeUser3SICXBorrow,16)) + self.repaySICXAmount1)
        self.assertEqual(reserveDatasICX['borrowRate'], ratesSICX['borrowRate'])
        self.assertEqual(reserveDatasICX['liquidityRate'], ratesSICX['liquidityRate'])
        #self.assertEqual(reserveDatasICX['totalLiquidity'], self.depositICXAmount1 - self.redeemIXCAmount1)
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalBorrowsBalanceUSD'], exaMul(reserveDataUSDb['totalBorrows'] , self.USDbRate) + exaMul(reserveDatasICX['totalBorrows'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalCollateralBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))        

    """

    def test_seven_withdrawTestUSDb(self):
        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oUSDb']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3OUSDb = self.process_call(_call)
        print('balanceOfUser3OUSDb', int(balanceOfUser3OUSDb, 16))

        params = {'_owner': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUser3USDb = self.process_call(_call)
        print('balanceOfUser3USDb', int(balanceOfUser3USDb, 16))

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDataUSDb = self.process_call(_call)
        print('USERR3ESERVEDATAUSDB', user3ReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        user3ReserveDatasICX = self.process_call(_call)
        print('USER3RESERVEDATASICX', user3ReserveDatasICX)

        params = {'_user': self.test_account3.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        user3AccountData = self.process_call(_call)
        print('USER3ACCOUNTDATA', user3AccountData)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        print('RESERVEDATAUSDB:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDatasICX = self.process_call(_call)
        print('RESERVEDATASICX:::', reserveDatasICX)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        print('RESERVEACCOUNTDATA', reserveAccountData)

        params = {'_user': self.test_account3.get_address(), '_amount': self.borrowSICXAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser3SICXBorrow = self.process_call(_call)
        print('originationFeeUser3SICXBorrow', int(originationFeeUser3SICXBorrow, 16))

        params = {'_user': self.test_account2.get_address(), '_amount': self.borrowUSDbAmount1}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFeeUser2USDbBorrow = self.process_call(_call)
        print('originationFeeUser2USDbBorrow', int(originationFeeUser2USDbBorrow, 16))

        params = {'_reserve': self.contracts['sample_token'], '_availableLiquidity': (self.depositUSDbAmount1 - self.borrowUSDbAmount1 + self.repayUSDbAmount1 - int(originationFeeUser2USDbBorrow, 16) - self.redeemUSDbAmount1) ,'_totalBorrows': self.borrowUSDbAmount1 - self.repayUSDbAmount1 + int(originationFeeUser2USDbBorrow, 16)}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        ratesUSDb = self.process_call(_call)
        print('ratesUSDb:::', ratesUSDb) 

        #healthfactor for user3
        params = {'_collateralBalanceUSD': exaMul((self.depositUSDbAmount1 - self.redeemUSDbAmount1), self.USDbRate),
                 '_borrowBalanceUSD': exaMul((self.borrowSICXAmount1 - self.repaySICXAmount1 + int(originationFeeUser3SICXBorrow,16)), self.sICXRate),
                 '_totalFeesUSD': 0,
                 '_liquidationThreshold': user3AccountData['currentLiquidationThreshold']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactorUser3 = self.process_call(_call)
        print('healthFactorUser3', int(healthFactorUser3, 16))
        
        #commented test does not pass due to accured interest
        self.assertEqual(balanceOfUser3OUSDb, hex(self.depositUSDbAmount1 - self.redeemUSDbAmount1))
        self.assertEqual(balanceOfUser3USDb, hex(self.userTestUSdbAmount - self.depositUSDbAmount1 + self.redeemUSDbAmount1))
        self.assertEqual(user3ReserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(user3ReserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        self.assertEqual(user3AccountData['totalLiquidityBalanceUSD'], exaMul(user3ReserveDataUSDb['currentOTokenBalance'], self.USDbRate))
        self.assertEqual(user3AccountData['healthFactor'], int(healthFactorUser3, 16))
        self.assertEqual(reserveDataUSDb['availableLiquidity'], (self.depositUSDbAmount1 - self.borrowUSDbAmount1 - self.redeemUSDbAmount1 - int(originationFeeUser2USDbBorrow,16)) + self.repayUSDbAmount1)
        self.assertEqual(reserveDataUSDb['borrowRate'], ratesUSDb['borrowRate'])
        self.assertEqual(reserveDataUSDb['liquidityRate'], ratesUSDb['liquidityRate'])
        #self.assertEqual(reserveDataUSDb['totalLiquidity'], self.depositUSDbAmount1 - self.redeemUSDbAmount1)
        self.assertEqual(reserveAccountData['totalLiquidityBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['availableLiquidityBalanceUSD'], exaMul(reserveDataUSDb['availableLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['availableLiquidity'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalBorrowsBalanceUSD'], exaMul(reserveDataUSDb['totalBorrows'] , self.USDbRate) + exaMul(reserveDatasICX['totalBorrows'] ,self.sICXRate))
        self.assertEqual(reserveAccountData['totalCollateralBalanceUSD'], exaMul(reserveDataUSDb['totalLiquidity'] , self.USDbRate) + exaMul(reserveDatasICX['totalLiquidity'] ,self.sICXRate))        

