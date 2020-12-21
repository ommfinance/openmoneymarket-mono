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
        # Reserve configurations 18181818181818181818 868181818181818181818 1000000000000000000000
        self.feePercentage = 1 * 10 ** 16
        self.USDbRate = 1 * 10 ** 18
        self.sICXRate = 5 * 10 ** 17
        self.ICXRate = 1 * 10 ** 18
        self.liquidationBonus = 1 *10 ** 17
        self.decimals = 18
        self.baseLTVasCollateralICX = 33 * 10 ** 16
        self.baseLTVasCollateralUSDb = 33 * 10 ** 16
        self.liquidationThreshold = 66 * 10 ** 16 

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
        #Transfer 500k ICX to test_account2
        self.userTestICXAmount = 500000 * 10 ** 18
        self._transferTestICXToUser(self.userTestICXAmount, self.test_account2.get_address()) 

        #Trasnfer 1 Mill USDb to test_account3
        self.userTestUSdbAmount = 1000000 * 10 ** 18
        self._transferTestUSDbToUser(self.userTestUSdbAmount, self.test_account3.get_address())

        #test_account2 deposits 1000 ICX into sicx reserve
        self.depositICXAmount1 = 1000 * 10 ** 18 
        self._depositICX(self.depositICXAmount1, self.test_account2)

        #test_account3 deposits 1000 USDb into usdb reserve i.e sample_token        
        self.depositUSDbAmount1 = 1000 * 10 ** 18
        self._depositUSDb(self.depositUSDbAmount1, self.test_account3)

        #Test Case2
        #test_account2 borrows 150 USDb from usdb reserve i.e sample_token        
        self.borrowUSDBAmount1 = 150 * 10 ** 18 
        self._borrowUSDb(self.borrowUSDBAmount1, self.test_account2)

        #self.liquidationCall() #user cannot get liquidated 
        #Test Case3 
        #reduce icxUSD rate  
        #self.sICXRate = 15 * 10 ** 16
        #self.sICXRate = 37 * 10 ** 16
        self._changeOraclePriceFeed() 
        #time.sleep(1)
        #test_account3 pays off 1k loan from user2  
        self.loanPayoffAmount = 100 * 10 ** 18 
        self._liquidationCall(self.loanPayoffAmount, self.test_account2, self.test_account3) 

    def _changeOraclePriceFeed(self):
        settings = [{'contract': 'priceOracle', 'method': 'set_reference_data',
                     'params': {'_base': 'Sicx', '_quote': 'USD', '_rate': 2 * 10 ** 17}}]
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

    def _transferTestICXToUser(self, _testFund: int, _user):
        # Transferring 100k ICX to  test_account2
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

    def _transferTestUSDbToUser(self, _testFund: int, _user):
        # Transferring 1 Mill USdb to  test_account3
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

    def _depositICX(self, _depositAmount: int, _user):
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

    def _depositUSDb(self, _depositAmount: int, _user):
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

    def _borrowUSDb(self, _borrowAmount : int, _user):
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
    def _liquidationCall(self, _loanPayoffAmount : int, _borrowerUser : KeyWallet, _liquidatorUser : KeyWallet) :

        print('user2Data', self.getUserAccountData(_borrowerUser.get_address())) 
        print('_liquidatorUserInitial sicx amount', self.getUserSICXBalance(_liquidatorUser.get_address()))
        print('usdb reserve available liquidity before', self.getReserveData(self.contracts['sample_token'])['availableLiquidity'])
        print('before liquidation', self.getUserAccountData(self.test_account2.get_address()))
        liquidityUSDbbefore = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('user3 usdb balance before', self.getUserUSDbBalance(self.test_account3.get_address()))
        print('oICX balance of user2 before i.e borrower', self.getUserOICXBalance(self.test_account2.get_address()))

        print('calling liquidaitonCall')
        depositData = {'method': 'liquidationCall', 'params': 
            {'_collateral': self.contracts['sicx'],
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
        print('_liquidatorUser sicx amount after liquidation', self.getUserSICXBalance(_liquidatorUser.get_address()) )
        print('usdb reserve available liquidity after liquidation', self.getReserveData(self.contracts['sample_token'])['availableLiquidity'])
        liquidityUSDbafter = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('change in liquidity is', liquidityUSDbafter - liquidityUSDbbefore)
        print(self.getReserveData(self.contracts['sample_token']))
        print('after liquidation', self.getUserAccountData(self.test_account2.get_address()))
        print('user3 usdb balance after', self.getUserUSDbBalance(self.test_account3.get_address()))
        print('oICX balance of user2 i.e borrower', self.getUserOICXBalance(self.test_account2.get_address()))
        print('oICX balance of user3 ', self.getUserOICXBalance(self.test_account3.get_address()))

    """
    def functionCallExample(self):

        balanceOfUserUSDb = self.getUserUSDbBalance(self.test_account3.get_address())
        #print('getUserUSDbBalance', balanceOfUserUSDb)

        balanceOfUserOUSDb = self.getUserOUSDbBalance(self.test_account3.get_address())
        #print('getUserOUSDbBalance', balanceOfUserOUSDb)

        balanceOfUserOICX = self.getUserOICXBalance(self.test_account2.get_address())
        #print('getUserOICXBalance', balanceOfUserOICX)

        balanceOfUserSICX = self.getUserSICXBalance(self.test_account3.get_address())
        #print('getUserSICXBalance', balanceOfUserSICX) 

        userReserveDataUSDb = self.getUserReserveData(self.contracts['sample_token'], self.test_account2.get_address())
        #print('user2ReserveDataUSDb', userReserveDataUSDb)

        userReserveDataSICX = self.getUserReserveData(self.contracts['sicx'], self.test_account2.get_address())
        #print('user2ReserveDataSICX', userReserveDataSICX)

        userReserveDataUSDb = self.getUserReserveData(self.contracts['sample_token'], self.test_account3.get_address())
        #print('user3ReserveDataUSDb', userReserveDataUSDb)

        userReserveDataSICX = self.getUserReserveData(self.contracts['sicx'], self.test_account3.get_address())
        #print('user3ReserveDataSICX', userReserveDataSICX)

        user2AccountData = self.getUserAccountData(self.test_account2.get_address())
        print('user2AccountData',user2AccountData)

        user3AccountData = self.getUserAccountData(self.test_account3.get_address())
        print('user3AccountData',user3AccountData)

        user2AllReserveData = self.getUserAllReserveData(self.test_account2.get_address())
        #print('user2AllReserveData',user2AllReserveData)

        user3AllReserveData = self.getUserAllReserveData(self.test_account3.get_address())
        #print('user3AllReserveData',user3AllReserveData)

        usdbReserveData = self.getReserveData(self.contracts['sample_token'])
        #print('usdbReserveData', usdbReserveData)

        sicxReserveData = self.getReserveData(self.contracts['sicx'])
        #print('sicxReserveData', sicxReserveData)

        reserveAccountData = self.getReserveAccountData()
        #print('reserveAccountData',reserveAccountData)

        user2OGFee = self.calculateOriginationFee(self.borrowUSDbAmount1, self.test_account2.get_address())
        #print('user2OGFee',user2OGFee)

        user3OGFee = self.calculateOriginationFee(self.borrowSICXAmount1, self.test_account3.get_address())
        #print('user3OGFee',user3OGFee)

        usdbReserveRate = self.calculateInterestRates(self.contracts['sample_token'], self.depositUSDbAmount1 - self.borrowUSDbAmount1, self.borrowUSDbAmount1)
        #print('usdbReserveRate', usdbReserveRate)

        sicxReserveRate = self.calculateInterestRates(self.contracts['sicx'], self.depositICXAmount1 - self.borrowSICXAmount1, self.borrowSICXAmount1)
        #print('sicxReserveRate', sicxReserveRate)

        healthFactorUser2 = self.calculateHealthFactor(
            exaMul(self.depositICXAmount1, self.sICXRate),
            exaMul(self.borrowUSDbAmount1, self.USDbRate),
            exaMul(user2OGFee, self.USDbRate),
            self.liquidationThreshold
        )
        print('healthFactorUser2',healthFactorUser2)
        
        healthFactorUser3 = self.calculateHealthFactor(
            exaMul(self.depositUSDbAmount1, self.USDbRate),
            exaMul(self.borrowSICXAmount1, self.sICXRate),
            exaMul(user3OGFee, self.sICXRate),
            self.liquidationThreshold
        )
        print('healthFactorUser3',healthFactorUser3)

        borrowingPowerUser2 = self.calculateBorrowingPower(
            exaMul(self.depositICXAmount1, self.sICXRate),
            exaMul(self.borrowUSDbAmount1, self.USDbRate),
            exaMul(user2OGFee, self.USDbRate),
            self.liquidationThreshold
        )
        print('borrowingPowerUser2',borrowingPowerUser2)
        
        borrowingPowerUser3 = self.calculateBorrowingPower(
            exaMul(self.depositUSDbAmount1, self.USDbRate),
            exaMul(self.borrowSICXAmount1, self.sICXRate),
            exaMul(user3OGFee, self.sICXRate),
            self.liquidationThreshold
        )
        print('borrowingPowerUser3',borrowingPowerUser3)
    """
    """
    def test_oneinitTest(self):
        userUSDbBalance = self.getUserUSDbBalance(self.test_account2.get_address())

        usdbReserveData = self.getReserveData(self.contracts['sample_token'])
        print('usdbReserveData', usdbReserveData)

        sicxReserveData = self.getReserveData(self.contracts['sicx'])
        print('sicxReserveData', sicxReserveData)

        user2AccountData = self.getUserAccountData(self.test_account2.get_address())
        print('user2AccountData',user2AccountData)

        user3AccountData = self.getUserAccountData(self.test_account3.get_address())
        print('user3AccountData',user3AccountData)

        self.assertEqual(userUSDbBalance, self.borrowUSDBAmount1)
    """
        
        

    