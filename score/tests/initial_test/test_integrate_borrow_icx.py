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

		self.sicx_rate = self.call_tx(
				to=self.contracts['staking'], 
				method="getTodayRate"
			)

		self.depositAmount = 1 * 10 ** 18 		
		self.borrowAmount = exaDiv(1 * 10 ** 17, _int(self.sicx_rate))

		self._depositICX(self.deployer_wallet, self.depositAmount)

		owner_params = {'_owner':self.deployer_wallet.get_address()}

		sicx_reserve_params = {'_reserve': self.contracts['sicx']}

		user_reserve_params = {
			'_reserve': self.contracts['usdb'], 
			'_user': self.deployer_wallet.get_address()
			}

		user_params = {'_user': self.deployer_wallet.get_address()}

		############################################################

		self.sicx_balance_before = self.call_tx(
				to=self.contracts['sicx'], 
				method="balanceOf",
				params=owner_params
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

		self._borrowICX(self.deployer_wallet, self.borrowAmount)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


		self.sicx_balance_after = self.call_tx(
				to=self.contracts['sicx'], 
				method="balanceOf",
				params=owner_params
			)

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
		# self.assertEqual("hi","hi")

	# def test_borrow_user_reserve_data(self):

		print("\n")
		print("Borrow Amount", self.borrowAmount)
		print("\n")
		print("Before Borrow: principalBorrowBalance =>", _int(self.user_reserve_data_before['principalBorrowBalance']))
		print("After Borrow: principalBorrowBalance =>", _int(self.user_reserve_data_after['principalBorrowBalance']))
		print("\n")
		print("Before Borrow: borrowRate =>", _int(self.user_reserve_data_before['borrowRate']))
		print("After Borrow: borrowRate =>", _int(self.user_reserve_data_after['borrowRate']))
		print("\n")
		print("Before Borrow: userBorrowCumulativeIndex =>", _int(self.user_reserve_data_before['userBorrowCumulativeIndex']))
		print("After Borrow: userBorrowCumulativeIndex =>", _int(self.user_reserve_data_after['userBorrowCumulativeIndex']))
		# self.assertAlmostEqual(
		# 	_dec(self.user_reserve_data_before['principalBorrowBalance']) + self.borrowAmount/18, 
		# 	_dec(self.user_reserve_data_after['principalBorrowBalance'])
		# 	, 7)
		print("\n")
		print("Before Borrow: principalOTokenBalance =>", _int(self.user_reserve_data_before['principalOTokenBalance']))
		print("After Borrow: principalOTokenBalance =>", _int(self.user_reserve_data_after['principalOTokenBalance']))
		# self.assertEqual(_int(self.user_reserve_data_before['principalOTokenBalance']), _int(self.user_reserve_data_after['principalOTokenBalance']))

	# def test_borrow_reserve_data(self):

		expected_rates = self._get_rates(
			_int(self.reserve_data_after['totalBorrows']), 
			_int(self.reserve_data_after['totalLiquidity']), 
			self.contracts['sicx'])

		print("\n")
		print("Borrow Amount", self.borrowAmount)
		print("\n")
		print("Before Borrow: availableLiquidity =>", _int(self.reserve_data_before['availableLiquidity']))
		print("After Borrow: availableLiquidity =>", _int(self.reserve_data_after['availableLiquidity']))
		self.assertAlmostEqual(
			_dec(self.reserve_data_before['availableLiquidity']), 
			_dec(self.reserve_data_after['availableLiquidity'])+self.borrowAmount/10**18, 
			places = 4
			)
		print("\n")
		print("Before Borrow: totalLiquidity =>", _int(self.reserve_data_before['totalLiquidity']))
		print("After Borrow: totalLiquidity =>", _int(self.reserve_data_after['totalLiquidity']))
		self.assertAlmostEqual(
			_dec(self.reserve_data_before['totalLiquidity']), 
			_dec(self.reserve_data_after['totalLiquidity']), 
			places = 4
			)
		print("\n")
		print("Before Borrow: totalBorrows =>", _int(self.reserve_data_before['totalBorrows']))
		print("After Borrow: totalBorrows =>", _int(self.reserve_data_after['totalBorrows']))
		self.assertAlmostEqual(
			_dec(self.reserve_data_before['totalBorrows']) + self.borrowAmount/10**18, 
			_dec(self.reserve_data_after['totalBorrows']), 
			places = 4
			)

		self.assertEqual(_int(self.reserve_data_after['borrowRate']), expected_rates['borrow_rate'])
		self.assertEqual(_int(self.reserve_data_after['liquidityRate']), expected_rates['liquidity_rate'])

	# def test_user_account_data(self):

		self.assertGreater(
			_int(self.user_account_data_before['availableBorrowsUSD']), 
			_int(self.user_account_data_after['availableBorrowsUSD'])
			)

		# health factor will decrease after borrow
		self.assertGreater(
			_int(self.user_account_data_before['healthFactor']), 
			_int(self.user_account_data_after['healthFactor'])
			)

		# collateral should remain similar
		self.assertAlmostEqual(
			_dec(self.user_account_data_after['totalCollateralBalanceUSD']), 
			_dec(self.user_account_data_before['totalCollateralBalanceUSD']),
			places = 2
			)

		# sICX should increase by deposit amount
		self.assertEqual(
			_int(self.sicx_balance_before) + self.borrowAmount,
			_int(self.sicx_balance_after)
			)

		# icx balance should decrease
		self.assertAlmostEqual(
			(self.icx_balance_before)/10**18,
			(self.icx_balance_after)/10**18,
			places = 1
			)

		
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

	def _borrowICX(self, _from, _borrowAmount):

		params ={"_reserve": self.contracts['sicx'], "_amount": _borrowAmount}

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["lendingPool"],
			method="borrow",
			params=params
			)
		return tx_result
