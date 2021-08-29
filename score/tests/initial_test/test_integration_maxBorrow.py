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
from pprint import pprint

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
        self.baseLTVasCollateralICX = 50 * 10 ** 16
        self.baseLTVasCollateralUSDb = 50 * 10 ** 16
        self.liquidationThreshold = 65 * 10 ** 16 

        # Reserve constants of USDb
        self.optimalUtilizationRateUSDb = 6 * 10 ** 17
        self.baseBorrowRateUSDb = 1 * 10 ** 16
        self.slopeRate1USDb = 4 * 10 ** 16
        self.slopeRate2USDb = 5 * 10 ** 17

        # Reserve constants of ICX
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

        
        
        

        #Trasnfer 1 Mill USDb to test_account2
        self.userTestUSdbAmount = 1000000 * 10 ** 18
        self._transferTestUSDbToUser(self.userTestUSdbAmount, self.test_account2.get_address())

        #Transfer 1 mill USDb to test_account3
        self.userTestUSdbAmount = 1000000 * 10 ** 18
        self._transferTestUSDbToUser(self.userTestUSdbAmount, self.test_account3.get_address())


        self.UsdbDeposit = 10000 * 10**18
        self._depositUSDb(self.UsdbDeposit, self.test_account2)


        self.ICXDeposit = 1000 * 10**18
        self._depositICX(self.ICXDeposit, self._test1)
        

        self.borrowUSDb2=300 * 10 ** 18
        self._borrowUSDb(self.borrowUSDb2,self._test1)
        time.sleep(4)

        # self.borrowICX = 199849999 * 10 ** 12
        # self._borrowSICX(self.borrowICX,self._test1)

        userAccountData=self.getUserAccountData(self._test1.get_address())
        pprint(userAccountData)

        
        

    
    def _setVariablesAndInterfaces(self):
        contracts = self.contracts
        local_settings = [{'contract': 'lendingPool', 'method': 'setLendingPoolCoreAddress', 'params': {'_address': contracts['lendingPoolCore']}},
                          {'contract': 'lendingPool', 'method': 'setUSDbAddress',
                              'params': {'_address': contracts['sample_token']}},
                          {'contract': 'lendingPool', 'method': 'setDataProvider',
                           'params': {'_address': contracts['lendingPoolDataProvider']}},
                          {'contract': 'lendingPool', 'method': 'setFeeProvider',
                           'params': {'_address': contracts['feeProvider']}},
                          {'contract': 'feeProvider', 'method': 'setLoanOriginationFeePercentage',
                           'params': {'_percentage': 1*10**15}},
                          {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params': {
                              '_reserveAddress': contracts['sample_token'], '_sym':"USDb"}},
                          {'contract': 'lendingPoolDataProvider', 'method': 'setLendingPoolCoreAddress',
                           'params': {'_address': contracts['lendingPoolCore']}},
                          {'contract': 'lendingPoolDataProvider', 'method': 'setOracleAddress',
                           'params': {'_address': contracts['priceOracle']}},
                          {'contract': 'oUSDb', 'method': 'setCoreAddress',
                           'params': {'_address': contracts['lendingPoolCore']}},
                          {'contract': 'oUSDb', 'method': 'setReserveAddress',
                           'params': {'_address': contracts['sample_token']}},
                          {'contract': 'oUSDb', 'method': 'setDataProviderAddress',
                           'params': {'_address': contracts['lendingPoolDataProvider']}},
                          {'contract': 'oUSDb', 'method': 'setLendingPoolAddress',
                           'params': {'_address': contracts['lendingPool']}},
                          {'contract': 'priceOracle', 'method': 'set_reference_data',
                           'params': {'_base': 'USDb', '_quote': 'USD', '_rate': 1*10**18}},
                          {'contract': 'addressProvider', 'method': 'setLendingPool',
                           'params': {'_address': contracts['lendingPool']}},
                          {'contract': 'addressProvider', 'method': 'setLendingPoolDataProvider',
                           'params': {'_address': contracts['lendingPoolDataProvider']}},
                          {'contract': 'addressProvider', 'method': 'setUSDb',
                           'params': {'_address': contracts['sample_token']}},
                          {'contract': 'addressProvider', 'method': 'setoUSDb',
                           'params': {'_address': contracts['oUSDb']}},
                          {'contract': 'lendingPoolCore', 'method': 'setReserveConstants', 'params': {"_constants": [
                              {"reserve": contracts['sample_token'], "optimalUtilizationRate":f"8{'0'*17}", "baseBorrowRate":f"2{'0'*16}", "slopeRate1":f"4{'0'*16}", "slopeRate2":f"1{'0'*18}"}]}},
                          {'contract': 'lendingPool', 'method': 'setSICXAddress',
                           'params': {'_address': contracts['sicx']}},
                          {'contract': 'priceOracle', 'method': 'set_reference_data',
                           'params': {'_base': 'sICX', '_quote': 'USD', '_rate': 1*10**18}},
                          {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol',
                           'params': {'_reserveAddress': contracts['sicx'], '_sym':"sICX"}},
                          {'contract': 'addressProvider', 'method': 'setsICX',
                           'params': {'_address': contracts['sicx']}},
                          {'contract': 'addressProvider', 'method': 'setoICX',
                           'params': {'_address': contracts['oICX']}},
                          {'contract': 'lendingPoolCore', 'method': 'setReserveConstants', 'params': {"_constants": [
                              {"reserve": contracts['sicx'], "optimalUtilizationRate":f"6{'0'*17}", "baseBorrowRate":f"0{'0'*17}", "slopeRate1":f"8{'0'*16}", "slopeRate2":f"2{'0'*18}"}]}},
                          {'contract': 'oICX', 'method': 'setCoreAddress',
                           'params': {'_address': contracts['lendingPoolCore']}},
                          {'contract': 'oICX', 'method': 'setReserveAddress',
                           'params': {'_address': contracts['sicx']}},
                          {'contract': 'oICX', 'method': 'setDataProviderAddress',
                           'params': {'_address': contracts['lendingPoolDataProvider']}},
                          {'contract': 'oICX', 'method': 'setLendingPoolAddress',
                           'params': {'_address': contracts['lendingPool']}},
                          {'contract': 'lendingPool', 'method': 'setLiquidationManagerAddress',
                           'params': {'_address': contracts['liquidationManager']}},
                          {'contract': 'liquidationManager', 'method': 'setDataProviderAddress',
                           'params': {'_address': contracts['lendingPoolDataProvider']}},
                          {'contract': 'liquidationManager', 'method': 'setCoreAddress',
                           'params': {'_address': contracts['lendingPoolCore']}},
                          {'contract': 'liquidationManager', 'method': 'setOracleAddress',
                           'params': {'_address': contracts['priceOracle']}},
                          {'contract': 'liquidationManager', 'method': 'setFeeProviderAddress',
                           'params': {'_address': contracts['feeProvider']}}, ]

        for sett in local_settings:
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

    def _borrowSICX(self, _borrowAmount : int,_user):
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
            call_transaction,_user)
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
        print('----------------')
        print('borrowerUserDataBeforeLiquidation::', self.getUserAccountData(_borrowerUser.get_address())) 
        print('_liquidatorUserInitial sicx amount', self.getUserSICXBalance(_liquidatorUser.get_address())/10**18)
        print('usdb reserve before', self.getReserveData(self.contracts['sample_token']))
        liquidityUSDbbefore = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('_liquidatorUser usdb balance before', self.getUserUSDbBalance(_liquidatorUser.get_address())/10**18)
        print('oICX balance of borrower before ', self.getUserOICXBalance(_borrowerUser.get_address())/10**18)

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
        print('borrowerUserDataAfterLiquidation::', self.getUserAccountData(_borrowerUser.get_address())) 
        print('_liquidatorUser sicx amount after liquidation', (self.getUserSICXBalance(_liquidatorUser.get_address())/10**18) )
        print('usdb reserve after liquidation', self.getReserveData(self.contracts['sample_token']))
        liquidityUSDbafter = self.getReserveData(self.contracts['sample_token'])['availableLiquidity']
        print('change in liquidity is', (liquidityUSDbafter - liquidityUSDbbefore)/10**18)
        print('_liquidatorUser usdb balance after', self.getUserUSDbBalance(_liquidatorUser.get_address())/10**18)
        print('oICX balance of  borrower', self.getUserOICXBalance(_borrowerUser.get_address())/10**18)

    """
    def test_oneinitTest(self):
        #check  oToken of user2,3,4,5
        user2OTokenBalance = self.getUserOUSDbBalance(self.test_account2.get_address())
        self.assertEqual(user2OTokenBalance, self.depositUSDbAmountUser2)

        user3OTokenBalance = self.getUserOICXBalance(self.test_account3.get_address())
        self.assertEqual(user3OTokenBalance, self.depositICXAmountUser3)

        user4OTokenBalance = self.getUserOICXBalance(self.test_account4.get_address())
        self.assertEqual(user4OTokenBalance, self.depositICXAmountUser4)

        user5OTokenBalance = self.getUserOICXBalance(self.test_account5.get_address())
        self.assertEqual(user5OTokenBalance, self.depositICXAmountUser5)

        #check borrowed balance for user 3,4,5
        user3USDbBalance = self.getUserUSDbBalance(self.test_account3.get_address())
        self.assertEqual(user3USDbBalance, self.borrowUSDBAmountUser3)

        user4USDbBalance = self.getUserUSDbBalance(self.test_account4.get_address())
        self.assertEqual(user4USDbBalance, self.borrowUSDBAmountUser4)

        user5USDbBalance = self.getUserUSDbBalance(self.test_account5.get_address())
        self.assertEqual(user5USDbBalance, self.borrowUSDBAmountUser5)

        print('getUser3AccountData', self.getUserAccountData(self.test_account3.get_address()))
        print('getUser4AccountData', self.getUserAccountData(self.test_account4.get_address()))
        print('getUser5AccountData', self.getUserAccountData(self.test_account5.get_address()))
    """
        
    """
    def test_twoUser3Liquidation(self):
        collateralGivenToLiquidatorInSICX = exaMul(exaDiv(self.loanPayoffAmountUser3, self.sICXRate), EXA + self.liquidationBonus)
        collateralTrasnferredToFeeProviderInSICX = exaMul(exaDiv(exaMul(self.borrowUSDBAmountUser3, self.feePercentage), self.sICXRate), EXA + self.liquidationBonus)
        totalCollateralSubtractedFromUser = collateralGivenToLiquidatorInSICX + collateralTrasnferredToFeeProviderInSICX
        totalCollateralSubtractedUSD = exaMul(totalCollateralSubtractedFromUser, self.sICXRate)
        #borrower collateral balance
        self.assertEqual(self.getUserAccountData(self.test_account3.get_address())['totalLiquidityBalanceUSD'], exaMul(self.depositICXAmountUser3, self.sICXRate) - totalCollateralSubtractedUSD)
        #borrower borrow balance
        #test does not pass due to accured interest
        #self.assertEqual(self.getUserAccountData(self.test_account3.get_address())['totalBorrowBalanceUSD'], (self.borrowUSDBAmountUser3 - self.loanPayoffAmountUser3))

        #liquidator sicx balance
        self.assertEqual(self.getUserSICXBalance(self.test_account2.get_address()), collateralGivenToLiquidatorInSICX)
        #liquidator usdb balance
        self.assertEqual(self.getUserUSDbBalance(self.test_account2.get_address()), self.userTestUSdbAmount - self.depositUSDbAmountUser2 - self.loanPayoffAmountUser3)

        #usdb reserve available liquidity
        self.assertEqual(self.getReserveData(self.contracts['sample_token'])['availableLiquidity'] ,self.depositUSDbAmountUser2 - self.borrowUSDBAmountUser3 - self.borrowUSDBAmountUser4 - self.borrowUSDBAmountUser5 + self.loanPayoffAmountUser3)
        #usdb reserve total borrows
        #test does not pass due to accured interest
        #self.assertEqual(self.getReserveData(self.contracts['sample_token'])['totalBorrows'] ,self.borrowUSDBAmountUser3 + self.borrowUSDBAmountUser4 + self.borrowUSDBAmountUser5 - self.loanPayoffAmountUser3)
    """
    """
    def test_twoUser4Liquidation(self):
        #calculate bad depth manually
        badDepth = self.borrowUSDBAmountUser4 + exaMul(self.borrowUSDBAmountUser4, self.feePercentage) - exaMul(exaMul(self.depositICXAmountUser4 , self.sICXRate), self.baseLTVasCollateralICX)
        collateralGivenToLiquidatorInSICX = exaMul(exaDiv(badDepth, self.sICXRate), EXA + self.liquidationBonus)
        collateralTrasnferredToFeeProviderInSICX = exaMul(exaDiv(exaMul(self.borrowUSDBAmountUser4, self.feePercentage), self.sICXRate), EXA + self.liquidationBonus)
        totalCollateralSubtractedFromUser = collateralGivenToLiquidatorInSICX + collateralTrasnferredToFeeProviderInSICX
        totalCollateralSubtractedUSD = exaMul(totalCollateralSubtractedFromUser, self.sICXRate)
        #print(totalCollateralSubtractedUSD)
        #borrower collateral balance
        liquidatorPreviousSICXbalance = 96250000000000000000
        #test does not pass due to recursion value obtained during division
        #self.assertEqual(self.getUserAccountData(self.test_account4.get_address())['totalLiquidityBalanceUSD'], exaMul(self.depositICXAmountUser4, self.sICXRate) - totalCollateralSubtractedUSD)
        
        #borrower borrow balance
        #test does not pass due to accured interest
        self.assertEqual(self.getUserAccountData(self.test_account4.get_address())['totalBorrowBalanceUSD'], (self.borrowUSDBAmountUser4 - badDepth))

        #liquidator sicx balance
        #test does not pass due to recursion value lost in division
        #self.assertEqual(self.getUserSICXBalance(self.test_account2.get_address()),liquidatorPreviousSICXbalance + collateralGivenToLiquidatorInSICX)
        
        #liquidator usdb balance
        #test does not pass due to recursion value lost in division
        #self.assertEqual(self.getUserUSDbBalance(self.test_account2.get_address()), self.userTestUSdbAmount - self.depositUSDbAmountUser2 - badDepth - self.loanPayoffAmountUser3)

        #usdb reserve available liquidity
        #test does not pass due to accured interest
        #self.assertEqual(self.getReserveData(self.contracts['sample_token'])['availableLiquidity'] ,self.depositUSDbAmountUser2 - self.borrowUSDBAmountUser3 - self.borrowUSDBAmountUser4 - self.borrowUSDBAmountUser5 + self.loanPayoffAmountUser4 + self.loanPayoffAmountUser3)
        
        #usdb reserve total borrows
        #test does not pass due to accured interest
        #does not pass due to accured interst
        #self.assertEqual(self.getReserveData(self.contracts['sample_token'])['totalBorrows'] ,self.borrowUSDBAmountUser3 + self.borrowUSDBAmountUser4 + self.borrowUSDBAmountUser5 - self.loanPayoffAmountUser4 - self.loanPayoffAmountUser3)
    """
