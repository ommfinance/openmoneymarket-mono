from .test_integrate_base import *
import os
import json
from pprint import pprint
from prettytable import PrettyTable

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


def _int(_data):
	return int(_data, 0)

def _dec(_data):
	return int(_data, 0) / 10 ** 18

class TestTest(OMMTestBase):

	def setUp(self):
		super().setUp()

		self.depositAmount = 5 * 10 ** 18

		owner_params = {'_owner':self.deployer_wallet.get_address()}

		sicx_reserve_params = {'_reserve': self.contracts['sicx']}

		user_reserve_params = {
			'_reserve': self.contracts['sicx'], 
			'_user': self.deployer_wallet.get_address()
			}

		user_params = {'_user': self.deployer_wallet.get_address()}

		############################################################

		self.sicx_rate = self.call_tx(
				to=self.contracts['staking'], 
				method="getTodayRate"
			)

		self.icx_balance_before = self.get_balance(self.deployer_wallet.get_address())

		self.oicx_balance_before = self.call_tx(
				to=self.contracts['oICX'], 
				method="balanceOf",
				params=owner_params
			)

		self.reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=sicx_reserve_params)

		self.user_reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

		self.user_account_data_before = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"], 
			method="getUserAccountData",
			params=user_params)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.tx_result = self._depositICX(self.deployer_wallet, self.depositAmount)
		pprint(self.tx_result)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


		self.icx_balance_after = self.get_balance(self.deployer_wallet.get_address())

		self.oicx_balance_after = self.call_tx(
				to=self.contracts['oICX'], 
				method="balanceOf",
				params=owner_params
			)

		self.reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=sicx_reserve_params)

		self.user_reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

		self.user_account_data_after = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"], 
			method="getUserAccountData",
			params=user_params)

	def test_check(self):

	# def test_deposit_reserve_data(self):

		expected_rates = self._get_rates(
			_dec(self.reserve_data_after['totalBorrows']), 
			_dec(self.reserve_data_after['totalLiquidity']), 
			self.contracts['sicx'])		

		self.assertEqual(
			_int(self.reserve_data_after["borrowRate"]), 
			expected_rates["borrow_rate"])

		self.assertEqual(
			_int(self.reserve_data_after["liquidityRate"]), 
			expected_rates['liquidity_rate'])

		self.assertAlmostEqual(
			_dec(self.reserve_data_before['availableLiquidity']),
			_dec(self.reserve_data_after['availableLiquidity']) - self.depositAmount/10**18,
			places=1
			)

		self.assertAlmostEqual(
			_dec(self.reserve_data_before['totalLiquidity']),
			_dec(self.reserve_data_after['totalLiquidity']) - self.depositAmount/10**18,
			places=1
			)

		self.assertAlmostEqual(
			_dec(self.reserve_data_before['totalBorrows']),
			_dec(self.reserve_data_after['totalBorrows']),
			places=1
			)

		# initially equal, but after borrow, and someone deposit, then borrow rate should be lower
		self.assertGreaterEqual(
			_int(self.reserve_data_before['borrowRate']),
			_int(self.reserve_data_after['borrowRate']),
			)


	# def test_deposit_user_reserve_data(self):

		self.assertEqual(
			_int(self.user_reserve_data_before['principalBorrowBalance']),
			_int(self.user_reserve_data_after['principalBorrowBalance'])
			)

		self.assertGreaterEqual( 
			_int(self.user_reserve_data_after['principalOTokenBalance']),
			_int(self.user_reserve_data_before['principalOTokenBalance'])
			)

	# def test_deposit_user_data(self):
		# more the collateral, can deposit more
		self.assertGreater(
			_int(self.user_account_data_after['availableBorrowsUSD']), 
			_int(self.user_account_data_before['availableBorrowsUSD'])
			)

		# health factor will increase after deposit
		self.assertGreater(
			_int(self.user_account_data_after['healthFactor']), 
			_int(self.user_account_data_before['healthFactor'])
			)

		# collateral should increase
		self.assertGreater(
			_int(self.user_account_data_after['totalCollateralBalanceUSD']), 
			_int(self.user_account_data_before['totalCollateralBalanceUSD'])
			)

		# oICX should increase by deposit amount
		self.assertAlmostEqual(
			_dec(self.oicx_balance_before) + exaDiv(self.depositAmount, _int(self.sicx_rate))/10**18,
			_dec(self.oicx_balance_after),
			places = 3
			)

		# icx balance should decrease
		self.assertAlmostEqual(
			(self.icx_balance_before - exaDiv(self.depositAmount, _int(self.sicx_rate)))/10**18,
			(self.icx_balance_after)/10**18,
			places = 1
			)


	def _get_rates(self, totalBorrow, totalLiquidity, reserve) -> dict:
		if totalBorrow == 0:
			utilization_rate = 0
		else:
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

	def _depositICX(self, _from, _depositAmount):

		params = {"_amount": _depositAmount}
		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["lendingPool"], 
			value=_depositAmount,
			method="deposit",
			params=params
			)
		return tx_result
