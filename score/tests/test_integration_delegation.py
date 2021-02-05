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
DEPLOY = ['delegation',  'ommToken']


class TestIntegrationDelegation(IconIntegrateTestBase):
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
       

       


        # deploy SCORE
        for address in DEPLOY:
            self.SCORE_PROJECT = self.SCORES + "/" + address
            self.contracts[address] = self._deploy_score()['scoreAddress']
        
        self._setVariablesAndInterfaces()

        
        
        

        # Transfer omm token to users 
        self.ommAmount2 = 1000 * 10 ** 18
        self.ommAmount3 = 1000 * 10 ** 18
        self.ommAmount4 = 1000 * 10 ** 18
        self._transferOmm(self.ommAmount2, self.test_account2.get_address())
        self._transferOmm(self.ommAmount3, self.test_account3.get_address())
        self._transferOmm(self.ommAmount4, self.test_account4.get_address())

        # stake omm tokens by the users 
        self._stakeOmmToken(self.ommAmount2 // 2,self.test_account2)
        self._stakeOmmToken(self.ommAmount3 // 2,self.test_account3)
        self._stakeOmmToken(self.ommAmount4 // 2,self.test_account4)

        randomPrepList=["hx9a5a9c116379ecb9e4aadb423955fc9351771aa5",
                        "hx9a5a9c116379ecb9e4aadb423955fc9351771aa6",
                        "hx9a5a9c116379ecb9e4aadb423955fc9351771aa7",
                        "hx9a5a9c116379ecb9e4aadb423955fc9351771aa8",
                        "hx9a5a9c116379ecb9e4aadb423955fc9351771aa9"]

        #update delegation by user2
        delegations1=[{"prepAddress":randomPrepList[0],"prepPercentage":"1000000000000000000"}]
        self._updateDelegation(delegations1,self.test_account2)
        # delegationPercentage = self._delegationPercentage()
        # pprint(delegationPercentage)

        #update delegation by user3
        delegations2=[{"prepAddress":randomPrepList[0],"prepPercentage":"500000000000000000"},
                      {"prepAddress":randomPrepList[1],"prepPercentage":"500000000000000000"}]
        self._updateDelegation(delegations2,self.test_account3)
        # delegationPercentage = self._delegationPercentage()
        # pprint(delegationPercentage)

        #update delegation by user2
        delegations3=[{"prepAddress":randomPrepList[0],"prepPercentage":"400000000000000000"},
                      {"prepAddress":randomPrepList[3],"prepPercentage":"400000000000000000"},
                      {"prepAddress":randomPrepList[4],"prepPercentage":"200000000000000000"}]
        self._updateDelegation(delegations3,self.test_account2)

        self._stakeOmmToken(self.ommAmount3 // 4,self.test_account3)
        self._updateDelegation(None,self.test_account3)

        delegationPercentage = self._delegationPercentage()
        # pprint(delegationPercentage)

        userDetails = self._getUserDelegationDetails(self.test_account3.get_address())
        pprint(userDetails)
        # all prep votes
        votes={}
        for prep in randomPrepList:
            vote = self._prepVotes(prep)
            votes[prep]= int(vote,0)
        # pprint(votes)

        
     

        
       
        
        

    
    def _setVariablesAndInterfaces(self):
        contracts = self.contracts
        local_settings = [{'contract': 'ommToken', 'method': 'setAdmin', 'params': {'_admin':self._test1.get_address()}},
                          {'contract': 'ommToken', 'method': 'set_unstaking_period',
                              'params': {'_time': 30}},
                          {'contract': 'ommToken', 'method': 'setMinumumStake',
                           'params': {'_min':100 * 10**18}},
                          
                          {'contract': 'delegation', 'method': 'setOmmToken',
                           'params': {'_address': contracts['ommToken']}}, ]

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

    

    def _transferOmm(self, _testFund: int, _user):
        # Transferring 1 Mill USdb to  test_account3
        params = {"_to": _user,"_value": _testFund}
        call_transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['ommToken']) \
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

    def _stakeOmmToken(self, _value: int, _user):
        # calling deposit from test_account2
        params = {"_value": _value}
        call_transaction = CallTransactionBuilder() \
            .from_(_user.get_address()) \
            .to(self.contracts['ommToken']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("stake") \
            .params(params) \
            .build() 

        signed_transaction = SignedTransaction(
            call_transaction, _user)
        tx_result = self.process_transaction(signed_transaction)
        # pprint(tx_result)
        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

    def _updateDelegation(self, _delegations: int, _user):
        params = { "_delegations": _delegations}
        call_transaction = CallTransactionBuilder()\
            .from_(_user.get_address())\
            .to(self.contracts['delegation']) \
            .nid(3) \
            .step_limit(10000000) \
            .nonce(100) \
            .method("updateDelegations")\
            .params(params)\
            .build()

        signed_transaction = SignedTransaction(call_transaction,_user)
        tx_result = self.process_transaction(signed_transaction)
        if tx_result['status'] !=1:
            print("Update delegation",tx_result['failure'])
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('status' in tx_result)

        

    def _delegationPercentage(self):
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['delegation']) \
            .method("computeDelegationPercentages") \
            .build()
        delegationPercentage = self.process_call(_call)
        for key,value in delegationPercentage.items():
            delegationPercentage[key] = value / 10**18
        return delegationPercentage

    def _prepVotes(self, _prep : Address):
        params = {"_prep": _prep}
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['delegation']) \
            .method("prepVotes") \
            .params(params)\
            .build()
        votes = self.process_call(_call)

        return votes 

    def _getUserDelegationDetails(self, _user : Address):
        params = {"_user": _user }
        _call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(self.contracts['delegation']) \
            .method("getUserDelegationDetails") \
            .params(params)\
            .build()
        votes = self.process_call(_call)

        return votes 

    