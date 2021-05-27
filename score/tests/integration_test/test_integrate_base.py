import json
import os
from typing import Union, List
from pprint import pprint
from ..consts import *
from checkscore.repeater import retry
import time
from .test_integrate_utils import TestUtils
from iconsdk.exception import JSONRPCException
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconservice.base.address import Address
from tbears.config.tbears_config import tbears_server_config, TConfigKey as TbConf
from tbears.libs.icon_integrate_test import Account
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
SCORE_ADDRESS = "scoreAddress"

###### EXA MATH LIBRARY

EXA = 10 ** 18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000


# 365 days = (365 days) × (24 hours/day) × (3600 seconds/hour) = 31536000 seconds


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a * b)) // EXA


def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b


def exaPow(x: int, n: int) -> int:
    if n % 2 != 0:
        z = x
    else:
        z = EXA

    n = n // 2
    while n != 0:
        x = exaMul(x, x)

        if n % 2 != 0:
            z = exaMul(z, x)

        n = n // 2

    return z


def convertToExa(_amount: int, _decimals: int) -> int:
    if _decimals >= 0:
        return _amount * EXA // (10 ** _decimals)


def convertExaToOther(_amount: int, _decimals: int) -> int:
    if _decimals >= 0:
        return _amount * (10 ** _decimals) // EXA


class OMMTestBase(TestUtils):
    DIR = os.path.abspath(os.path.join(DIR_PATH, "../../"))
    print("DIR", DIR)
    CONTRACTS = ['addressProvider', 'daoFund', 'delegation', 'governance', 'lendingPool',
                 'lendingPoolCore', 'lendingPoolDataProvider', 'liquidationManager',
                 'ommToken', 'priceOracle', 'rewards', 'snapshot', 'worker_token']
    OTOKENS = ['oUSDb', 'oICX']

    def setUp(self):
        self._wallet_setup()
        super().setUp(
            network_only=True,
            icon_service=IconService(HTTPProvider(AWS_IP, 3)),  # aws tbears
            nid=3,
            tx_result_wait=5
        )
        self.contracts = {}
        # self.send_icx(self._test1, self.btest_wallet.get_address(), 1_000_000 * self.icx_factor)
        # self.send_icx(self._test1, self.staking_wallet.get_address(), 1_000_000 * self.icx_factor)
        # self.PREPS = {
        # 	self._wallet_array[0].get_address(),
        # 	self._wallet_array[1].get_address()
        # }

        if os.path.exists(os.path.join(DIR_PATH, "scores_address.json")):
            with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
                self.contracts = json.load(file)

            # self._deploy_helper_contracts()
            # self._config_omm()
            # self._update_contract("lendingPool")
            # self._update_helper_contract("staking")
            # self._register_100_preps(40, 60)
            # self._register_100_preps(60, 80)
            # self._register_100_preps(80, 99)
            # self._register_100_preps(100, 120)
            # self._register_100_preps(120, 150)
            return
        else:
            self._deploy_all()
            # self._deploy_helper_contracts()
            # self._config_omm()
            # # a = 1
            # for i in range(10):
            #     self._register_100_preps(a, a + 9)
            #     a += 10

    def _wallet_setup(self):
        self.icx_factor = 10 ** 18
        self.btest_wallet: 'KeyWallet' = self._wallet_array[5]
        self.staking_wallet: 'KeyWallet' = self._wallet_array[6]
        self.user1: 'KeyWallet' = self._wallet_array[7]
        self.user2: 'KeyWallet' = self._wallet_array[8]

        self.deployer_wallet: 'KeyWallet' = self._test1
        print(self.deployer_wallet.get_address())

        self.genesis_accounts = [
            Account("test1", Address.from_string(
                self._test1.get_address()), 800_000_000 * self.icx_factor),
            Account("btest_wallet", Address.from_string(
                self.btest_wallet.get_address()), 1_000_000 * self.icx_factor),
            Account("staking_wallet", Address.from_string(self.staking_wallet.get_address()),
                    1_000_000 * self.icx_factor),
            Account("user1", Address.from_string(
                self.user1.get_address()), 1_000_000 * self.icx_factor),
            Account("user2", Address.from_string(
                self.user2.get_address()), 1_000_000 * self.icx_factor),
        ]

    def _deploy_all(self):
        txns = []

        for item in self.CONTRACTS:
            params = {}
            if item == "sample_token":
                params = {'_name': "BridgeDollars",
                          '_symbol': 'USDb', '_decimals': 18}
            elif item == "omm_token":
                params = {'_initialSupply': 0, '_decimals': 18}
            elif item == "worker_token":
                params = {'_initialSupply': 100, '_decimals': 18}
            elif item == "sicx":
                params = {'_initialSupply': 500000000, '_decimals': 18}
            elif item == "oToken":
                params = {"_name": "BridgeUSDInterestToken",
                          "_symbol": "oUSDb"}

            deploy_tx = self.build_deploy_tx(
                from_=self.deployer_wallet,
                to=self.contracts.get(item, SCORE_INSTALL_ADDRESS),
                content=os.path.abspath(os.path.join(self.DIR, item)),
                params=params
            )
            txns.append(deploy_tx)

        otxns = []
        param1 = {"_name": "OmmUSDbInterestToken", "_symbol": "oUSDb"}
        param2 = {"_name": "ICXinterestToken", "_symbol": "oICX"}
        # param3 = {"_name":"IconUSDInterest","_symbol":"oIUSDC","_decimals":6}
        deploy_oUSDb = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("oUSDb", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "oToken")),
            params=param1
        )
        deploy_oICX = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("oICX", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "oToken")),
            params=param2
        )
        # deploy_oIUSDc = self.build_deploy_tx(
        # 	from_ = self.deployer_wallet,
        # 	to = self.contracts.get("oIUSDC", SCORE_INSTALL_ADDRESS),
        # 	content = os.path.abspath(os.path.join(self.DIR, "oToken")),
        # 	params = param3
        # 	)
        otxns.append(deploy_oUSDb)
        otxns.append(deploy_oICX)
        # otxns.append(deploy_oIUSDc)

        results = self.process_transaction_bulk(
            requests=txns,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        oresults = self.process_transaction_bulk(
            requests=otxns,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        for idx, tx_result in enumerate(results):
            # print(tx_result)
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
            self.contracts[self.CONTRACTS[idx]] = tx_result[SCORE_ADDRESS]

        for idx, tx_result in enumerate(oresults):
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
            self.contracts[self.OTOKENS[idx]] = tx_result[SCORE_ADDRESS]

        with open(os.path.join(DIR_PATH, "scores_address.json"), "w") as file:
            json.dump(self.contracts, file, indent=4)

    def _deploy_helper_contracts(self):
        DIR = os.path.abspath(os.path.join(
            DIR_PATH, "../../helper-contracts/"))

        if os.path.exists(os.path.join(DIR_PATH, "scores_address.json")):
            with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
                self.contracts = json.load(file)

        content = os.path.abspath(os.path.join(DIR, "staking"))
        deploy_staking = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("staking", SCORE_INSTALL_ADDRESS),
            content=content,
            params={}
        )

        tx_hash = self.process_transaction(deploy_staking, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_hash['status'])
        self.assertTrue('scoreAddress' in tx_result)
        staking_score = tx_result['scoreAddress']
        self.contracts.update({"staking": staking_score})

        deploy_bridge = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("usdb", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(DIR, "bridge"))
        )

        tx_hash_1 = self.process_transaction(deploy_bridge, self.icon_service)
        tx_result_1 = self.get_tx_result(tx_hash_1['txHash'])
        self.assertEqual(True, tx_hash_1['status'])
        self.assertTrue('scoreAddress' in tx_result_1)
        self.contracts.update({"usdb": tx_result_1['scoreAddress']})

        tx_hash = self.process_transaction(deploy_bridge, self.icon_service)
        tx_result = self.get_tx_result(tx_hash)

        self.assertEqual(True, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)
        self.contracts.update({"usdb": tx_result['scoreAddress']})

        deploy_sicx = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("sicx", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(DIR, "sicx")),
            params={"_admin": self.contracts['staking']} # staking_score
        )

        tx_hash_1 = self.process_transaction(deploy_sicx, self.icon_service)
        tx_result_1 = self.get_tx_result(tx_hash_1['txHash'])
        self.assertEqual(True, tx_hash_1['status'])
        self.assertTrue('scoreAddress' in tx_result_1)
        self.contracts.update({"sicx": tx_result_1['scoreAddress']})

        with open(os.path.join(DIR_PATH, "scores_address.json"), "w") as file:
            json.dump(self.contracts, file, indent=4)

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self, _tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    def _update_contract(self, contract):
        
        content = os.path.abspath(os.path.join(self.DIR, contract))
        deploy_staking = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get(contract, SCORE_INSTALL_ADDRESS),
            content=content,
            params={}
        )

        tx_hash = self.process_transaction(deploy_staking, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_hash['status'])
        self.assertTrue('scoreAddress' in tx_result)

    def _update_helper_contract(self, contract):
        DIR = os.path.abspath(os.path.join(
            DIR_PATH, "../../helper-contracts/"))
        
        content = os.path.abspath(os.path.join(DIR, contract))
        deploy_staking = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get(contract, SCORE_INSTALL_ADDRESS),
            content=content,
            params={}
        )

        tx_hash = self.process_transaction(deploy_staking, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_hash['status'])
        self.assertTrue('scoreAddress' in tx_result)


    def _config_omm(self):
        print("-------------------------------Configuring OMM----------------------------------------------------")
        with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
            self.contracts = json.load(file)
        self._config_lendingPool()
        self._config_lendingPoolDataProvider()
        self._config_oToken()
        self._config_priceOracleRef()
        self._config_addressProvider()
        self._config_lendingPoolCoreSettings()
        self._config_oICX()
        # self._config_oIUSDC()
        self._config_liquidationManager()
        self._config_delegation()
        self._config_ommToken()
        self._config_lendingPoolCore()
        # self._config_priceOracle()
        self._config_snapshot()
        self._config_rewards()
        self._config_governance()
        self._add_reserves_to_lendingPoolCore()
        self._config_staking()

    def _config_lendingPool(self):
        print(
            "-------------------------------Configuring LENDING POOL----------------------------------------------------")

        contracts = self.contracts
        settings_lendingPool = [
            {'contract': 'lendingPool', 'method': 'setLendingPoolCore',
             'params': {'_address': contracts['lendingPoolCore']}},
            {'contract': 'lendingPool', 'method': 'setLendingPoolDataProvider',
             'params': {'_address': contracts['lendingPoolDataProvider']}},
            {'contract': 'lendingPool', 'method': 'setLiquidationManager',
             'params': {'_address': contracts['liquidationManager']}},
            {'contract': 'lendingPool', 'method': 'setStaking',
             'params': {'_address': contracts['staking']}},
            {'contract': 'lendingPool', 'method': 'setOICX',
             'params': {'_address': contracts['oICX']}},
            {'contract': 'lendingPool', 'method': 'setReward',
             'params': {'_address': contracts['rewards']}},
            {'contract': 'lendingPool', 'method': 'setDaoFund', # 
             'params': {'_address': contracts['daoFund']}},
            {'contract': 'lendingPool', 'method': 'setSnapshot', #
             'params': {'_address': contracts['snapshot']}},
            {'contract': 'lendingPool', 'method': 'setSICX',
             'params': {'_address': contracts['sicx']}},
            {'contract': 'lendingPool', 'method': 'setLoanOriginationFeePercentage',
             'params': {'_percentage': 10 ** 15}},  # added later
        ]
        self._get_transaction(settings_lendingPool)

    def _config_lendingPoolDataProvider(self):
        print(
            "-------------------------------Configuring LENDING POOL DATA PROVIDER----------------------------------------------------")

        contracts = self.contracts
        settings_lendinPoolDataProvider = [{'contract': 'lendingPoolDataProvider', 'method': 'setSymbol',
                                            'params': {'_reserve': contracts['usdb'], '_sym': "USDb"}},
                                           {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol',
                                            'params': {'_reserve': contracts['sicx'], '_sym': "ICX"}},
                                           # {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['iusdc'],'_sym':"USDC"}},
                                           {'contract': 'lendingPoolDataProvider', 'method': 'setLendingPoolCore',
                                            'params': {'_address': contracts['lendingPoolCore']}},
                                           {'contract': 'lendingPoolDataProvider', 'method': 'setPriceOracle',
                                            'params': {'_address': contracts['priceOracle']}},
                                           {'contract': 'lendingPoolDataProvider', 'method': 'setLendingPool',
                                            'params': {'_address': contracts['lendingPool']}},
                                           {'contract': 'lendingPoolDataProvider', 'method': 'setLiquidationManager',
                                            'params': {'_address': contracts['liquidationManager']}},
                                           {'contract': 'lendingPoolDataProvider', 'method': 'setStaking',
                                            'params': {'_address': contracts['staking']}}
                                           ]
        self._get_transaction(settings_lendinPoolDataProvider)

    def _config_oToken(self):
        print("-------------------------------Configuring OTOKEN----------------------------------------------------")

        contracts = self.contracts
        settings_oToken = [
            {'contract': 'oUSDb', 'method': 'setLendingPoolCore',
             'params': {'_address': contracts['lendingPoolCore']}},
            {'contract': 'oUSDb', 'method': 'setReserve',
             'params': {'_address': contracts['usdb']}},
            {'contract': 'oUSDb', 'method': 'setLendingPoolDataProvider',
             'params': {'_address': contracts['lendingPoolDataProvider']}},
            {'contract': 'oUSDb', 'method': 'setLendingPool',
             'params': {'_address': contracts['lendingPool']}},
            {'contract': 'oUSDb', 'method': 'setLiquidation', 'params': {'_address': contracts['liquidationManager']}}]

        self._get_transaction(settings_oToken)

    def _config_priceOracleRef(self):
        print(
            "-------------------------------Configuring PRICE ORACLE REFERENCE DATA----------------------------------------------------")

        contracts = self.contracts
        setting_priceOracle = [{'contract': 'priceOracle', 'method': 'set_reference_data',
                                'params': {'_base': 'USDb', '_quote': 'USD', '_rate': 1 * 10 ** 18}},
                               {'contract': 'priceOracle', 'method': 'set_reference_data',
                                'params': {'_base': 'ICX', '_quote': 'USD', '_rate': 15 * 10 ** 17}},
                               # {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'IUSDC','_quote':'USDC','_rate':10*10**17}}
                               ]

        self._get_transaction(setting_priceOracle)

    def _config_addressProvider(self):
        print(
            "-------------------------------Configuring ADDRESS PROVIDER ----------------------------------------------------")

        contracts = self.contracts
        setting_addressProvider = [{'contract': 'addressProvider', 'method': 'setLendingPool',
                                    'params': {'_address': contracts['lendingPool']}},
                                   {'contract': 'addressProvider', 'method': 'setLendingPoolDataProvider',
                                    'params': {'_address': contracts['lendingPoolDataProvider']}},
                                   {'contract': 'addressProvider', 'method': 'setUSDb',
                                    'params': {'_address': contracts['usdb']}},
                                   {'contract': 'addressProvider', 'method': 'setoUSDb',
                                    'params': {'_address': contracts['oUSDb']}},
                                   {'contract': 'addressProvider', 'method': 'setsICX',
                                    'params': {'_address': contracts['sicx']}},
                                   {'contract': 'addressProvider', 'method': 'setoICX',
                                    'params': {'_address': contracts['oICX']}},
                                   {'contract': 'addressProvider', 'method': 'setStaking',
                                    'params': {'_address': contracts['staking']}},
                                   # {'contract': 'addressProvider', 'method': 'setIUSDC', 'params':{'_address':contracts['iusdc']}},
                                   # {'contract': 'addressProvider', 'method': 'setoIUSDC', 'params':{'_address':contracts['oIUSDC']}},
                                   {'contract': 'addressProvider', 'method': 'setOmmToken',
                                    'params': {'_address': contracts['ommToken']}},
                                   {'contract': 'addressProvider', 'method': 'setDelegation',
                                    'params': {'_address': contracts['delegation']}},
                                   {'contract': 'addressProvider', 'method': 'setRewards',
                                    'params': {'_address': contracts['rewards']}}
                                   ]

        self._get_transaction(setting_addressProvider)

    def _config_lendingPoolCoreSettings(self):
        print(
            "-------------------------------Configuring LENDING POOL CORE RESERVE SETTINGS ----------------------------------------------------")

        contracts = self.contracts
        settings_reserves = [{'contract': 'lendingPoolCore',
                              'method': 'setReserveConstants',
                              'params': {"_constants": [{"reserve": contracts['usdb'],
                                                         "optimalUtilizationRate": f"8{'0' * 17}",
                                                         "baseBorrowRate": f"2{'0' * 16}",
                                                         "slopeRate1": f"6{'0' * 16}",
                                                         "slopeRate2": f"1{'0' * 18}"}]}},
                             {'contract': 'lendingPoolCore',
                              'method': 'setReserveConstants',
                              'params': {"_constants": [{"reserve": contracts['sicx'],
                                                         "optimalUtilizationRate": f"8{'0' * 17}",
                                                         "baseBorrowRate": f"0{'0' * 17}",
                                                         "slopeRate1": f"8{'0' * 16}",
                                                         "slopeRate2": f"2{'0' * 18}"}]}}
                             # {'contract': 'lendingPoolCore',
                             # 	'method': 'setReserveConstants',
                             # 	'params' :{"_constants": [{"reserve":contracts['iusdc'],
                             # 								"optimalUtilizationRate":f"8{'0'*17}",
                             # 							   "baseBorrowRate":f"2{'0'*16}",
                             # 							   "slopeRate1":f"6{'0'*16}",
                             # 							   "slopeRate2":f"1{'0'*18}"} ]}}
                             ]

        self._get_transaction(settings_reserves)

    def _config_oICX(self):
        print("-------------------------------Configuring OICX ----------------------------------------------------")

        contracts = self.contracts
        settings_oicx = [
            {'contract': 'oICX', 'method': 'setLendingPoolCore',
             'params': {'_address': contracts['lendingPoolCore']}},
            {'contract': 'oICX', 'method': 'setReserve',
             'params': {'_address': contracts['sicx']}},
            {'contract': 'oICX', 'method': 'setLendingPoolDataProvider',
             'params': {'_address': contracts['lendingPoolDataProvider']}},
            {'contract': 'oICX', 'method': 'setLendingPool',
             'params': {'_address': contracts['lendingPool']}},
            {'contract': 'oICX', 'method': 'setLiquidation', 'params': {'_address': contracts['liquidationManager']}}]

        self._get_transaction(settings_oicx)

    # def _config_oIUSDC(self):
    # 	print("-------------------------------Configuring OIUSDC ----------------------------------------------------")

    # 	contracts = self.contracts
    # 	settings_oiusdc = [ {'contract': 'oIUSDC', 'method': 'setLendingPoolCore', 'params':{'_address':contracts['lendingPoolCore']}},
    # 				{'contract': 'oIUSDC', 'method': 'setReserve', 'params':{'_address':contracts['iusdc']}},
    # 				{'contract': 'oIUSDC', 'method': 'setLendingPoolDataProvider', 'params':{'_address':contracts['lendingPoolDataProvider']}},
    # 				{'contract': 'oIUSDC', 'method': 'setLendingPool', 'params':{'_address':contracts['lendingPool']}},
    # 				{'contract': 'oIUSDC', 'method': 'setLiquidation', 'params':{'_address':contracts['liquidationManager']}}
    # 				]
    # 	self._get_transaction(settings_oiusdc)

    def _config_liquidationManager(self):
        print(
            "-------------------------------Configuring LIQUIDATION MANAGER ----------------------------------------------------")

        contracts = self.contracts
        settings_liquidationManager = [{'contract': 'liquidationManager', 'method': 'setLendingPoolDataProvider',
                                        'params': {'_address': contracts['lendingPoolDataProvider']}},
                                       {'contract': 'liquidationManager', 'method': 'setLendingPoolCore',
                                        'params': {'_address': contracts['lendingPoolCore']}},
                                       {'contract': 'liquidationManager', 'method': 'setPriceOracle',
                                        'params': {'_address': contracts['priceOracle']}},
                                       # {'contract': 'liquidationManager', 'method': 'setFeeProvider','params': {'_address':contracts['feeProvider']}},
                                       {'contract': 'liquidationManager', 'method': 'setStaking',
                                        'params': {'_address': contracts['staking']}}
                                       ]
        self._get_transaction(settings_liquidationManager)

    def _config_delegation(self):
        print(
            "-------------------------------Configuring DELEGATION ----------------------------------------------------")

        contracts = self.contracts
        settings_delegation = [{'contract': 'delegation', 'method': 'setLendingPoolCore',
                                'params': {'_address': contracts['lendingPoolCore']}},
                               {'contract': 'delegation', 'method': 'setOmmToken',
                                'params': {'_address': contracts['ommToken']}}]
        self._get_transaction(settings_delegation)

    def _config_ommToken(self):
        print(
            "-------------------------------Configuring OMM TOKEN ----------------------------------------------------")

        contracts = self.contracts
        settings_ommToken = [{'contract': 'ommToken', 'method': 'setAdmin', 'params': {'_admin': contracts['rewards']}},
                             {'contract': 'ommToken', 'method': 'setDelegation',
                              'params': {'_address': contracts['delegation']}},
                             {'contract': 'ommToken', 'method': 'setRewards',
                              'params': {'_address': contracts['rewards']}},
                             {'contract': 'ommToken', 'method': 'setMinimumStake',
                              'params': {'_min': 10 * 10 ** 18}},
                             {'contract': 'ommToken', 'method': 'setUnstakingPeriod', 'params': {'_time': 120}}]
        self._get_transaction(settings_ommToken)

    def _config_lendingPoolCore(self):
        print(
            "-------------------------------Configuring LENDING POOL CORE ----------------------------------------------------")

        contracts = self.contracts
        settings_lendingPoolCore = [{'contract': 'lendingPoolCore', 'method': 'setLendingPool',
                                     'params': {'_address': contracts['lendingPool']}},
                                    {'contract': 'lendingPoolCore', 'method': 'setDaoFund',
                                     'params': {'_address': contracts['daoFund']}},
                                    {'contract': 'lendingPoolCore', 'method': 'setPriceOracle',
                                     'params': {'_address': contracts['priceOracle']}},
                                    {'contract': 'lendingPoolCore', 'method': 'setLiquidationManager',
                                     'params': {'_address': contracts['liquidationManager']}},
                                    {'contract': 'lendingPoolCore', 'method': 'setDelegation',
                                     'params': {'_address': contracts['delegation']}},
                                    {'contract': 'lendingPoolCore', 'method': 'setStaking',
                                     'params': {'_address': contracts['staking']}},
                                    {'contract': 'lendingPoolCore', 'method': 'set_id', 'params': {'_value': '1'}}]

        self._get_transaction(settings_lendingPoolCore)

    # def _config_priceOracle(self):
    # 	print("-------------------------------Configuring PRICE ORACLE -----------------------------------------------------")

    # 	contracts = self.contracts
    # 	settings_priceOracle =[{'contract':  'priceOracle', 'method': 'setBandOracle','params': {'_address':"cx61a36e5d10412e03c907a507d1e8c6c3856d9964"}},
    # 				   {'contract':  'priceOracle', 'method': 'toggleOraclePriceBool','params':{}}]

    # 	tx = self.getTransaction(settings_priceOracle)

    def _config_snapshot(self):
        print(
            "-------------------------------Configuring SNAPSHOT ----------------------------------------------------")

        contracts = self.contracts
        settings_snapshot = [
            {'contract': 'snapshot', 'method': 'setAdmin',
             'params': {'_address': contracts['lendingPool']}},
            {'contract': 'snapshot', 'method': 'setGovernance', 'params': {'_address': contracts['governance']}}]

        self._get_transaction(settings_snapshot)

    def _config_rewards(self):
        print("-------------------------------Configuring REWARDS ----------------------------------------------------")

        contracts = self.contracts
        settings_rewards = [
            {'contract': 'rewards', 'method': 'setLendingPool',
             'params': {'_address': contracts['lendingPool']}},
            {'contract': 'rewards', 'method': 'setOmm',
             'params': {'_address': contracts['ommToken']}},
            {'contract': 'rewards', 'method': 'setLendingPoolCore',
             'params': {'_address': contracts['lendingPoolCore']}},
            {'contract': 'rewards', 'method': 'setSnapshot',
             'params': {'_address': contracts['snapshot']}},
            {'contract': 'rewards', 'method': 'setWorkerToken',
             'params': {'_address': contracts['worker_token']}},
            {'contract': 'rewards', 'method': 'setAdmin',
             'params': {'_address': contracts['governance']}},
            {'contract': 'rewards', 'method': 'setDaoFund',
             'params': {'_address': contracts['daoFund']}},
            {'contract': 'rewards', 'method': 'setLpToken',
             'params': {'_address': "cx291dacbb875a94b364194a5febaac4e6318681f7"}},
        ]

        self._get_transaction(settings_rewards)

    def _config_governance(self):
        print(
            "-------------------------------Configuring GOVERNANCE ----------------------------------------------------")

        contracts = self.contracts
        settings_governance = [
            {'contract': 'governance', 'method': 'setSnapshot',
             'params': {'_address': contracts['snapshot']}},
            {'contract': 'governance', 'method': 'setRewards',
             'params': {'_address': contracts['rewards']}},
            {'contract': 'governance', 'method': 'setStartTimestamp',
             'params': {'_timestamp': 1577854800000000}}
        ]
        self._get_transaction(settings_governance)

    def _config_staking(self):
        print("-------------------------------Configuring STAKING----------------------------------------------------")

        contracts = self.contracts
        txs = [
            self.build_tx(self.deployer_wallet, to=self.contracts['staking'],
                          method='setSicxAddress', params={'_address': self.contracts['sicx']}),
            self.build_tx(self.deployer_wallet,
                          to=self.contracts['staking'], method='toggleStakingOn')
        ]

        results = self.process_transaction_bulk(
            requests=txs,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        for tx_result in results:
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")

    def _add_reserves_to_lendingPoolCore(self):
        print(
            "------------------------------- ADDING RESERVES TO LENDING POOL CORE ----------------------------------------------------")

        contracts = self.contracts
        # params_iusdc ={"_reserve": {"reserveAddress":contracts['iusdc'],"oTokenAddress":contracts['oIUSDC'],"totalBorrows":"0","lastUpdateTimestamp": "0","liquidityRate":"0","borrowRate":"0","liquidityCumulativeIndex":f"1{'0'*18}","borrowCumulativeIndex":f"1{'0'*18}","baseLTVasCollateral":"500000000000000000","liquidationThreshold":"650000000000000000","liquidationBonus":"100000000000000000","decimals":"6","borrowingEnabled": "1","usageAsCollateralEnabled":"1","isFreezed":"0","isActive":"1"} }
        params_usdb = {
            "_reserve": {"reserveAddress": contracts['usdb'], "oTokenAddress": contracts['oUSDb'], "totalBorrows": "0",
                         "lastUpdateTimestamp": "0", "liquidityRate": "0", "borrowRate": "0",
                         "liquidityCumulativeIndex": f"1{'0' * 18}", "borrowCumulativeIndex": f"1{'0' * 18}",
                         "baseLTVasCollateral": "500000000000000000", "liquidationThreshold": "650000000000000000",
                         "liquidationBonus": "100000000000000000", "decimals": "18", "borrowingEnabled": "1",
                         "usageAsCollateralEnabled": "1", "isFreezed": "0", "isActive": "1"}}
        params_icx = {
            "_reserve": {"reserveAddress": contracts['sicx'], "oTokenAddress": contracts['oICX'], "totalBorrows": "0",
                         "lastUpdateTimestamp": "0", "liquidityRate": "0", "borrowRate": "0",
                         "liquidityCumulativeIndex": f"1{'0' * 18}", "borrowCumulativeIndex": f"1{'0' * 18}",
                         "baseLTVasCollateral": "500000000000000000", "liquidationThreshold": "650000000000000000",
                         "liquidationBonus": "100000000000000000", "decimals": "18", "borrowingEnabled": "1",
                         "usageAsCollateralEnabled": "1", "isFreezed": "0", "isActive": "1"}}

        settings = [
            # {'contract': 'lendingPoolCore',
            #  'method': 'addReserveData', 'params': params_iusdc},
            {'contract': 'lendingPoolCore',
             'method': 'addReserveData', 'params': params_usdb},
            {'contract': 'lendingPoolCore',
             'method': 'addReserveData', 'params': params_icx}
        ]
        self._get_transaction(settings)

    def _register_100_preps(self, start, end):
        txs = []
        self.call_tx("cx0000000000000000000000000000000000000000", "getPReps", params={"startRanking":9,"endRanking":200})
        # for i in range(start, end):
        #     params = {"name": "Test P-rep " + str(i), "country": "KOR", "city": "Unknown",
        #               "email": "nodehx9eec61296a7010c867ce24c20e69588e283212" + str(i) + "@example.com", "website":
        #                   'https://nodehx9eec61296a7010c867ce24c20e69588e283212' +
        #                   str(i) + '.example.com',
        #               "details": 'https'
        #                          '://nodehx9eec61296a7010c867ce24c20e69588e283212' +
        #                          str(i) + '.example.com/details',
        #               "p2pEndpoint": "nodehx9eec61296a7010c867ce24c20e69588e283212" + str(i) + ".example.com:7100",
        #               "nodeAddress": "hx9eec61296a7010c867ce24c20e69588e28321" + str(i)}
        #     self.send_icx(
        #         self.deployer_wallet, self._wallet_array[i].get_address(), 3000000000000000000000)
        #     txs.append(self.build_tx(self._wallet_array[i], "cx0000000000000000000000000000000000000000",
        #                              2000000000000000000000, "registerPRep", params))
        # ab = self.process_transaction_bulk(txs, self.icon_service, 10)
        # pprint(ab)

    def _get_transaction(self, settings):
        txs = []
        contracts = self.contracts
        for sett in settings:
            print(
                f'Calling {sett["method"]}, with parameters {sett["params"]} on the {sett["contract"]} contract.')
            res = self.build_tx(self.deployer_wallet, to=contracts[sett['contract']], method=sett['method'],
                                params=sett['params'])
            txs.append(res)

        results = self.process_transaction_bulk(
            requests=txs,
            network=self.icon_service,
            block_confirm_interval=self.tx_result_wait
        )

        for tx_result in results:
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
