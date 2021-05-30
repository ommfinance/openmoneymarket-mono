from .test_integrate_base import *
import os
import json
from pprint import pprint
from prettytable import PrettyTable

DIR_PATH = os.path.abspath(os.path.dirname(__file__))

class TestTest(OMMTestBase):

	def setUp(self):
		super().setUp()
		with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
			self.contracts = json.load(file)

		params = {'_reserve': self.contracts['usdb']}

		self.reserve_configs = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveConfigurationData",
			params=params)

		reserve_params = {'_reserve': self.contracts['usdb']}

		user_reserve_params = {
			'_reserve': self.contracts['usdb'], 
			'_user': self.deployer_wallet.get_address()
			}

		self._depositAmount = 1 * 10 ** 18

		self.reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=reserve_params)

		self.user_reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

		user_params = {'_user': self.deployer_wallet.get_address()}

		self.user_account_data_before = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"], 
			method="getUserAccountData",
			params=user_params)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.tx_result = self._deposit(self.deployer_wallet, self._depositAmount)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=reserve_params)

		self.user_reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

		self.user_account_data_after = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"], 
			method="getUserAccountData",
			params=user_params)
		

	def test_check(self):
	# 	self.assertEqual("Hello","Hello")

	# def test_reserve_configuration_data(self):

		# params while adding reserves to lending pool core
		reserves = {
			"baseLTVasCollateral":"500000000000000000",
			"liquidationThreshold":"650000000000000000",
			"liquidationBonus":"100000000000000000",
			"decimals":"18",
			"borrowingEnabled": "1",
			"usageAsCollateralEnabled":"1",
			"isActive":"1"
			}

		self.assertEqual(int(self.reserve_configs['baseLTVasCollateral'],0), int(reserves['baseLTVasCollateral']))
		self.assertEqual(int(self.reserve_configs['liquidationThreshold'],0), int(reserves['liquidationThreshold']))
		self.assertEqual(self.reserve_configs['usageAsCollateralEnabled'], '0x1')
		self.assertEqual(self.reserve_configs['borrowingEnabled'], '0x1')
		self.assertEqual(self.reserve_configs['isActive'], '0x1')
		self.assertEqual(int(self.reserve_configs['liquidationBonus'],0), int(reserves['liquidationBonus']))

	# def test_deposit_reserve_data(self):

		expected_rates = self._get_rates(
			self._int(self.reserve_data_after['totalBorrows']), 
			self._int(self.reserve_data_after['totalLiquidity']), 
			self.contracts['usdb'])

		print("Before Deposit: totalLiquidity => ",self._int(self.reserve_data_before["totalLiquidity"]))
		print("After Deposit: totalLiquidity => ",self._int(self.reserve_data_after["totalLiquidity"]))
		print("totalLiquidityBefore + depositAmount => ", self._int(self.reserve_data_before["totalLiquidity"])+self._depositAmount)

		self.assertEqual(self._int(self.reserve_data_after["totalLiquidity"]), self._int(self.reserve_data_before["totalLiquidity"])+self._depositAmount)
		self.assertEqual(self._int(self.reserve_data_after["borrowRate"]), expected_rates["borrow_rate"])
		self.assertEqual(self._int(self.reserve_data_after["liquidityRate"]), expected_rates['liquidity_rate'])
		self.assertEqual(self._int(self.reserve_data_after['liquidationThreshold']), self._int(self.reserve_data_before['liquidationThreshold']))

	# def test_deposit_user_reserve_data(self):

		otoken_params = {
			'_user': self.deployer_wallet.get_address()
		}

		otoken_principal_balance = self.call_tx(
			to=self.contracts["oUSDb"], 
			method="principalBalanceOf",
			params=otoken_params)

		minted_amount = self._int(self.tx_result['eventLogs'][3]['data'][0])

		# asserts
		self.assertEqual(self.user_reserve_data_after['principalOTokenBalance'], otoken_principal_balance)

		print("Before Deposit: principalOTokenBalance => ", self._int(self.user_reserve_data_before['principalOTokenBalance']))
		print("After Deposit: principalOTokenBalance => ", self._int(self.user_reserve_data_after['principalOTokenBalance']))

		## interest accured will increase the value after transaction
		self.assertGreaterEqual(
			self._int(self.user_reserve_data_after['principalOTokenBalance']),
			self._int(self.user_reserve_data_before['principalOTokenBalance']) + self._depositAmount
			)

		# since someone has already borrowed usdb, on depositing more usdb, the borrow rate should decrease
		self.assertEqual(
			(self._int(self.user_reserve_data_before["borrowRate"]) - self._int(self.user_reserve_data_after["borrowRate"])) > 0, 
			True)

		# no changes in borrow balances
		self.assertAlmostEqual(
			self._int(self.user_reserve_data_before["currentBorrowBalance"])/10**18, 
			self._int(self.user_reserve_data_after["currentBorrowBalance"])/10**18,
			places = 6
			)

		self.assertEqual(
			self._int(self.user_reserve_data_before["principalBorrowBalance"]), 
			self._int(self.user_reserve_data_after["principalBorrowBalance"])
			)

	# def test_user_account_data(self):

		# asserts
		self.assertGreater(
			self._int(self.user_account_data_after["availableBorrowsUSD"]),
			self._int(self.user_account_data_before["availableBorrowsUSD"])
			)
		
		self.assertEqual(self._int(self.user_account_data_after['healthFactorBelowThreshold']), False)

	def _get_rates(self, totalBorrow, totalLiquidity, reserve) -> dict:
		utilization_rate = exaDiv(totalBorrow, totalLiquidity)

		constants = self.call_tx(
			to=self.contracts['lendingPoolCore'], 
			method="getReserveConstants",
			params={'_reserve': self.contracts['usdb']})

		optimal_rate = self._int(constants['optimalUtilizationRate'])
		slope_rate_1 = self._int(constants['slopeRate1'])
		slope_rate_2 = self._int(constants['slopeRate2'])
		base_borrow = self._int(constants['baseBorrowRate'])

		if utilization_rate < optimal_rate:
			borrow_rate = base_borrow + exaMul(
				exaDiv(utilization_rate, optimal_rate), slope_rate_1)
		else:
			borrow_rate = base_borrow + slope_rate_1 + exaMul(
				exaDiv((utilization_rate - optimal_rate),
					   (EXA - optimal_rate)), slope_rate_2)

		liquidity_rate = exaMul(exaMul(borrow_rate, utilization_rate), 9 * EXA // 10)
		return {"borrow_rate":borrow_rate, "liquidity_rate":liquidity_rate}

	def _deposit(self, _from, _depositAmount):

		depositData = {'method': 'deposit', 'params': {'amount': _depositAmount}}

		data = json.dumps(depositData).encode('utf-8')
		params = {"_to": self.contracts['lendingPool'],
				  "_value": _depositAmount, 
				  "_data": data}
		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["usdb"], #USDB contract
			method="transfer",
			params=params
			)
		return tx_result

	def _int(self, _data):
		return int(_data, 0)