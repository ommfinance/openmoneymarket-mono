import json
import os
from typing import Union, List
from pprint import pprint
from ..consts import *

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import TransactionBuilder, DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
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


def get_key(my_dict: dict, value: Union[str, int]):
	return list(my_dict.keys())[list(my_dict.values()).index(value)]

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


class TestUtils(IconIntegrateTestBase):

	def setUp(self,
			  genesis_accounts: List[Account] = None,
			  block_confirm_interval: int = tbears_server_config[TbConf.BLOCK_CONFIRM_INTERVAL],
			  network_only: bool = False,
			  network_delay_ms: int = tbears_server_config[TbConf.NETWORK_DELAY_MS],
			  icon_service: IconService = None,
			  nid: int = 3,
			  tx_result_wait: int = 3):
		super().setUp(genesis_accounts, block_confirm_interval, network_only, network_delay_ms)
		self.icon_service = icon_service
		self.nid = nid
		self.tx_result_wait = tx_result_wait

	def deploy_tx(self,
				  from_: KeyWallet,
				  to: str = SCORE_INSTALL_ADDRESS,
				  value: int = 0,
				  content: str = None,
				  params: dict = None) -> dict:

		signed_transaction = self.build_deploy_tx(from_, to, value, content, params)
		tx_result = self.process_transaction(signed_transaction, network=self.icon_service,
											 block_confirm_interval=self.tx_result_wait)

		self.assertTrue('status' in tx_result, tx_result)
		self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
		self.assertTrue('scoreAddress' in tx_result)

		return tx_result

	def build_deploy_tx(self,
						from_: KeyWallet,
						to: str = SCORE_INSTALL_ADDRESS,
						value: int = 0,
						content: str = None,
						params: dict = None,
						step_limit: int = 3_000_000_000,
						nonce: int = 100) -> SignedTransaction:
		print(f"---------------------------Deploying contract: {content}---------------------------------------")
		params = {} if params is None else params
		transaction = DeployTransactionBuilder() \
			.from_(from_.get_address()) \
			.to(to) \
			.value(value) \
			.step_limit(step_limit) \
			.nid(self.nid) \
			.nonce(nonce) \
			.content_type("application/zip") \
			.content(gen_deploy_data_content(content)) \
			.params(params) \
			.build()

		signed_transaction = SignedTransaction(transaction, from_)
		return signed_transaction

	def send_icx(self, from_: KeyWallet, to: str, value: int):
		previous_to_balance = self.get_balance(to)
		previous_from_balance = self.get_balance(from_.get_address())

		signed_icx_transaction = self.build_send_icx(from_, to, value)
		tx_result = self.process_transaction(signed_icx_transaction, self.icon_service, self._block_confirm_interval)

		self.assertTrue('status' in tx_result, tx_result)
		self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
		fee = tx_result['stepPrice'] * tx_result['cumulativeStepUsed']
		self.assertEqual(previous_to_balance + value, self.get_balance(to))
		self.assertEqual(previous_from_balance - value - fee, self.get_balance(from_.get_address()))

	def build_send_icx(self, from_: KeyWallet, to: str, value: int,
					   step_limit: int = 1000000, nonce: int = 3) -> SignedTransaction:
		send_icx_transaction = TransactionBuilder(
			from_=from_.get_address(),
			to=to,
			value=value,
			step_limit=step_limit,
			nid=self.nid,
			nonce=nonce
		).build()
		signed_icx_transaction = SignedTransaction(send_icx_transaction, from_)
		return signed_icx_transaction

	def get_balance(self, address: str) -> int:
		if self.icon_service is not None:
			return self.icon_service.get_balance(address)
		params = {'address': Address.from_string(address)}
		response = self.icon_service_engine.query(method="icx_getBalance", params=params)
		return response

	def send_tx(self, from_: KeyWallet, to: str, value: int = 0, method: str = None, params: dict = None) -> dict:
		print(f"------------Calling {method}, with params={params} to {to} contract----------")
		signed_transaction = self.build_tx(from_, to, value, method, params)
		tx_result = self.process_transaction(signed_transaction, self.icon_service, self.tx_result_wait)

		self.assertTrue('status' in tx_result)
		self.assertEqual(1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
		return tx_result

	def build_tx(self, from_: KeyWallet, to: str, value: int = 0, method: str = None, params: dict = None) \
			-> SignedTransaction:
		params = {} if params is None else params
		tx = CallTransactionBuilder(
			from_=from_.get_address(),
			to=to,
			value=value,
			step_limit=3_000_000_000,
			nid=self.nid,
			nonce=5,
			method=method,
			params=params
		).build()
		signed_transaction = SignedTransaction(tx, from_)
		return signed_transaction

	def call_tx(self, to: str, method: str, params: dict = None):

		params = {} if params is None else params
		call = CallBuilder(
			to=to,
			method=method,
			params=params
		).build()
		response = self.process_call(call, self.icon_service)
		print(f"-----Reading method={method}, with params={params} on the {to} contract------")
		print(f"-------------------The output is: : ")
		pprint(response)
		return response


class OMMTestBase(TestUtils):

	DIR = os.path.abspath(os.path.join(DIR_PATH, "../"))
	CONTRACTS = ['addressProvider', 'daoFund','delegation','governance', 'lendingPool', 
					'lendingPoolCore','lendingPoolDataProvider', 'liquidationManager',
					'ommToken', 'priceOracle','rewards' ,'snapshot','worker_token']
	OTOKENS = ['oUSDb', 'oICX', 'oIUSDC']

	def setUp(self):
		self._wallet_setup()
		super().setUp(genesis_accounts=self.genesis_accounts,
					  block_confirm_interval=2,
					  network_delay_ms=0,
					  network_only=True,
					  icon_service=IconService(HTTPProvider("https://bicon.net.solidwallet.io", 3)), # add testnet url 
					  nid=3,
					  tx_result_wait=6
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
			# self._config_omm()
			return
		else:
			self._deploy_all()
			self._config_omm()

	def _wallet_setup(self):
		self.icx_factor = 10 ** 18
		self.btest_wallet: 'KeyWallet' = self._wallet_array[5]
		self.staking_wallet: 'KeyWallet' = self._wallet_array[6]
		self.user1: 'KeyWallet' = self._wallet_array[7]
		self.user2: 'KeyWallet' = self._wallet_array[8]

		# private="a691ef7d5601f9b5be4f9b9d80215159ea6ff0b88003e3d34e078d40e778b39a"
		self.deployer_wallet: 'KeyWallet' = KeyWallet.load(bytes.fromhex(DEPLOYER_PRIVATE))
		self.test1_wallet: 'KeyWallet' = KeyWallet.load(bytes.fromhex(TEST1_PRIVATE))
		self.test2_wallet: 'KeyWallet' = KeyWallet.load(bytes.fromhex(TEST2_PRIVATE))

		# self.deployer_wallet: 'KeyWallet' = deployer_wallet
		self.genesis_accounts = [
			Account("test1", Address.from_string(self._test1.get_address()), 800_000_000 * self.icx_factor),
			Account("btest_wallet", Address.from_string(self.btest_wallet.get_address()), 1_000_000 * self.icx_factor),
			Account("staking_wallet", Address.from_string(self.staking_wallet.get_address()),
					1_000_000 * self.icx_factor),
			Account("user1", Address.from_string(self.user1.get_address()), 1_000_000 * self.icx_factor),
			Account("user2", Address.from_string(self.user2.get_address()), 1_000_000 * self.icx_factor),
		]

	def _deploy_all(self):
		txns = []

		for item in self.CONTRACTS:
			params = {}
			if item == "sample_token":
				params = {'_name': "BridgeDollars",'_symbol':'USDb' ,'_decimals': 18}
			elif item == "omm_token":
				params = {'_initialSupply':0, '_decimals': 18}
			elif item == "worker_token":
				params = {'_initialSupply':100, '_decimals': 18}
			elif item == "sicx":
				params = {'_initialSupply':500000000, '_decimals': 18}
			elif item == "oToken":
				params = {"_name":"BridgeUSDInterestToken","_symbol":"oUSDb"}
			deploy_tx = self.build_deploy_tx(
				from_ = self.deployer_wallet, 
				to = self.contracts.get(item, SCORE_INSTALL_ADDRESS),
				content = os.path.abspath(os.path.join(self.DIR, item)),
				params = params
				)
			txns.append(deploy_tx)

		otxns = []
		param1 = {"_name":"OmmUSDbInterestToken","_symbol":"oUSDb"}
		param2 = {"_name":"ICXinterestToken","_symbol":"oICX"}
		param3 = {"_name":"IconUSDInterest","_symbol":"oIUSDC","_decimals":6}
		deploy_oUSDb = self.build_deploy_tx(
			from_ = self.deployer_wallet, 
			to = self.contracts.get(item, SCORE_INSTALL_ADDRESS),
			content = os.path.abspath(os.path.join(self.DIR, "oToken")),
			params = param1
			)
		deploy_oICX = self.build_deploy_tx(
			from_ = self.deployer_wallet, 
			to = self.contracts.get(item, SCORE_INSTALL_ADDRESS),
			content = os.path.abspath(os.path.join(self.DIR, "oToken")),
			params = param2
			)
		deploy_oIUSDc = self.build_deploy_tx(
			from_ = self.deployer_wallet, 
			to = self.contracts.get(item, SCORE_INSTALL_ADDRESS),
			content = os.path.abspath(os.path.join(self.DIR, "oToken")),
			params = param3
			)
		otxns.append(deploy_oUSDb)
		otxns.append(deploy_oICX)
		otxns.append(deploy_oIUSDc)

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

	def _config_omm(self):
		print("-------------------------------Configuring OMM----------------------------------------------------")
		with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
			self.contracts = json.load(file)
		# self._config_lendingPool()
		# self._config_lendingPoolDataProvider()
		# self._config_oToken()
		# self._config_priceOracleRef()
		# self._config_addressProvider()
		# self._config_lendingPoolCoreSettings()
		# self._config_oICX()
		# self._config_oIUSDC()
		# self._config_liquidationManager()
		# self._config_delegation()
		# self._config_ommToken()
		# self._config_lendingPoolCore()
		# self._config_priceOracle()
		# self._config_snapshot()
		# self._config_rewards()
		# self._config_governance()
		# self._add_reserves_to_lendingPoolCore()

	def _config_lendingPool(self):
		print("-------------------------------Configuring LENDING POOL----------------------------------------------------")

		contracts = self.contracts
		settings_lendingPool = [
						{'contract': 'lendingPool', 'method': 'setLendingPoolCore', 'params':{'_address': contracts['lendingPoolCore']}},
						{'contract': 'lendingPool', 'method': 'setLendingPoolDataProvider', 'params':{'_address': contracts['lendingPoolDataProvider']}},
						{'contract': 'lendingPool', 'method': 'setLiquidationManager','params': {'_address':contracts['liquidationManager']}},
						{'contract': 'lendingPool', 'method': 'setStaking', 'params':{'_address': contracts['staking']}},
						{'contract': 'lendingPool', 'method': 'setOICX', 'params':{'_address': contracts['oICX']}},
						{'contract': 'lendingPool', 'method': 'setReward','params': {'_address':contracts['rewards']}},
						{'contract': 'lendingPool', 'method': 'setSICX','params': {'_address':contracts['sicx']}},
						{'contract': 'lendingPool', 'method': 'setLoanOriginationFeePercentage','params': {'_percentage':10 ** 15}}, # added later
					   ]
		self._get_transaction(settings_lendingPool)

	def _config_lendingPoolDataProvider(self):
		print("-------------------------------Configuring LENDING POOL DATA PROVIDER----------------------------------------------------")

		contracts = self.contracts
		settings_lendinPoolDataProvider=[{'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['usdb'],'_sym':"USDb"}},
								{'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['sicx'],'_sym':"ICX"}},
								{'contract': 'lendingPoolDataProvider', 'method': 'setSymbol', 'params':{'_reserve': contracts['iusdc'],'_sym':"USDC"}},
								{'contract': 'lendingPoolDataProvider', 'method': 'setLendingPoolCore', 'params':{'_address': contracts['lendingPoolCore']}},
								{'contract': 'lendingPoolDataProvider', 'method': 'setPriceOracle', 'params':{'_address': contracts['priceOracle']}},
								{'contract': 'lendingPoolDataProvider', 'method': 'setLendingPool', 'params':{'_address': contracts['lendingPool']}},
								{'contract': 'lendingPoolDataProvider', 'method': 'setLiquidationManager', 'params':{'_address': contracts['liquidationManager']}},
								{'contract': 'lendingPoolDataProvider', 'method': 'setStaking', 'params':{'_address': contracts['staking']}}
			]
		self._get_transaction(settings_lendinPoolDataProvider)

	def _config_oToken(self):
		print("-------------------------------Configuring OTOKEN----------------------------------------------------")

		contracts = self.contracts
		settings_oToken =[{'contract': 'oUSDb', 'method': 'setLendingPoolCore', 'params':{'_address':contracts['lendingPoolCore']}},
			{'contract': 'oUSDb', 'method': 'setReserve', 'params':{'_address':contracts['usdb']}},
			{'contract': 'oUSDb', 'method': 'setLendingPoolDataProvider', 'params':{'_address':contracts['lendingPoolDataProvider']}},
			{'contract': 'oUSDb', 'method': 'setLendingPool', 'params':{'_address':contracts['lendingPool']}},
			{'contract': 'oUSDb', 'method': 'setLiquidation', 'params':{'_address':contracts['liquidationManager']}}]

		self._get_transaction(settings_oToken)

	def _config_priceOracleRef(self):
		print("-------------------------------Configuring PRICE ORACLE REFERENCE DATA----------------------------------------------------")

		contracts = self.contracts
		setting_priceOracle =[{'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'USDb','_quote':'USD','_rate':1*10**18}},
					  {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'ICX','_quote':'USD','_rate':15*10**17}},
					  # {'contract': 'priceOracle', 'method': 'set_reference_data', 'params':{'_base':'IUSDC','_quote':'USDC','_rate':10*10**17}}
					  ]

		self._get_transaction(setting_priceOracle)

	def _config_addressProvider(self):
		print("-------------------------------Configuring ADDRESS PROVIDER ----------------------------------------------------")

		contracts = self.contracts
		setting_addressProvider =[  {'contract': 'addressProvider', 'method': 'setLendingPool', 'params':{'_address':contracts['lendingPool']}},
							{'contract': 'addressProvider', 'method': 'setLendingPoolDataProvider', 'params':{'_address':contracts['lendingPoolDataProvider']}},
							{'contract': 'addressProvider', 'method': 'setUSDb', 'params':{'_address':contracts['usdb']}},
							{'contract': 'addressProvider', 'method': 'setoUSDb', 'params':{'_address':contracts['oUSDb']}},
							{'contract': 'addressProvider', 'method': 'setsICX', 'params':{'_address':contracts['sicx']}},
							{'contract': 'addressProvider', 'method': 'setoICX', 'params':{'_address':contracts['oICX']}},
							{'contract': 'addressProvider', 'method': 'setStaking', 'params':{'_address':contracts['staking']}},
							{'contract': 'addressProvider', 'method': 'setIUSDC', 'params':{'_address':contracts['iusdc']}},
							{'contract': 'addressProvider', 'method': 'setoIUSDC', 'params':{'_address':contracts['oIUSDC']}},
							{'contract': 'addressProvider', 'method': 'setOmmToken', 'params':{'_address':contracts['ommToken']}},
							{'contract': 'addressProvider', 'method': 'setDelegation', 'params':{'_address':contracts['delegation']}},
							{'contract': 'addressProvider', 'method': 'setRewards', 'params':{'_address':contracts['rewards']}}
						 ]
		
		self._get_transaction(setting_addressProvider)

	def _config_lendingPoolCoreSettings(self):
		print("-------------------------------Configuring LENDING POOL CORE RESERVE SETTINGS ----------------------------------------------------")

		contracts = self.contracts
		settings_reserves = [{'contract': 'lendingPoolCore', 
						'method': 'setReserveConstants', 
						'params' :{"_constants": [{"reserve":contracts['usdb'],
												   "optimalUtilizationRate":f"8{'0'*17}",
												   "baseBorrowRate":f"2{'0'*16}",
												   "slopeRate1":f"6{'0'*16}",
												   "slopeRate2":f"1{'0'*18}"} ]}},
					 {'contract': 'lendingPoolCore', 
						'method': 'setReserveConstants', 
						'params' :{"_constants": [{"reserve":contracts['sicx'],
													"optimalUtilizationRate":f"8{'0'*17}",
													"baseBorrowRate":f"0{'0'*17}",
													"slopeRate1":f"8{'0'*16}",
													"slopeRate2":f"2{'0'*18}"} ]}},
					{'contract': 'lendingPoolCore', 
						'method': 'setReserveConstants', 
						'params' :{"_constants": [{"reserve":contracts['iusdc'],
													"optimalUtilizationRate":f"8{'0'*17}",
												   "baseBorrowRate":f"2{'0'*16}",
												   "slopeRate1":f"6{'0'*16}",
												   "slopeRate2":f"1{'0'*18}"} ]}}
					]
		
		self._get_transaction(settings_reserves)

	def _config_oICX(self):
		print("-------------------------------Configuring OICX ----------------------------------------------------")

		contracts = self.contracts
		settings_oicx = [{'contract': 'oICX', 'method': 'setLendingPoolCore', 'params':{'_address':contracts['lendingPoolCore']}},
				{'contract': 'oICX', 'method': 'setReserve', 'params':{'_address':contracts['sicx']}},
				{'contract': 'oICX', 'method': 'setLendingPoolDataProvider', 'params':{'_address':contracts['lendingPoolDataProvider']}},
				{'contract': 'oICX', 'method': 'setLendingPool', 'params':{'_address':contracts['lendingPool']}},
				{'contract': 'oICX', 'method': 'setLiquidation', 'params':{'_address':contracts['liquidationManager']}}]

		self._get_transaction(settings_oicx)

	def _config_oIUSDC(self):
		print("-------------------------------Configuring OIUSDC ----------------------------------------------------")

		contracts = self.contracts
		settings_oiusdc = [ {'contract': 'oIUSDC', 'method': 'setLendingPoolCore', 'params':{'_address':contracts['lendingPoolCore']}},
					{'contract': 'oIUSDC', 'method': 'setReserve', 'params':{'_address':contracts['iusdc']}},
					{'contract': 'oIUSDC', 'method': 'setLendingPoolDataProvider', 'params':{'_address':contracts['lendingPoolDataProvider']}},
					{'contract': 'oIUSDC', 'method': 'setLendingPool', 'params':{'_address':contracts['lendingPool']}},
					{'contract': 'oIUSDC', 'method': 'setLiquidation', 'params':{'_address':contracts['liquidationManager']}}
					]
		self._get_transaction(settings_oiusdc)

	def _config_liquidationManager(self):
		print("-------------------------------Configuring LIQUIDATION MANAGER ----------------------------------------------------")

		contracts = self.contracts
		settings_liquidationManager =  [{'contract': 'liquidationManager', 'method': 'setLendingPoolDataProvider', 'params': {'_address':contracts['lendingPoolDataProvider']}},
								{'contract': 'liquidationManager', 'method': 'setLendingPoolCore', 'params': {'_address':contracts['lendingPoolCore']}},
								{'contract': 'liquidationManager', 'method': 'setPriceOracle','params': {'_address':contracts['priceOracle']}},
								# {'contract': 'liquidationManager', 'method': 'setFeeProvider','params': {'_address':contracts['feeProvider']}},
								{'contract': 'liquidationManager', 'method': 'setStaking','params': {'_address':contracts['staking']}}
								]
		self._get_transaction(settings_liquidationManager)

	def _config_delegation(self):
		print("-------------------------------Configuring DELEGATION ----------------------------------------------------")

		contracts = self.contracts
		settings_delegation =[{'contract': 'delegation', 'method': 'setLendingPoolCore','params': {'_address':contracts['lendingPoolCore']}},
					 {'contract':  'delegation', 'method': 'setOmmToken','params': {'_address':contracts['ommToken']}}]
		self._get_transaction(settings_delegation)


	def _config_ommToken(self):
		print("-------------------------------Configuring OMM TOKEN ----------------------------------------------------")

		contracts = self.contracts
		settings_ommToken =[{'contract': 'ommToken', 'method': 'setAdmin','params': {'_admin':contracts['rewards']}},
					{'contract':  'ommToken', 'method': 'setDelegation','params': {'_address':contracts['delegation']}},
					{'contract':  'ommToken', 'method': 'setRewards','params': {'_address':contracts['rewards']}},
					{'contract':  'ommToken', 'method': 'setMinimumStake','params': {'_min':10 * 10**18}},
					{'contract':  'ommToken', 'method': 'setUnstakingPeriod','params': {'_time': 120}}]
		self._get_transaction(settings_ommToken)


	def _config_lendingPoolCore(self):
		print("-------------------------------Configuring LENDING POOL CORE ----------------------------------------------------")

		contracts = self.contracts
		settings_lendingPoolCore =[ {'contract': 'lendingPoolCore', 'method': 'setLendingPool','params': {'_address':contracts['lendingPool']}},
							{'contract': 'lendingPoolCore', 'method': 'setDaoFund','params': {'_address':contracts['daoFund']}},
							{'contract': 'lendingPoolCore', 'method': 'setPriceOracle','params': {'_address':contracts['priceOracle']}},
							{'contract': 'lendingPoolCore', 'method': 'setLiquidationManager','params': {'_address':contracts['liquidationManager']}},
							{'contract': 'lendingPoolCore', 'method': 'setDelegation','params': {'_address':contracts['delegation']}},
							{'contract': 'lendingPoolCore', 'method': 'setStaking','params': {'_address':contracts['staking']}},
							{'contract': 'lendingPoolCore', 'method': 'set_id','params': {'_value':'1'}}]
		
		self._get_transaction(settings_lendingPoolCore)

	# def _config_priceOracle(self):
	# 	print("-------------------------------Configuring PRICE ORACLE -----------------------------------------------------")

	# 	contracts = self.contracts
	# 	settings_priceOracle =[{'contract':  'priceOracle', 'method': 'setBandOracle','params': {'_address':"cx61a36e5d10412e03c907a507d1e8c6c3856d9964"}},
	# 				   {'contract':  'priceOracle', 'method': 'toggleOraclePriceBool','params':{}}]

	# 	tx = self.getTransaction(settings_priceOracle)

	def _config_snapshot(self):
		print("-------------------------------Configuring SNAPSHOT ----------------------------------------------------")

		contracts = self.contracts
		settings_snapshot =[{'contract': 'snapshot', 'method': 'setAdmin','params': {'_address':contracts['lendingPool']}},
					{'contract': 'snapshot', 'method': 'setGovernance','params': {'_address':contracts['governance']}}]
		
		self._get_transaction(settings_snapshot)


	def _config_rewards(self):
		print("-------------------------------Configuring REWARDS ----------------------------------------------------")

		contracts = self.contracts
		settings_rewards=[ {'contract': 'rewards', 'method': 'setLendingPool','params': {'_address':contracts['lendingPool']}},
			{'contract': 'rewards', 'method': 'setOmm','params': {'_address':contracts['ommToken']}},
			{'contract': 'rewards', 'method': 'setLendingPoolCore','params': {'_address':contracts['lendingPoolCore']}},
			{'contract': 'rewards', 'method': 'setSnapshot','params': {'_address':contracts['snapshot']}},
			{'contract': 'rewards', 'method': 'setWorkerToken','params': {'_address':contracts['worker_token']}},
			{'contract': 'rewards', 'method': 'setAdmin','params': {'_address':contracts['governance']}},
			{'contract': 'rewards', 'method': 'setDaoFund','params': {'_address':contracts['daoFund']}},
			{'contract': 'rewards', 'method': 'setLpToken','params': {'_address':"cx291dacbb875a94b364194a5febaac4e6318681f7"}},                  
			]
					
		self._get_transaction(settings_rewards)

	def _config_governance(self):
		print("-------------------------------Configuring GOVERNANCE ----------------------------------------------------")

		contracts = self.contracts
		settings_governance =[
					{'contract': 'governance', 'method': 'setSnapshot','params': {'_address':contracts['snapshot']}},
					{'contract': 'governance', 'method': 'setRewards','params': {'_address':contracts['rewards']}},
					{'contract': 'governance', 'method': 'setStartTimestamp','params': {'_timestamp': 1577854800000000}}
					]
		self._get_transaction(settings_governance)

	def _add_reserves_to_lendingPoolCore(self):
		print("------------------------------- ADDING RESERVES TO LENDING POOL CORE ----------------------------------------------------")

		contracts = self.contracts
		params_iusdc ={"_reserve": {"reserveAddress":contracts['iusdc'],"oTokenAddress":contracts['oIUSDC'],"totalBorrows":"0","lastUpdateTimestamp": "0","liquidityRate":"0","borrowRate":"0","liquidityCumulativeIndex":f"1{'0'*18}","borrowCumulativeIndex":f"1{'0'*18}","baseLTVasCollateral":"500000000000000000","liquidationThreshold":"650000000000000000","liquidationBonus":"100000000000000000","decimals":"6","borrowingEnabled": "1","usageAsCollateralEnabled":"1","isFreezed":"0","isActive":"1"} }
		params_usdb = {"_reserve": {"reserveAddress":contracts['usdb'],"oTokenAddress":contracts['oUSDb'],"totalBorrows":"0","lastUpdateTimestamp": "0","liquidityRate":"0","borrowRate":"0","liquidityCumulativeIndex":f"1{'0'*18}","borrowCumulativeIndex":f"1{'0'*18}","baseLTVasCollateral":"500000000000000000","liquidationThreshold":"650000000000000000","liquidationBonus":"100000000000000000","decimals":"18","borrowingEnabled": "1","usageAsCollateralEnabled":"1","isFreezed":"0","isActive":"1"} }
		params_icx = {"_reserve": {"reserveAddress":contracts['sicx'],"oTokenAddress":contracts['oICX'],"totalBorrows":"0","lastUpdateTimestamp": "0","liquidityRate":"0","borrowRate":"0","liquidityCumulativeIndex":f"1{'0'*18}","borrowCumulativeIndex":f"1{'0'*18}","baseLTVasCollateral":"500000000000000000","liquidationThreshold":"650000000000000000","liquidationBonus":"100000000000000000","decimals":"18","borrowingEnabled": "1","usageAsCollateralEnabled":"1","isFreezed":"0","isActive":"1"} }

		settings = [
					{'contract': 'lendingPoolCore', 'method': 'addReserveData','params': params_iusdc},
					{'contract': 'lendingPoolCore', 'method': 'addReserveData','params': params_usdb},
					{'contract': 'lendingPoolCore', 'method': 'addReserveData','params': params_icx}
				]
		self._get_transaction(settings)

	def _get_transaction(self, settings):
		txs = []
		contracts = self.contracts
		for sett in settings:
			print(f'Calling {sett["method"]}, with parameters {sett["params"]} on the {sett["contract"]} contract.')
			res = self.build_tx(self.deployer_wallet, to=contracts[sett['contract']], method=sett['method'], params=sett['params'])
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