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
        self.initialLiquidityCumulativeIndex = 1 * 10**18

        # deploy SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + address
            self.contracts[address] = self._deploy_score()['scoreAddress']

        self._setVariablesAndInterfaces()
        self.depositAmount = 100 * 10 ** 18
        self._deposit(self.depositAmount)

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

    def _deposit(self, _depositAmount: int):

        # Transferring USdb to  test_account2
        params = {"_to": self.test_account2.get_address(),
                  "_value": 1000 * 10 ** 18}
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

    def test_depositReserveConfigs(self):
        # getting reserve configurations
        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveConfigurationData") \
            .params(params) \
            .build()
        reserveConfigs = self.process_call(_call)
        # print(reserveConfigs)

        # testing and asserting reserve configuration data
        self.assertEqual(reserveConfigs['baseLTVasCollateral'], self.baseLTVasCollateral)
        self.assertEqual(reserveConfigs['liquidationThreshold'], self.liquidationThreshold)
        self.assertEqual(reserveConfigs['usageAsCollateralEnabled'], True)
        self.assertEqual(reserveConfigs['borrowingEnabled'], True)
        self.assertEqual(reserveConfigs['isActive'], True)
        self.assertEqual(reserveConfigs['liquidationBonus'], self.liquidationBonus)

    def test_depositReserveData(self):
        # getting reserve data
        params = {'_reserve': self.contracts['sample_token']}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getReserveData") \
            .params(params) \
            .build()
        reserveData = self.process_call(_call)

        # testing and asserting reserve data
        self.assertEqual(str(reserveData['reserveAddress']), self.contracts['sample_token'])
        self.assertEqual(str(reserveData['oTokenAddress']), self.contracts['oToken'])
        self.assertEqual(reserveData['totalBorrows'], 0)
        self.assertEqual(reserveData['liquidityRate'], 0)
        self.assertEqual(reserveData['borrowRate'], self.initialBorrowRate)
        self.assertEqual(reserveData['liquidityCumulativeIndex'], self.initialLiquidityCumulativeIndex)
        self.assertEqual(reserveData['baseLTVasCollateral'], self.baseLTVasCollateral)
        self.assertEqual(reserveData['liquidationThreshold'], self.liquidationThreshold)
        self.assertEqual(reserveData['liquidationBonus'], self.liquidationBonus)
        self.assertEqual(reserveData['decimals'], self.decimals)
        self.assertEqual(reserveData['borrowingEnabled'], True)
        self.assertEqual(reserveData['usageAsCollateralEnabled'], True)
        self.assertEqual(reserveData['isFreezed'], False)
        self.assertEqual(reserveData['isActive'], True)
        self.assertEqual(reserveData['totalLiquidity'], self.depositAmount)
        self.assertEqual(reserveData['availableLiquidity'], self.depositAmount)

    def test_depositUserReserveData(self):
        # getting user data for reserve 
        params = {'_reserve': self.contracts['sample_token'], '_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserReserveData") \
            .params(params) \
            .build()
        userReserveData = self.process_call(_call)

        # getting price of USDb from oracle
        params = {'_base': 'USDb', '_quote': 'USD'}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['priceOracle']) \
            .method("get_reference_data") \
            .params(params) \
            .build()
        price = int(self.process_call(_call), 0)
        self.assertEqual(price, self.USDbRate)

        # getting oToken balance of the user
        params = {'_owner': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['oToken']) \
            .method("balanceOf") \
            .params(params) \
            .build()
        oTokenBalance = int(self.process_call(_call), 0)
        self.assertEqual(oTokenBalance, self.depositAmount)

        # testing and asserting user data for reserve

        self.assertEqual(userReserveData['currentOTokenBalance'], oTokenBalance)
        self.assertEqual(userReserveData['currentOTokenBalanceUSD'],exaMul(userReserveData['currentOTokenBalance'], price))
        self.assertEqual(userReserveData['currentBorrowBalance'], 0)
        self.assertEqual(userReserveData['currentBorrowBalanceUSD'],exaMul(userReserveData['currentBorrowBalance'], price))
        self.assertEqual(userReserveData['principalBorrowBalance'], 0)
        self.assertEqual(userReserveData['principalBorrowBalanceUSD'],exaMul(userReserveData['principalBorrowBalance'], price))
        self.assertEqual(userReserveData['liquidityRate'], 0)
        self.assertEqual(userReserveData['borrowRate'], self.initialBorrowRate)
        self.assertEqual(userReserveData['originationFee'], 0)
        self.assertEqual(userReserveData['userBorrowCumulativeIndex'], 0)
        self.assertEqual(userReserveData['lastUpdateTimestamp'], 0)
        self.assertEqual(userReserveData['useAsCollateral'], True)

    def test_userAllReserveData(self):
        # getting user account data (data for all reserves)
        params = {'_user': self.test_account2.get_address()}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['lendingPoolDataProvider']) \
            .method("getUserAccountData") \
            .params(params) \
            .build()
        userAccountData = self.process_call(_call)
        print(userAccountData)

        # testing and asserting user data for  all reserves

        self.assertEqual(userAccountData['totalLiquidityBalanceUSD'], exaMul(self.depositAmount, self.USDbRate))
        self.assertEqual(userAccountData['totalCollateralBalanceUSD'], exaMul(self.depositAmount, self.USDbRate))
        self.assertEqual(userAccountData['totalBorrowBalanceUSD'], 0)
        self.assertEqual(userAccountData['totalFeesUSD'], 0)
        self.assertEqual(userAccountData['currentLtv'], self.baseLTVasCollateral)
        self.assertEqual(userAccountData['healthFactor'], -1)
        self.assertEqual(userAccountData['healthFactorBelowThreshold'], False)

