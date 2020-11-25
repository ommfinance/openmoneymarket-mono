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

        # Reserve configurations
        self.feePercentage = 25 * 10 ** 14
        self.USDbRate = 1 * 10 ** 18
        self.sIXCRate = 1 * 10 ** 18
        self.liquidationBonus = 10
        self.decimals = 18
        self.baseLTVasCollateral = 6 * 10 ** 17
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
        #Transfer 1 Mill to test_account2
        self.userTestICXAmount = 1000000 * 10 ** 18
        self._transferTestICXToUser(self.userTestICXAmount)
        #test_account2 deposits 50k ICX into sicx reserve
        self.depositICXAmount1 = 50000 * 10 ** 18
        self._depositICX(self.depositICXAmount1)

        #Test Case 2
        #test_account2 withdraws 40k ICX from sicx reserve
        self.withdrawIXCAmount1 = 40000 * 10 ** 18
        self._withdraw(self.withdrawIXCAmount1)

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
                     'params': {'_base': 'Sicx', '_quote': 'USD', '_rate': self.sIXCRate}},

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
                               "baseLTVasCollateral": str(self.baseLTVasCollateral),
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

    def _withdraw(self, _withdrawAmount : int):
        params = {"_amount": _withdrawAmount}
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

    """
    def test_one_checkUserBalance(self):
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUserUSDb = self.process_call(_call)
        print('balanceOfUserUSDb', int(balanceOfUserUSDb, 16))

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUsersICX = self.process_call(_call)
        print('balanceOfUsersICX', int(balanceOfUsersICX, 16))
        #self.assertEqual(int(balanceOfUsersICX, 16), 0)
        #self.assertEqual(int(balanceOfUserUSDb, 16), 0)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveDataUSDb = self.process_call(_call)
        print('userReserveDataUSDb', userReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveDataICX = self.process_call(_call)
        print('userReserveDataICX', userReserveDataICX)

        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataUSDb = self.process_call(_call)
        print('reserveDataUSDb:::', reserveDataUSDb)

        params = {'_reserve': self.contracts['sicx']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveDataICX = self.process_call(_call)
        print('reserveDataICX:::', reserveDataICX)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        userAccountData = self.process_call(_call)
        print('userAccountData', userAccountData)
    """
    
    """
    def test_two_depositTest(self):
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUserUSDb = self.process_call(_call)
        #print('balanceOfUserUSDb', int(balanceOfUserUSDb, 16))

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUsersICX = self.process_call(_call)
        #print('balanceOfUsersICX', int(balanceOfUsersICX, 16))

        self.assertEqual(int(balanceOfUsersICX, 16), 0)
        self.assertEqual(int(balanceOfUserUSDb, 16), 0)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveDataUSDb = self.process_call(_call)
        #print('USERRESERVEDATAUSDB', userReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveDatasICX = self.process_call(_call)
        #print('USERRESERVEDATASICX', userReserveDatasICX)

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

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        userAccountData = self.process_call(_call)
        #print('USERACCOUNTDATA', userAccountData)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        getUserAllReserveData = self.process_call(_call)
        #print('USERALLRESERVEDATA', getUserAllReserveData)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        #print('RESERVEACCOUNTDATA', reserveAccountData)

        self.assertEqual((userReserveDataUSDb['currentOTokenBalance'] + userReserveDatasICX['currentOTokenBalance']), self.depositICXAmount1)
        self.assertEqual((getUserAllReserveData['USDb']['currentOTokenBalance'] + getUserAllReserveData['Sicx']['currentOTokenBalance']),  (userReserveDataUSDb['currentOTokenBalance'] + userReserveDatasICX['currentOTokenBalance']))
        self.assertEqual(exaMul((reserveDatasICX['totalLiquidity'] + reserveDataUSDb['totalLiquidity']), self.sIXCRate), reserveAccountData['totalLiquidityBalanceUSD'])
        self.assertEqual(exaMul((reserveDatasICX['totalBorrows'] + reserveDataUSDb['totalBorrows']), self.sIXCRate), reserveAccountData['totalBorrowsBalanceUSD'])
        """

    def test_three_withdrawTest(self):
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sample_token']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUserUSDb = self.process_call(_call)
        #print('balanceOfUserUSDb', int(balanceOfUserUSDb, 16))

        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['sicx']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        balanceOfUsersICX = self.process_call(_call)
        #print('balanceOfUsersICX', int(balanceOfUsersICX, 16))

        self.assertEqual(int(balanceOfUsersICX, 16), self.withdrawIXCAmount1)
        self.assertEqual(int(balanceOfUserUSDb, 16), 0)

        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveDataUSDb = self.process_call(_call)
        #print('USERRESERVEDATAUSDB', userReserveDataUSDb)

        params = {'_reserve': self.contracts['sicx'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveDatasICX = self.process_call(_call)
        #print('USERRESERVEDATASICX', userReserveDatasICX)

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

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build() 
        userAccountData = self.process_call(_call)
        #print('USERACCOUNTDATA', userAccountData)

        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAllReserveData") \
            .params(params) \
            .build() 
        getUserAllReserveData = self.process_call(_call)
        #print('USERALLRESERVEDATA', getUserAllReserveData)

        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveAccountData") \
            .build() 
        reserveAccountData = self.process_call(_call)
        #print('RESERVEACCOUNTDATA', reserveAccountData)

        self.assertEqual((userReserveDataUSDb['currentOTokenBalance'] + userReserveDatasICX['currentOTokenBalance']), (self.depositICXAmount1 - self.withdrawIXCAmount1))
        self.assertEqual((getUserAllReserveData['USDb']['currentOTokenBalance'] + getUserAllReserveData['Sicx']['currentOTokenBalance']),  (userReserveDataUSDb['currentOTokenBalance'] + userReserveDatasICX['currentOTokenBalance']))
        self.assertEqual(exaMul((reserveDatasICX['totalLiquidity'] + reserveDataUSDb['totalLiquidity']), self.sIXCRate), reserveAccountData['totalLiquidityBalanceUSD'])
        self.assertEqual(exaMul((reserveDatasICX['totalBorrows'] + reserveDataUSDb['totalBorrows']), self.sIXCRate), reserveAccountData['totalBorrowsBalanceUSD'])
