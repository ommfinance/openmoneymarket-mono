from .test_integrate_base import *
import os
import json
from pprint import pprint

DIR_PATH = os.path.abspath(os.path.dirname(__file__))

def _int(value):
	return int(value, 0 )

def _dec(value):
	return int(value, 0) / 10 ** 18

class TestTest(OMMTestBase):
	def setUp(self):
		super().setUp()
		with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
			self.contracts = json.load(file)

		params = {'_reserve': self.contracts['usdb']}

		reserve_params = {'_reserve': self.contracts['usdb']}

		user_reserve_params = {
			'_reserve': self.contracts['usdb'], 
			'_user': self.deployer_wallet.get_address()
			}
		

		self._depositAmount = 1 * 10 ** 18
		self._borrowAmount = 1 * 10 ** 17

		self._deposit(self.deployer_wallet, self._depositAmount)

		self.reserve_configs = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveConfigurationData",
			params=params)

		self.reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=reserve_params)

		self.user_reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.tx_result = self._borrow(self.deployer_wallet, self._borrowAmount)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=reserve_params)

		self.user_reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

	def test_borrow_user_reserve_data(self):

		print("\n")
		print("Borrow Amount", self._borrowAmount)
		print("\n")
		print("Before Borrow: principalBorrowBalance =>", _int(self.user_reserve_data_before['principalBorrowBalance']))
		print("After Borrow: principalBorrowBalance =>", _int(self.user_reserve_data_after['principalBorrowBalance']))
		# self.assertAlmostEqual(
		# 	_dec(self.user_reserve_data_before['principalBorrowBalance']) + self._borrowAmount/18, 
		# 	_dec(self.user_reserve_data_after['principalBorrowBalance'])
		# 	, 7)
		print("\n")
		print("Before Borrow: principalOTokenBalance =>", _int(self.user_reserve_data_before['principalOTokenBalance']))
		print("After Borrow: principalOTokenBalance =>", _int(self.user_reserve_data_after['principalOTokenBalance']))
		self.assertEqual(_int(self.user_reserve_data_before['principalOTokenBalance']), _int(self.user_reserve_data_after['principalOTokenBalance']))

	def test_borrow_reserve_data(self):

		expected_rates = self._get_rates(
			_int(self.reserve_data_after['totalBorrows']), 
			_int(self.reserve_data_after['totalLiquidity']), 
			self.contracts['usdb'])

		print("\n")
		print("Borrow Amount", self._borrowAmount)
		print("\n")
		print("Before Borrow: availableLiquidity =>", _int(self.reserve_data_before['availableLiquidity']))
		print("After Borrow: availableLiquidity =>", _int(self.reserve_data_after['availableLiquidity']))
		self.assertAlmostEqual(
			_dec(self.reserve_data_before['availableLiquidity']), 
			_dec(self.reserve_data_after['availableLiquidity'])+self._borrowAmount/10**18, 
			places = 4
			)
		print("\n")
		print("Before Borrow: totalLiquidity =>", _int(self.reserve_data_before['totalLiquidity']))
		print("After Borrow: totalLiquidity =>", _int(self.reserve_data_after['totalLiquidity']))
		self.assertAlmostEqual(
			_dec(self.reserve_data_before['totalLiquidity']), 
			_dec(self.reserve_data_after['totalLiquidity']), 
			places = 6
			)
		print("\n")
		print("Before Borrow: totalBorrows =>", _int(self.reserve_data_before['totalBorrows']))
		print("After Borrow: totalBorrows =>", _int(self.reserve_data_after['totalBorrows']))
		self.assertAlmostEqual(
			_dec(self.reserve_data_before['totalBorrows']) + self._borrowAmount/10**18, 
			_dec(self.reserve_data_after['totalBorrows']), 
			places = 6
			)

		self.assertEqual(_int(self.reserve_data_after['borrowRate']), expected_rates['borrow_rate'])
		self.assertEqual(_int(self.reserve_data_after['liquidityRate']), expected_rates['liquidity_rate'])

	def _get_rates(self, totalBorrow, totalLiquidity, reserve) -> dict:
		utilization_rate = exaDiv(totalBorrow, totalLiquidity)

		constants = self.call_tx(
			to=self.contracts['lendingPoolCore'], 
			method="getReserveConstants",
			params={'_reserve': reserve})

		optimal_rate = _int(constants['optimalUtilizationRate'])
		slope_rate_1 = _int(constants['slopeRate1'])
		slope_rate_2 = _int(constants['slopeRate2'])
		base_borrow = _int(constants['baseBorrowRate'])

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

	def _borrow(self, _from, _borrowAmount):

		params = {
				  "_reserve": self.contracts['usdb'],
				  "_amount": _borrowAmount,
				  }
		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["lendingPool"],
			method="borrow",
			params=params
			)
		return tx_result
