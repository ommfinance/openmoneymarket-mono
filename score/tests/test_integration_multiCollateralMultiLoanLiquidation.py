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
from iconservice import *

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
DEPLOY = ['addressProvider', 'feeProvider', 'lendingPool', 'lendingPoolCore',
          'lendingPoolDataProvider', 'priceOracle', 'sample_token', 'sicx', 'liquidationManager']


class TestIntegrationDepositUSDb(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"

    SCORES = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()
        self.contracts = {}
        self.icon_service = None
        self.test_account2 = KeyWallet.create()
        self.test_account3 = KeyWallet.create()
        self.test_account4 = KeyWallet.create()
        self.test_account5 = KeyWallet.create()
        # Reserve configurations
        self.feePercentage = 1 * 10 ** 16
        self.USDbRate = 1 * 10 ** 18
        self.sICXRate = 5 * 10 ** 17
        self.ICXRate = 1 * 10 ** 18
        self.liquidationBonus = 1 *10 ** 17
        self.decimals = 18
        self.baseLTVasCollateralICX = 33 * 10 ** 16
        self.baseLTVasCollateralUSDb = 33 * 10 ** 16
        self.liquidationThreshold = 50 * 10 ** 16 

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
        #Transfer 100k ICX to test_account2
        self.userTestICXAmountUser2 = 100000 * 10 ** 18
        self._transferTestICXToUser(self.userTestICXAmountUser2, self.test_account2.get_address()) 

        #Transfer 100k ICX to test_account3
        self.userTestICXAmountUser3 = 100000 * 10 ** 18
        self._transferTestICXToUser(self.userTestICXAmountUser3, self.test_account3.get_address()) 

        #Transfer 100k ICX to test_account4
        self.userTestICXAmountUser4 = 100000 * 10 ** 18
        self._transferTestICXToUser(self.userTestICXAmountUser4, self.test_account4.get_address()) 

        #Transfer 200k ICX to test_account5
        self.userTestICXAmountUser5 = 200000 * 10 ** 18
        self._transferTestICXToUser(self.userTestICXAmountUser5, self.test_account5.get_address()) 

        #Trasnfer 500k USDb to test_account2
        self.userTestUSdbAmountUser2 = 500000 * 10 ** 18
        self._transferTestUSDbToUser(self.userTestUSdbAmountUser2, self.test_account2.get_address())

        #Trasnfer 600k USDb to test_account3
        self.userTestUSdbAmountUser3 = 600000 * 10 ** 18
        self._transferTestUSDbToUser(self.userTestUSdbAmountUser3, self.test_account3.get_address())

        #transfer sicx to test_account3
        self.userTestSICXAmountUser3 = 100000 * 10 ** 18
        self._transferTestSICXToUser(self.userTestSICXAmountUser3, self.test_account3.get_address())

        #transfer sicx to test_account5
        self.userTestSICXAmountUser5 = 200 * 10 ** 18
        self._transferTestSICXToUser(self.userTestSICXAmountUser5, self.test_account5.get_address())

        #Trasnfer 200k USDb to test_account4
        self.userTestUSdbAmountUser4 = 200000 * 10 ** 18
        self._transferTestUSDbToUser(self.userTestUSdbAmountUser4, self.test_account4.get_address())

        #Trasnfer 300k USDb to test_account5
        self.userTestUSdbAmountUser5 = 300000 * 10 ** 18
        self._transferTestUSDbToUser(self.userTestUSdbAmountUser5, self.test_account5.get_address())

        #test_account4 deposits 200 USDb into usdb reserve i.e sample_token        
        self.depositUSDbAmountUser4 = 200 * 10 ** 18
        self._depositUSDb(self.depositUSDbAmountUser4, self.test_account4)

        #test_account5 deposits 400 USDb into usdb reserve i.e sample_token        
        self.depositUSDbAmountUser5 = 400 * 10 ** 18
        self._depositUSDb(self.depositUSDbAmountUser5, self.test_account5)

        #test_account4 deposits 500 ICX into sicx reserve
        self.depositICXAmountUser4 = 500 * 10 ** 18 
        self._depositICX(self.depositICXAmountUser4, self.test_account4)

        #test_account5 deposits 800 ICX into sicx reserve
        self.depositICXAmountUser5 = 800 * 10 ** 18 
        self._depositICX(self.depositICXAmountUser5, self.test_account5)

        #test_account4 borrows USDb from usdb reserve i.e sample_token        
        self.borrowUSDBAmountUser4 = 137 * 10 ** 18 
        self._borrowUSDb(self.borrowUSDBAmountUser4, self.test_account4)

        #test_account5 borrows USDb from usdb reserve i.e sample_token        
        self.borrowUSDBAmountUser5 = 210 * 10 ** 18 
        self._borrowUSDb(self.borrowUSDBAmountUser5, self.test_account5)

        #test_account4 borrows ICX         
        self.borrowICXAmountUser4 = 20 * 10 ** 18 
        self._borrowSICX(self.borrowICXAmountUser4, self.test_account4)

        #test_account5 borrows ICX       
        self.borrowICXAmountUser5 = 20 * 10 ** 18 
        self._borrowSICX(self.borrowICXAmountUser5, self.test_account5)
        
        #reduce icxUSD rate  
        self.sICXRate = 15 * 10 ** 16
        self._changeOraclePriceFeed(self.sICXRate) 
        #test_account2 pays off 21 USDb loan from user4 
        #unable to trigger liquidation for user 5 as healthfactor >1 
        self.loanPayoffAmountUser4 = 40 * 10 ** 18 
        self._liquidationCallUSDbRepay(self.loanPayoffAmountUser4, self.test_account4, self.test_account2) 
        
        self.sICXRate = 2 * 10 ** 16
        self._changeOraclePriceFeed(self.sICXRate)
        #test_account3 pays off ICX loan from user5
        self.loanPayoffAmountUser5 = 1 * 10 ** 18 
        self._liquidationCallICXRepay(self.loanPayoffAmountUser5, self.test_account5, self.test_account3) 
        
    def _changeOraclePriceFeed(self, sICXRate: int):
        settings = [{'contract': 'priceOracle', 'method': 'set_reference_data',
                     'params': {'_base': 'Sicx', '_quote': 'USD', '_rate': sICXRate}}]
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

    def _setVariablesAndInterfaces(self):
        settings = [{'contract': 'lendingPool', 'method': 'setLendingPoolCoreAddress',
                     'params': {'_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'lendingPool', 'method': 'setUSDbAddress',
                     'params': {'_address': (self.contracts['sample_token'])}},

                    {'contract': 'lendingPool', 'method': 'setSICXAddress',
                     'params': {'_address': (self.contracts['sicx'])}},

                    {'contract': 'lendingPool', 'method': 'setLiquidationManagerAddress',
                     'params': {'_address': self.contracts['liquidationManager']}},

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

                    {'contract': 'liquidationManager', 'method': 'setDataProviderAddress', 'params': {
                        '_address': self.contracts['lendingPoolDataProvider']}},
                    {'contract': 'liquidationManager', 'method': 'setCoreAddress', 'params': {
                        '_address': self.contracts['lendingPoolCore']}},
                    {'contract': 'liquidationManager', 'method': 'setOracleAddress',
                     'params': {'_address': self.contracts['priceOracle']}},
                    {'contract': 'liquidationManager', 'method': 'setFeeProviderAddress',
                     'params': {'_address': self.contracts['feeProvider']}},

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

    def _transferTestICXToUser(self, _testFund: int, _user : KeyWallet):
        transaction = TransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(_user) \
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

    def _transferTestUSDbToUser(self, _testFund: int, _user : KeyWallet):
        params = {"_to": _user,"_value": _testFund}
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

    def _transferTestSICXToUser(self, _testFund: int, _user : KeyWallet):
        params = {"_to": _user,"_value": _testFund}
        call_transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
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

    def _depositICX(self, _depositAmount: int, _user : KeyWallet):
        # calling deposit from test_account2
        params = {"_amount": _depositAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(_user.get_address()) \
            .to(self.contracts['lendingPool']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .value(_depositAmount) \
            .method("deposit") \
            .params(params) \
            .build() 

        signed_transaction = SignedTransaction(
            call_transaction, _user)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _depositUSDb(self, _depositAmount: int, _user : KeyWallet):
        depositData = {'method': 'deposit', 'params': {'amount': _depositAmount}}
        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _depositAmount, "_data": data}
        call_transaction = CallTransactionBuilder() \
            .from_(_user.get_address()) \
            .to(self.contracts['sample_token']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, _user)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _borrowUSDb(self, _borrowAmount : int, _user : KeyWallet):
        params = {"_reserve": self.contracts['sample_token'], "_amount": _borrowAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(_user.get_address()) \
            .to(self.contracts['lendingPool']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("borrow") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, _user)
        tx_result = self.process_transaction(signed_transaction)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('status' in tx_result)

    def _borrowSICX(self, _borrowAmount : int, _user : KeyWallet):
        params = {"_reserve": self.contracts['sicx'], "_amount": _borrowAmount}
        call_transaction = CallTransactionBuilder() \
            .from_(_user.get_address()) \
            .to(self.contracts['lendingPool']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("borrow") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, _user)
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
    
    #FUNCTIONS
    def getUserUSDbBalance(self, _address):
        params = {'_owner': _address}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUserUSDb = self.process_call(_call)
        #print('balanceOfUserUSDb', int(balanceOfUserUSDb, 16))
        return int(balanceOfUserUSDb, 16)

    def getUserOUSDbBalance(self, _address):
        params = {'_owner': _address}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oUSDb']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUserOUSDb = self.process_call(_call)
        #print('balanceOfUserOUSDb', int(balanceOfUserOUSDb, 16))
        return int(balanceOfUserOUSDb, 16)

    def getUserOICXBalance(self, _address):
        params = {'_owner': _address}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oICX']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUserOICX = self.process_call(_call)
        #print('balanceOfUserOUSDb', int(balanceOfUserOUSDb, 16))
        return int(balanceOfUserOICX, 16)

    def getUserSICXBalance(self, _address):
        params = {'_owner': _address}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUserSICX = self.process_call(_call)
        #print('balanceOfUserOUSDb', int(balanceOfUserOUSDb, 16))
        return int(balanceOfUserSICX, 16)

    def getUserReserveData(self, _reserve, _address):
        params = {'_reserve': _reserve, '_user': _address}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveData = self.process_call(_call)
        #print('userReserveData', userReserveData)
        return userReserveData

    def getUserAccountData(self, _address):
        params = {'_user': _address}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        userAccountData = self.process_call(_call)
        #print('userAccountData', userAccountData)
        return userAccountData

    def getUserAllReserveData(self, _address):
        params = {'_user': _address}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        getUserAllReserveData = self.process_call(_call)
        #print('userAllReserveData', getUserAllReserveData)
        return getUserAllReserveData

    def getReserveData(self, _reserve):
        params = {'_reserve': _reserve}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveData = self.process_call(_call)
        #print('reserveData', reserveData)
        return reserveData

    def getReserveAccountData(self):
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        #print('RESERVEACCOUNTDATA', reserveAccountData)
        return reserveAccountData

    def calculateOriginationFee(self, _borrowAmount: int, _user):
        params = {'_user': _user, '_amount': _borrowAmount}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['feeProvider']) \
            .method("calculateOriginationFee") \
            .params(params) \
            .build()
        originationFee = self.process_call(_call)
        #print('originationFee', int(originationFee, 16))
        return int(originationFee, 16)

    def calculateInterestRates(self, _reserve, _availableLiquidity, _totalBorrows):
        params = {'_reserve': _reserve, '_availableLiquidity': _availableLiquidity ,'_totalBorrows': _totalBorrows}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolCore']) \
            .method("calculateInterestRates") \
            .params(params) \
            .build()
        rates = self.process_call(_call)
        #print('rates', rates) 
        return rates

    def calculateHealthFactor(self, _collateralBalanceUSD, _borrowBalanceUSD, _totalFeesUSD, _liquidationThreshold):
        params = {'_collateralBalanceUSD': _collateralBalanceUSD,
                 '_borrowBalanceUSD': _borrowBalanceUSD,
                 '_totalFeesUSD': _totalFeesUSD,
                 '_liquidationThreshold': _liquidationThreshold}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateHealthFactorFromBalancesInternal") \
            .params(params) \
            .build()
        healthFactor = self.process_call(_call)
        #print('healthFactor', int(healthFactor, 16))
        return int(healthFactor, 16)
        
    def calculateBorrowingPower(self, _collateralBalanceUSD, _borrowBalanceUSD, _totalFeesUSD, _ltv):
        params = {'_collateralBalanceUSD': _collateralBalanceUSD,
                 '_borrowBalanceUSD': _borrowBalanceUSD,
                 '_totalFeesUSD': _totalFeesUSD,
                 '_ltv': _ltv}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("calculateBorrowingPowerFromBalancesInternal") \
            .params(params) \
            .build()
        borrowingPower = self.process_call(_call)
        #print('borrowingPower', int(borrowingPower, 16))
        return int(borrowingPower, 16)
    
    #def liquidationCall(self, _collateral, _reserve, _user, _purchaseAmount):
    def _liquidationCallUSDbRepay(self, _loanPayoffAmount : int, _borrowerUser : KeyWallet, _liquidatorUser : KeyWallet) :
        print('----------------')
        print('borrowerUserDataBeforeLiquidation::', self.getUserAccountData(_borrowerUser.get_address())) 
        print('_liquidatorUserInitial sicx amount', self.getUserSICXBalance(_liquidatorUser.get_address())/10**18)
        print('_liquidatorUser usdb balance before', self.getUserUSDbBalance(_liquidatorUser.get_address())/10**18)
        print('usdb reserve before', self.getReserveData(self.contracts['sample_token']))
        liquidityUSDbbefore = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('oICX balance of borrower before ', self.getUserOICXBalance(_borrowerUser.get_address())/10**18)
        print('oUSDb balance of borrower before ', self.getUserOUSDbBalance(_borrowerUser.get_address())/10**18)
        print('calling liquidaitonCall')
        depositData = {'method': 'liquidationCall', 'params': 
            {'_collateral': self.contracts['sample_token'],
            '_reserve': self.contracts['sample_token'],
            '_user': _borrowerUser.get_address(),
            '_purchaseAmount': _loanPayoffAmount}}
        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _loanPayoffAmount, "_data": data}
        call_transaction = CallTransactionBuilder() \
            .from_(_liquidatorUser.get_address()) \
            .to(self.contracts['sample_token']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, _liquidatorUser)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        print('borrowerUserDataAfterLiquidation::', self.getUserAccountData(_borrowerUser.get_address())) 
        print('_liquidatorUser sicx amount after liquidation', (self.getUserSICXBalance(_liquidatorUser.get_address())/10**18) )
        print('_liquidatorUser usdb balance after', self.getUserUSDbBalance(_liquidatorUser.get_address())/10**18)
        print('usdb reserve after liquidation', self.getReserveData(self.contracts['sample_token']))
        liquidityUSDbafter = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('change in liquidity is', (liquidityUSDbafter - liquidityUSDbbefore)/10**18)
        print('oICX balance of  borrower after', self.getUserOICXBalance(_borrowerUser.get_address())/10**18)
        print('oUSDb balance of borrower after ', self.getUserOUSDbBalance(_borrowerUser.get_address())/10**18)
        
    def _liquidationCallICXRepay(self, _loanPayoffAmount : int, _borrowerUser : KeyWallet, _liquidatorUser : KeyWallet) :
        print('----------------')
        print('borrowerUserDataBeforeLiquidation::', self.getUserAccountData(_borrowerUser.get_address())) 
        print('_liquidatorUserInitial sicx amount', self.getUserSICXBalance(_liquidatorUser.get_address())/10**18)
        print('_liquidatorUser usdb balance before', self.getUserUSDbBalance(_liquidatorUser.get_address())/10**18)
        print('sicx reserve before', self.getReserveData(self.contracts['sicx']))
        liquidityUSDbbefore = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('oICX balance of borrower before ', self.getUserOICXBalance(_borrowerUser.get_address())/10**18)
        print('oUSDb balance of borrower before ', self.getUserOUSDbBalance(_borrowerUser.get_address())/10**18)
        print('calling liquidaitonCall')
        depositData = {'method': 'liquidationCall', 'params': 
            {'_collateral': self.contracts['sicx'],
            '_reserve': self.contracts['sicx'],
            '_user': _borrowerUser.get_address(),
            '_purchaseAmount': _loanPayoffAmount}}
        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _loanPayoffAmount, "_data": data}
        call_transaction = CallTransactionBuilder() \
            .from_(_liquidatorUser.get_address()) \
            .to(self.contracts['sicx']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(
            call_transaction, _liquidatorUser)
        tx_result = self.process_transaction(signed_transaction)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        print('borrowerUserDataAfterLiquidation::', self.getUserAccountData(_borrowerUser.get_address())) 
        print('_liquidatorUser sicx amount after liquidation', (self.getUserSICXBalance(_liquidatorUser.get_address())/10**18) )
        print('_liquidatorUser usdb balance after', self.getUserUSDbBalance(_liquidatorUser.get_address())/10**18)
        print('sicx reserve after', self.getReserveData(self.contracts['sicx']))
        liquidityUSDbafter = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('change in liquidity is', (liquidityUSDbafter - liquidityUSDbbefore)/10**18)
        print('oICX balance of  borrower after', self.getUserOICXBalance(_borrowerUser.get_address())/10**18)
        print('oUSDb balance of borrower after ', self.getUserOUSDbBalance(_borrowerUser.get_address())/10**18)
        