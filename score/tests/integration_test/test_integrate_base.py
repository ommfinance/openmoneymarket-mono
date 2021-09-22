import json
import os
from pprint import pprint
from checkscore.repeater import retry
from dotenv import load_dotenv
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet
from iconservice.base.address import Address
from tbears.libs.icon_integrate_test import Account
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS

from .test_integrate_utils import TestUtils

# print(os.curdir)
ROOT=os.path.abspath(os.curdir)
# print(ROOT)
ENV_PATH = os.path.abspath(os.path.join(ROOT, ".env.test"))

HELPER_CONTRACTS=os.path.abspath(os.path.join(ROOT,'tests/config/helper-contracts'))
# print(ROOT,ENV_PATH)
load_dotenv(ENV_PATH)

score_configuration_path=os.environ.get("SCORE_ADDRESS_PATH")
keystore_file = os.environ.get("KEYSTORE_FILE")
KEYSTORE_PASS = os.environ.get("KEYSTORE_PASS")
# print("score_configuration_path",score_configuration_path)
SCORE_ADDRESS_PATH = os.path.join(score_configuration_path)
KEYSTORE_FILE = os.path.join(keystore_file)

# print("SCORE_ADDRESS_PATH",SCORE_ADDRESS_PATH)

T_BEARS_URL = os.environ.get("T_BEARS_URL")
NID = int(os.environ.get("NID"),base=16)
SCORE_ADDRESS = "scoreAddress"
EMISSION_PER_ASSET = (400000 * 10 ** 18 ) // (4 * 86400)
TIMESTAMP = 1622560500000000
LOAN_ORIGINATION_PERCENT = 10 ** 15
EXA = 10 ** 18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000
PREP_LIST = ["hxec79e9c1c882632688f8c8f9a07832bcabe8be8f","hxd3be921dfe193cd49ed7494a53743044e3376cd3",\
            "hx9e7509f86ea3ba5c139161d6e92a3982659e9f30", "hxaad52424d4aec9dac7d9f6796da527f471269d2c"]
OMM_SICX_ID = 1
OMM_USDS_ID = 2
OUSDS_EMISSION = int(0.5 * 0.5 * EXA)
DUSDS_EMISSION = int(0.5 * 0.5 * EXA)
DICX_EMISSION = int(0.5 * 0.5 * EXA)
OICX_EMISSION = int(0.5 * 0.5 * EXA)
OMM_SICX_DIST_PERCENTAGE = int(0.1 * EXA)
OMM_USDS_DIST_PERCENTAGE = int(0.1 * EXA)
OMM_DIST_PERCENTAGE = int(0.2 * EXA)
WORKER_DIST_PERCENTAGE = int(0.2 * EXA)
DAO_DIST_PERCENTAGE = int(0.2 * EXA)

RE_DEPLOY_CONTRACT=[]

###### EXA MATH LIBRARY



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
    DIR = ROOT

    CONTRACTS = ['addressProvider', 'daoFund', 'delegation', 'lendingPool', 'feeProvider',
                 'lendingPoolCore', 'lendingPoolDataProvider', 'liquidationManager', 'stakedLp',
                 'ommToken', 'priceOracle', 'rewardDistribution', 'governance', 'workerToken']
    OTOKENS = ['oUSDS', 'oICX']
    DTOKENS = ['dUSDS', 'dICX']

    def setUp(self):
        self._wallet_setup()
        self.icon_service=IconService(HTTPProvider(T_BEARS_URL, 3))
        super().setUp(
            network_only=True,
            icon_service=self.icon_service,  # aws tbears
            nid=NID,
            tx_result_wait=5
        )
        print(f"balanace------setup------${self.icon_service.get_balance(self.deployer_wallet.get_address())}")
        self.contracts = {}
        self._deploy_contracts()
        with open(SCORE_ADDRESS_PATH, "r") as file:
            self.contracts = json.load(file)
        for contract in RE_DEPLOY_CONTRACT:
            self._update_contract(contract)
        # self._update_token_contract("dToken", "dICX")
        # self._update_token_contract("dToken", "dUSDS")

    def tearDown(self):
        print(f"balanace-----teardown-------${self.icon_service.get_balance(self.deployer_wallet.get_address())}")


    def _deploy_contracts(self):
        if os.path.exists(SCORE_ADDRESS_PATH) is False:
            print(f'{SCORE_ADDRESS_PATH} does not exists')
            self._deploy_all()
            self._deploy_helper_contracts()
            self._config_omm()
            self._supply_liquidity()

    def _wallet_setup(self):
        # self.deployer_wallet: 'KeyWallet' = self._test1
        self.deployer_wallet: 'KeyWallet' = KeyWallet.load(KEYSTORE_FILE, KEYSTORE_PASS)


    def _deploy_all(self):
        txns = []

        for item in self.CONTRACTS:
            params = {}
            if item == "sample_token":
                params = {'_name': "BridgeDollars",
                          '_symbol': 'USDs', '_decimals': 18}
            elif item == "omm_token":
                params = {'_initialSupply': 0, '_decimals': 18}
            elif item == "workerToken":
                params = {'_initialSupply': 100, '_decimals': 18}
            elif item == "sicx":
                params = {'_initialSupply': 500000000, '_decimals': 18}
            elif item == "oToken":
                params = {"_name": "BridgeUSDInterestToken",
                          "_symbol": "oUSDs"}

            deploy_tx = self.build_deploy_tx(
                from_=self.deployer_wallet,
                to=self.contracts.get(item, SCORE_INSTALL_ADDRESS),
                content=os.path.abspath(os.path.join(self.DIR, item)),
                params=params
            )
            txns.append(deploy_tx)

        otxns = []
        param1 = {"_name": "OmmUSDsInterestToken", "_symbol": "oUSDs"}
        param2 = {"_name": "ICXinterestToken", "_symbol": "oICX"}
        # param3 = {"_name":"IconUSDInterest","_symbol":"oIUSDC","_decimals":6}
        deploy_oUSDs = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("oUSDS", SCORE_INSTALL_ADDRESS),
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
        #   from_ = self.deployer_wallet,
        #   to = self.contracts.get("oIUSDC", SCORE_INSTALL_ADDRESS),
        #   content = os.path.abspath(os.path.join(self.DIR, "oToken")),
        #   params = param3
        #   )
        otxns.append(deploy_oUSDs)
        otxns.append(deploy_oICX)
        # otxns.append(deploy_oIUSDc)

        dtxns = []
        param1 = {"_name":"Omm USDS Debt Token","_symbol":"dUSDS"}
        param2 = {"_name":"Omm ICX Debt Token","_symbol":"dICX"}
        deploy_dUSDS = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("dUSDS", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "dToken")),
            params=param1
        )
        deploy_dICX = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("dICX", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(self.DIR, "dToken")),
            params=param2
        )
        dtxns.append(deploy_dUSDS)
        dtxns.append(deploy_dICX)

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

        dresults = self.process_transaction_bulk(
            requests=dtxns,
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

        for idx, tx_result in enumerate(dresults):
            self.assertTrue('status' in tx_result, tx_result)
            self.assertEqual(1, tx_result['status'],
                             f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
            self.contracts[self.DTOKENS[idx]] = tx_result[SCORE_ADDRESS]

        with open(SCORE_ADDRESS_PATH, "w") as file:
            json.dump(self.contracts, file, indent=4)

    def _deploy_helper_contracts(self):

        if os.path.exists(SCORE_ADDRESS_PATH):
            with open(SCORE_ADDRESS_PATH, "r") as file:
                self.contracts = json.load(file)

        content = os.path.abspath(os.path.join(HELPER_CONTRACTS, "staking.zip"))
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
        print("staking_score",staking_score)
        self.contracts.update({"staking": staking_score})

        deploy_bridge = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("usds", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(HELPER_CONTRACTS, "bridge.zip"))
        )

        tx_hash_1 = self.process_transaction(deploy_bridge, self.icon_service)
        tx_result_1 = self.get_tx_result(tx_hash_1['txHash'])
        self.assertEqual(True, tx_hash_1['status'])
        self.assertTrue('scoreAddress' in tx_result_1)
        self.contracts.update({"usds": tx_result_1['scoreAddress']})

        deploy_sicx = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("sicx", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(HELPER_CONTRACTS, "sicx.zip")),
            params={"_admin": self.contracts['staking']}  # staking_score
        )

        tx_hash_1 = self.process_transaction(deploy_sicx, self.icon_service)
        tx_result_1 = self.get_tx_result(tx_hash_1['txHash'])
        self.assertEqual(True, tx_hash_1['status'])
        self.assertTrue('scoreAddress' in tx_result_1)
        self.contracts.update({"sicx": tx_result_1['scoreAddress']})

        deploy_lp_token = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("lptoken", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath(os.path.join(HELPER_CONTRACTS, "lpToken.zip")),
        )

        tx_hash_lp_token = self.process_transaction(deploy_lp_token, self.icon_service)
        tx_result_lp_token = self.get_tx_result(tx_hash_lp_token['txHash'])
        self.assertEqual(True, tx_hash_lp_token['status'])
        self.assertTrue('scoreAddress' in tx_result_lp_token)
        self.contracts.update({"lpToken": tx_result_lp_token[SCORE_ADDRESS]})

        with open(SCORE_ADDRESS_PATH, "w") as file:
            json.dump(self.contracts, file, indent=4)

    @retry(JSONRPCException, tries=10, delay=1, back_off=2)
    def get_tx_result(self, _tx_hash):
        tx_result = self.icon_service.get_transaction_result(_tx_hash)
        return tx_result

    def _update_token_contract(self, contract, token):
        content = os.path.abspath(os.path.join(self.DIR, contract))
        update_contract = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get(token),
            content=content,
            params = {}
            )

        tx_hash = self.process_transaction(update_contract, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_hash['status'])
        self.assertTrue('scoreAddress' in tx_result)

    def _update_contract(self, contract):

        content = os.path.abspath(os.path.join(self.DIR, contract))
        deploy_contract = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get(contract, SCORE_INSTALL_ADDRESS),
            content=content,
            params={}
        )
        print(contract)

        tx_hash = self.process_transaction(deploy_contract, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_hash['status'])
        self.assertTrue('scoreAddress' in tx_result)

    def _update_helper_contract(self, contract):

        content = os.path.abspath(os.path.join(HELPER_CONTRACTS, f"{contract}.zip"))
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
        with open(SCORE_ADDRESS_PATH, "r") as file:
            self.contracts = json.load(file)
        self._deposit_for_fee_sharing()
        self._mint_bridge()
        self._config_address_provider()
        self._config_general()
        self._config_staking()
        self._config_rewards()
        self._add_reserves_to_lendingPoolCore()
        self._add_reserves_constants()

    def _config_address_provider(self):
        contracts = self.contracts
        contracts['bandOracle'] = "cx399dea56cf199b1c9e43bead0f6a284bdecfbf62"
        contract_details = [
            {'name': 'addressProvider', 'address': contracts['addressProvider']},
            {'name': 'daoFund', 'address': contracts['daoFund']},
            {'name': 'delegation', 'address': contracts['delegation']},
            {'name': 'feeProvider', 'address': contracts['feeProvider']},
            {'name': 'governance', 'address': contracts['governance']},
            {'name': 'lendingPool', 'address': contracts['lendingPool']},
            {'name': 'lendingPoolCore', 'address': contracts['lendingPoolCore']},
            {'name': 'lendingPoolDataProvider', 'address': contracts['lendingPoolDataProvider']},
            {'name': 'liquidationManager', 'address': contracts['liquidationManager']},
            {'name': 'ommToken', 'address': contracts['ommToken']},
            {'name': 'priceOracle', 'address': contracts['priceOracle']},
            {'name': 'bandOracle', 'address': contracts['bandOracle']},
            {'name': 'bridgeOToken', 'address': contracts['oUSDS']},
            {'name': 'rewards', 'address': contracts['rewardDistribution']},
            {'name': 'workerToken', 'address': contracts['workerToken']},
            {'name': 'sICX', 'address': contracts['sicx']},
            {'name': 'usds', 'address': contracts['usds']},
            {'name': 'staking', 'address': contracts['staking']},
            {'name': 'ousds', 'address': contracts['oUSDS']},
            {'name': 'dusds', 'address': contracts['dUSDS']},
            {'name': 'oICX', 'address': contracts['oICX']},
            {'name': 'dICX', 'address': contracts['dICX']},
            {'name': 'stakedLp', 'address': contracts['stakedLp']},
            {'name': 'dex', 'address': contracts['lpToken']}
            # {'name': 'diusdc', 'address': contracts['dIUSDC']},
            # {'name': 'oiusdc', 'address': contracts['oIUSDC']},
            # {'name': 'iusdc', 'address': contracts['iusdc']},
        ]

        setting_address_provider = [
            {'contract': 'addressProvider', 'method': 'setAddresses', 'params':{'_addressDetails':contract_details}},
            {'contract': 'addressProvider', 'method': 'setLendingPoolAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setLendingPoolCoreAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setLendingPoolDataProviderAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setLiquidationManagerAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setOmmTokenAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setoICXAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setoUSDsAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setdICXAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setdUSDsAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setDelegationAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setRewardAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setGovernanceAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setGovernanceAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setStakedLpAddresses', 'params':{}},
            {'contract': 'addressProvider', 'method': 'setPriceOracleAddress', 'params':{}},            
        ]

        self._get_transaction(setting_address_provider)

    def _config_general(self):
        contracts = self.contracts
        settings = [
            {'contract': 'lendingPool', 'method': 'setFeeSharingTxnLimit','params': {'_limit': 3}},
            {'contract': 'feeProvider', 'method': 'setLoanOriginationFeePercentage', 'params':{'_percentage': f"{LOAN_ORIGINATION_PERCENT}"}},
            {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['usds'],'_sym':"USDS"}},
            {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['sicx'],'_sym':"ICX"}},
            {'contract': 'priceOracle', 'method': 'setOraclePriceBool', 'params':{'_value': '0x0'}},
            {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'USDS','_quote':'USD','_rate':1*10**18}},
            {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'ICX','_quote':'USD','_rate':10*10**17}},
            {'contract': 'delegation', 'method': 'addAllContributors','params': {'_preps':PREP_LIST}},
            {'contract': 'governance', 'method': 'setStartTimestamp','params': {'_timestamp': TIMESTAMP}},     
            {'contract':  'ommToken', 'method': 'setMinimumStake','params': {'_min':10 * 10**18}},
            {'contract':  'stakedLp', 'method': 'addPool','params': {'_pool': contracts['sicx'], '_id': f"{OMM_SICX_ID}" }},
            {'contract':  'stakedLp', 'method': 'addPool','params': {'_pool': contracts['usds'],'_id': f"{OMM_USDS_ID}" }},
            # {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['iusdc'],'_sym':"USDC"}},
            # {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'IUSDC','_quote':'USD','_rate':10*10**17}},  
            # {'contract':  'stakedLp', 'method': 'addPool','params': {'_pool': contracts['iusdc'] , '_id': OMM_USDC_ID}}
        ]

        self._get_transaction(settings)


    def _deposit_for_fee_sharing(self):
        contracts = ['usds', 'lendingPool']
        for contract in contracts:
            print(f"-------------------------------Deposit fee sharing amount to {contract}----------------------------------")
            deposit_fee = self.deposit_tx(self.deployer_wallet, self.contracts[contract])
            tx_hash = self.process_transaction(deposit_fee, self.icon_service)
            tx_result = self.get_tx_result(tx_hash['txHash'])
            self.assertEqual(True, tx_hash['status'])

    def _mint_bridge(self):
        param = {
            '_to': self.deployer_wallet.get_address(),
            '_value': 1000000 * 10 ** 18
        }
        tx_result = self.send_tx(
                from_=self.deployer_wallet,
                to=self.contracts['usds'],
                method="mint",
                params=param
            )
        self.assertEqual(True, tx_result['status'])

    def _add_reserves_constants(self):
        print(
            "-------------------------------Configuring LENDING POOL CORE RESERVE SETTINGS VIA GOVERNANCE ----------------------------------------------------")

        contracts = self.contracts
        settings_reserves = [{'contract': 'governance',
                              'method': 'setReserveConstants',
                              'params': {"_constants": [{"reserve": contracts['usds'],
                                                         "optimalUtilizationRate": f"8{'0' * 17}",
                                                         "baseBorrowRate": f"2{'0' * 16}",
                                                         "slopeRate1": f"6{'0' * 16}",
                                                         "slopeRate2": f"1{'0' * 18}"}]}},
                             {'contract': 'governance',
                              'method': 'setReserveConstants',
                              'params': {"_constants": [{"reserve": contracts['sicx'],
                                                         "optimalUtilizationRate": f"8{'0' * 17}",
                                                         "baseBorrowRate": f"0{'0' * 17}",
                                                         "slopeRate1": f"8{'0' * 16}",
                                                         "slopeRate2": f"2{'0' * 18}"}]}}
                             # {'contract': 'lendingPoolCore',
                             #  'method': 'setReserveConstants',
                             #  'params' :{"_constants": [{"reserve":contracts['iusdc'],
                             #                              "optimalUtilizationRate":f"8{'0'*17}",
                             #                             "baseBorrowRate":f"2{'0'*16}",
                             #                             "slopeRate1":f"6{'0'*16}",
                             #                             "slopeRate2":f"1{'0'*18}"} ]}}
                             ]

        self._get_transaction(settings_reserves)

    def _config_rewards(self):
        print("-------------------------------Configuring REWARDS ----------------------------------------------------")

        contracts = self.contracts
        settings_rewards = [
            {'contract': 'rewardDistribution', 'method': 'configureAssetEmission',
                     'params': {
                        "_assetConfig":
                            [
                                {"asset": contracts["oUSDS"], "distPercentage":f"{OUSDS_EMISSION}"},
                                {"asset": contracts["dUSDS"], "distPercentage":f"{DUSDS_EMISSION}"},
                                {"asset": contracts["dICX"], "distPercentage":f"{DICX_EMISSION}"},
                                {"asset": contracts["oICX"], "distPercentage":f"{OICX_EMISSION}"},
                                # {"asset": contracts["oIUSDC"], "distPercentage":f"{OIUSDC_EMISSION}"},
                                # {"asset": contracts["dIUSDC"], "distPercentage":f"{DIUSDC_EMISSION}"}
                            ]
                        }
            },
            {'contract': 'rewardDistribution', 'method': 'configureLPEmission',
                     'params': {
                        "_lpConfig":
                            [
                                {"_id": f"{OMM_SICX_ID}", "distPercentage": f"{OMM_SICX_DIST_PERCENTAGE}"},
                                {"_id": f"{OMM_USDS_ID}", "distPercentage": f"{OMM_USDS_DIST_PERCENTAGE}"},
                                # {"_id": f"{OMM_USDC_ID}", "distPercentage": f"{OMM_USDC_DIST_PERCENTAGE}"}
                            ]
                        }
            },
            {'contract': 'rewardDistribution', 'method': 'configureOmmEmission',
                     'params': { "_distPercentage": f"{OMM_DIST_PERCENTAGE}"}
            },
            {'contract':'rewardDistribution','method':'setDailyDistributionPercentage',
                     'params':{"_recipient": "worker" ,"_percentage": f"{WORKER_DIST_PERCENTAGE}"}
            },
            {'contract':'rewardDistribution','method':'setDailyDistributionPercentage',
                     'params':{"_recipient": "daoFund","_percentage":f"{DAO_DIST_PERCENTAGE}"}
            },
            {'contract':'lendingPoolDataProvider','method':'setDistPercentages',
                     'params':{
                         "_percentages": [
                             {'recipient': 'worker' ,'distPercentage': f"{WORKER_DIST_PERCENTAGE}"},
                             {'recipient': 'daoFund' ,'distPercentage': f"{DAO_DIST_PERCENTAGE}" }
                         ]
                     }
            }
        ]

        self._get_transaction(settings_rewards)

    def _config_staking(self):
        print("-------------------------------Configuring STAKING----------------------------------------------------")

        contracts = self.contracts
        settings_staking = [
            {'contract': 'staking', 'method': 'setSicxAddress',
             'params':{'_address':contracts['sicx']}},
            {'contract': 'staking', 'method': 'toggleStakingOn',
             'params': {}}
        ]

        self._get_transaction(settings_staking)

    def _add_reserves_to_lendingPoolCore(self):
        print(
            "------------------------------- ADDING RESERVES TO LENDING POOL CORE VIA GOVERNANCE ----------------------------------------------------")

        contracts = self.contracts
        # params_iusdc ={
        #     "_reserve": {
        #         "reserveAddress":contracts['iusdc'],
        #         "oTokenAddress":contracts['oIUSDC'],
        #         "dTokenAddress": contracts['dIUSDC'],
        #         "lastUpdateTimestamp": "0",
        #         "liquidityRate":"0",
        #         "borrowRate":"0",
        #         "liquidityCumulativeIndex":f"1{'0'*18}",
        #         "borrowCumulativeIndex":f"1{'0'*18}",
        #         "baseLTVasCollateral":"500000000000000000",
        #         "liquidationThreshold":"650000000000000000",
        #         "liquidationBonus":"100000000000000000",
        #         "decimals":"6",
        #         "borrowingEnabled": "1",
        #         "usageAsCollateralEnabled":"1",
        #         "isFreezed":"0",
        #         "isActive":"1"
        #     } 
        # }

        params_usds ={
            "_reserve": {
                "reserveAddress":contracts['usds'],
                "oTokenAddress":contracts['oUSDS'],
                "dTokenAddress": contracts['dUSDS'],
                "lastUpdateTimestamp": "0",
                "liquidityRate":"0",
                "borrowRate":"0",
                "liquidityCumulativeIndex":f"1{'0'*18}",
                "borrowCumulativeIndex":f"1{'0'*18}",
                "baseLTVasCollateral":"500000000000000000",
                "liquidationThreshold":"650000000000000000",
                "liquidationBonus":"100000000000000000",
                "decimals":"18",
                "borrowingEnabled": "1",
                "usageAsCollateralEnabled":"1",
                "isFreezed":"0",
                "isActive":"1"
            } 
        }

        params_icx = {
            "_reserve": {
                "reserveAddress":contracts['sicx'],
                "oTokenAddress":contracts['oICX'],
                "dTokenAddress": contracts['dICX'],
                "lastUpdateTimestamp": "0",
                "liquidityRate":"0",
                "borrowRate":"0",
                "liquidityCumulativeIndex":f"1{'0'*18}",
                "borrowCumulativeIndex":f"1{'0'*18}",
                "baseLTVasCollateral":"500000000000000000",
                "liquidationThreshold":"650000000000000000",
                "liquidationBonus":"100000000000000000",
                "decimals":"18",
                "borrowingEnabled": "1",
                "usageAsCollateralEnabled":"1",
                "isFreezed":"0",
                "isActive":"1"
            } 
        }

        settings = [
            # {'contract': 'governance',
            #  'method': 'addReserveData', 'params': params_iusdc},
            {'contract': 'governance',
             'method': 'initializeReserve', 'params': params_usds},
            {'contract': 'governance',
             'method': 'initializeReserve', 'params': params_icx}
        ]
        self._get_transaction(settings)

    def _supply_liquidity(self):

        # deposit USDS
        depositData = {'method': 'deposit', 'params': {'amount': 50 * 10 ** 18}}

        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                "_value": 50*EXA,
                "_data": data}
        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts["usds"], #USDS contract
            method="transfer",
            params=params
            )
        self.assertEqual(tx_result['status'], 1)

        # deposit ICX
        params = {"_amount": 10 * 10 ** 18}
        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts["lendingPool"], 
            value=100 * 10 ** 18,
            method="deposit",
            params=params
            )
        self.assertEqual(tx_result['status'], 1)


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
