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
# print("score_configuration_path",score_configuration_path)
SCORE_ADDRESS_PATH = os.path.join(score_configuration_path)

# print("SCORE_ADDRESS_PATH",SCORE_ADDRESS_PATH)

T_BEARS_URL = os.environ.get("T_BEARS_URL")
SCORE_ADDRESS = "scoreAddress"
EMISSION_PER_ASSET = (400000 * 10 ** 18 ) // (4 * 86400)
TIMESTAMP = 1622560500000000
LOAN_ORIGINATION_PERCENT = 10 ** 15
EXA = 10 ** 18
halfEXA = EXA // 2
SECONDS_PER_YEAR = 31536000
PREP_LIST = ["hx9eec61296a7010c867ce24c20e69588e2832bc52","hx000e0415037ae871184b2c7154e5924ef2bc075e",\
            "hx2fb8fb849cba40bf59a48ebcef899d6ae45382f4", "hx0d091baf34fb2b8e144f3e878dc73c35e77f912f"]

OMM_SICX_ID = 1
OMM_USDS_ID = 2

OUSDS_EMISSION = int(0.5 * 0.5 * EXA)
DUSDS_EMISSION = int(0.5 * 0.5 * EXA)
DICX_EMISSION = int(0.5 * 0.5 * EXA)
OICX_EMISSION = int(0.5 * 0.5 * EXA)

OMM_SICX_DIST_PERCENTAGE = int(0.1 * EXA)
OMM_USDS_DIST_PERCENTAGE = int(0.1 * EXA)
OMM_DIST_PERCENTAGE = int(0.2 * EXA)

WORKER_DIST_PERCENTAGE = int(0.3 * EXA)
DAO_DIST_PERCENTAGE = int(0.4 * EXA)
LENDING_BORROW_PERCENTAGE = int(0.1*EXA)
LP_OMM_STAKING_PERCENTAGE = int(0.2*EXA)

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

    CONTRACTS = ['daoFund', 'delegation', 'lendingPool', 'feeProvider',
                 'lendingPoolCore', 'lendingPoolDataProvider', 'liquidationManager', 'stakedLp',
                 'ommToken', 'priceOracle', 'rewardDistribution', 'governance', 'workerToken']
    OTOKENS = ['oUSDS', 'oICX']
    DTOKENS = ['dUSDS', 'dICX']

    def setUp(self):
        self._wallet_setup()
        super().setUp(
            network_only=True,
            icon_service=IconService(HTTPProvider(T_BEARS_URL, 3)),  # aws tbears
            nid=3,
            tx_result_wait=5
        )
        self.contracts = {}
        self._deploy_contracts()
        with open(SCORE_ADDRESS_PATH, "r") as file:
            self.contracts = json.load(file)
        for contract in RE_DEPLOY_CONTRACT:
            self._update_contract(contract)
        # self._update_token_contract("dToken", "dICX")
        # self._update_token_contract("dToken", "dUSDS")

    def _deploy_contracts(self):
        if os.path.exists(SCORE_ADDRESS_PATH) is False:
            print(f'{SCORE_ADDRESS_PATH} does not exists')
            self._deploy_all()
            self._deploy_helper_contracts()
            self._config_omm()
            self._supply_liquidity()

    def _wallet_setup(self):
        self.icx_factor = 10 ** 18
        self.btest_wallet: 'KeyWallet' = self._wallet_array[5]
        self.staking_wallet: 'KeyWallet' = self._wallet_array[6]
        self.user1: 'KeyWallet' = self._wallet_array[7]
        self.user2: 'KeyWallet' = self._wallet_array[8]

        self.deployer_wallet: 'KeyWallet' = self._test1

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
        _deploy = self.build_deploy_tx(
            from_=self.deployer_wallet,
            to=self.contracts.get("addressProvider", SCORE_INSTALL_ADDRESS),
            content=os.path.abspath((os.path.join(self.DIR, "addressProvider"))),
            params={}
        )

        tx_hash = self.process_transaction(_deploy, self.icon_service)
        tx_result = self.get_tx_result(tx_hash['txHash'])
        self.assertEqual(True, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)
        _addressProvider = tx_result['scoreAddress']

        txns = []

        for item in self.CONTRACTS:
            params = {}
            if item == "omm_token":
                params = {'_initialSupply': 0, '_decimals': 18}
            elif item == "workerToken":
                params = {'_initialSupply': 100, '_decimals': 18}
            elif item == "sicx":
                params = {'_initialSupply': 500000000, '_decimals': 18}
            elif item == "rewardDistribution":
                DISTRIBUTION_PERCENTAGE = [
                    {"recipient": "worker", "percentage": f'{WORKER_DIST_PERCENTAGE}'},
                    {"recipient": "daoFund", "percentage": f'{DAO_DIST_PERCENTAGE}'},
                    {"recipient": "lendingBorrow", "percentage": f'{LENDING_BORROW_PERCENTAGE}'},
                    {"recipient": "liquidityProvider", "percentage": f'{LP_OMM_STAKING_PERCENTAGE}'}
                ]
                params = {"_distPercentage": DISTRIBUTION_PERCENTAGE, "_startTimestamp": TIMESTAMP}

            if item not in ['addressProvider', "workerToken"]:
                params['_addressProvider'] = _addressProvider

            deploy_tx = self.build_deploy_tx(
                from_=self.deployer_wallet,
                to=self.contracts.get(item, SCORE_INSTALL_ADDRESS),
                content=os.path.abspath(os.path.join(self.DIR, item)),
                params=params
            )
            txns.append(deploy_tx)

        otxns = []
        param1 = {"_name": "OmmUSDsInterestToken", "_symbol": "oUSDs","_addressProvider": _addressProvider}
        param2 = {"_name": "ICXinterestToken", "_symbol": "oICX","_addressProvider": _addressProvider}
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
        param1 = {"_name":"Omm USDS Debt Token","_symbol":"dUSDS","_addressProvider": _addressProvider}
        param2 = {"_name":"Omm ICX Debt Token","_symbol":"dICX","_addressProvider": _addressProvider}
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

        self.contracts['addressProvider'] = _addressProvider

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
        self._add_pools()
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
            {'name': 'USDS', 'address': contracts['usds']},
            {'name': 'staking', 'address': contracts['staking']},
            {'name': 'oUSDS', 'address': contracts['oUSDS']},
            {'name': 'dUSDS', 'address': contracts['dUSDS']},
            {'name': 'oICX', 'address': contracts['oICX']},
            {'name': 'dICX', 'address': contracts['dICX']},
            {'name': 'stakedLP', 'address': contracts['stakedLp']},
            {'name': 'dex', 'address': contracts['lpToken']},
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
            {'contract':  'ommToken', 'method': 'setMinimumStake','params': {'_min':10 * 10**18}}
            # {'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['iusdc'],'_sym':"USDC"}},
            # {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'IUSDC','_quote':'USD','_rate':10*10**17}},  
            # {'contract':  'stakedLp', 'method': 'addPool','params': {'_pool': contracts['iusdc'] , '_id': OMM_USDC_ID}}
        ]

        self._get_transaction(settings)


    def _deposit_for_fee_sharing(self):
        contracts = ['usds', 'lendingPool', 'ommToken']
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
                                                         "slopeRate2": f"2{'0' * 18}"}]}},
                             {'contract': 'governance',
                              'method': 'setReserveConstants',
                              'params': {"_constants": [{"reserve": contracts['sicx'],
                                                         "optimalUtilizationRate": f"8{'0' * 17}",
                                                         "baseBorrowRate": f"0{'0' * 17}",
                                                         "slopeRate1": f"8{'0' * 16}",
                                                         "slopeRate2": f"4{'0' * 18}"}]}}
                             # {'contract': 'lendingPoolCore',
                             #  'method': 'setReserveConstants',
                             #  'params' :{"_constants": [{"reserve":contracts['iusdc'],
                             #                              "optimalUtilizationRate":f"8{'0'*17}",
                             #                             "baseBorrowRate":f"2{'0'*16}",
                             #                             "slopeRate1":f"6{'0'*16}",
                             #                             "slopeRate2":f"1{'0'*18}"} ]}}
                             ]

        self._get_transaction(settings_reserves)

    def _add_pools(self):
        contracts = self.contracts
        asset_configs = [
            {
                'contract': 'governance', 'method': 'addPools',
                'params': {
                    "_assetConfigs":
                        [
                         #reserves
                         {"poolID": f'{-1}', "rewardEntity": "lendingBorrow", "asset": contracts["oUSDS"], "assetName": "oUSDS",
                          "distPercentage": f"{OUSDS_EMISSION}"},
                         {"poolID": f'{-1}', "rewardEntity": "lendingBorrow", "asset": contracts["dUSDS"], "assetName": "dUSDS",
                          "distPercentage": f"{DUSDS_EMISSION}"},
                         {"poolID": f'{-1}', "rewardEntity": "lendingBorrow", "asset": contracts["dICX"], "assetName": "dICX",
                          "distPercentage": f"{DICX_EMISSION}"},
                         {"poolID": f'{-1}', "rewardEntity": "lendingBorrow", "asset": contracts["oICX"], "assetName": "oICX",
                          "distPercentage": f"{OICX_EMISSION}"},
                         #liquidity providers
                         {"poolID": f'{OMM_SICX_ID}', "rewardEntity": "liquidityProvider", "asset": contracts["ommToken"],
                          "assetName": "OMM/sICX", "distPercentage": f"{OMM_SICX_DIST_PERCENTAGE}"},
                         {"poolID": f'{OMM_USDS_ID}', "rewardEntity": "liquidityProvider", "asset": contracts["ommToken"],
                          "assetName": "OMM/USDS", "distPercentage": f"{OMM_USDS_DIST_PERCENTAGE}"},
                         #omm token
                         {"poolID": f'{-1}', "rewardEntity": "liquidityProvider", "asset": contracts["ommToken"],
                          "assetName": "OMM", "distPercentage": f"{OMM_DIST_PERCENTAGE}"}
                    ]
                }
            }
        ]
        self._get_transaction(asset_configs)

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
             'method': 'initializeReserve', 'params': params_icx},
            {'contract': 'governance',
             'method': 'updateBorrowThreshold', 'params': {
                    "_reserve": contracts['sicx'],
                    "_borrowThreshold": 90*EXA//100}},
            {'contract': 'governance',
             'method': 'updateBorrowThreshold', 'params': {
                    "_reserve": contracts['usds'],
                    "_borrowThreshold": 90*EXA//100
             }}
        ]
        self._get_transaction(settings)

    def _supply_liquidity(self):

        # deposit USDS
        depositData = {'method': 'deposit', 'params': {'amount': 5000 * 10 ** 18}}

        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                "_value": 5000*EXA,
                "_data": data}
        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts["usds"], #USDS contract
            method="transfer",
            params=params
            )
        self.assertEqual(tx_result['status'], 1)

        # deposit ICX
        params = {"_amount": 10000 * 10 ** 18}
        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts["lendingPool"], 
            value=10000 * 10 ** 18,
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
