from .test_integrate_base import *
import os
import json
from pprint import pprint

DIR_PATH = os.path.abspath(os.path.dirname(__file__))

def _int(value):
	return int(value, 0 )

def _dec(value):
	return int(value,0) / 10**18

class TestTest(OMMTestBase):

	def setUp(self):
		super().setUp()
		with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
			self.contracts = json.load(file)

		################################################
		################################################
		self._depositAmount = 1 * 10 ** 18
		self._depositICX(self.deployer_wallet, self._depositAmount)
		################################################
		################################################

		self.sicx_rate = self.call_tx(
				to=self.contracts['staking'], 
				method="getTodayRate"
			)

		reserve_params = {'_reserve': self.contracts['usdb']}

		user_reserve_params = {
			'_reserve': self.contracts['usdb'], 
			'_user': self.deployer_wallet.get_address()
			}

		user_account_params = {
			'_user': self.deployer_wallet.get_address()
		}

		owner_params = {'_owner':self.deployer_wallet.get_address()}

		self._redeemAmount = exaDiv(5 * 10 ** 17, _int(self.sicx_rate))

		self.sicx_balance_before = self.call_tx(
				to=self.contracts['sicx'], 
				method="balanceOf",
				params=owner_params
			)

		self.icx_balance_before = self.get_balance(self.deployer_wallet.get_address())
		print("ICX BEFORE: ", self.icx_balance_before)

		self.oicx_balance_before = self.call_tx(
				to=self.contracts['oICX'], 
				method="balanceOf",
				params=owner_params
			)

		self.reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=reserve_params)

		self.user_reserve_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

		self.user_account_data_before = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserAccountData",
			params=user_account_params)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.tx_result = self._redeemICX(self.deployer_wallet, self._redeemAmount)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.sicx_balance_after = self.call_tx(
				to=self.contracts['sicx'], 
				method="balanceOf",
				params=owner_params
			)

		self.icx_balance_after = self.get_balance(self.deployer_wallet.get_address())
		print("ICX AFTER: ", self.icx_balance_after)

		self.oicx_balance_after = self.call_tx(
				to=self.contracts['oICX'], 
				method="balanceOf",
				params=owner_params
			)

		self.reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveData",
			params=reserve_params)

		self.user_reserve_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserReserveData",
			params=user_reserve_params)

		self.user_account_data_after = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserAccountData",
			params=user_account_params)

	def test_check(self):
	# 	self.assertEqual("hi", "hi")

	# def test_redeem_user_reserve_data(self):

		print("\n")
		print("Redeem Amount", self._redeemAmount)
		print("\n")
		print("Before Redeem: principalBorrowBalance =>", _int(self.user_reserve_data_before['principalBorrowBalance']))
		print("After Redeem: principalBorrowBalance =>", _int(self.user_reserve_data_after['principalBorrowBalance']))
		self.assertEqual(
			_int(self.user_reserve_data_before['principalBorrowBalance']),
			_int(self.user_reserve_data_after['principalBorrowBalance'])
			)
		print("\n")
		print("Before Redeem: principalOTokenBalance =>", _int(self.user_reserve_data_before['principalOTokenBalance']))
		print("After Redeem: principalOTokenBalance =>", _int(self.user_reserve_data_after['principalOTokenBalance']))
		self.assertEqual(
			_int(self.user_reserve_data_before['principalOTokenBalance']),
			_int(self.user_reserve_data_after['principalOTokenBalance'])
			)

	# def test_redeem_reserve_data(self):

		expected_rates = self._get_rates(
			_int(self.reserve_data_after['totalBorrows']), 
			_int(self.reserve_data_after['totalLiquidity']), 
			self.contracts['sicx'])

		print("\n")
		print("Redeem Amount", self._redeemAmount)
		print("\n")
		print("Before Redeem: availableLiquidity =>", _int(self.reserve_data_before['availableLiquidity']))
		print("After Redeem: availableLiquidity =>", _int(self.reserve_data_after['availableLiquidity']))
		print("\n")
		print("Before Redeem: totalLiquidity =>", _int(self.reserve_data_before['totalLiquidity']))
		print("After Redeem: totalLiquidity =>", _int(self.reserve_data_after['totalLiquidity']))
		print("\n")
		print("Before Redeem: totalBorrows =>", _int(self.reserve_data_before['totalBorrows']))
		print("After Redeem: totalBorrows =>", _int(self.reserve_data_after['totalBorrows']))

		self.assertEqual(_int(self.reserve_data_before['availableLiquidity']), _int(self.reserve_data_after['availableLiquidity']))
		self.assertEqual(_int(self.reserve_data_before['totalLiquidity']), _int(self.reserve_data_after['totalLiquidity']))
		self.assertEqual(_int(self.reserve_data_before['totalBorrows']), _int(self.reserve_data_after['totalBorrows']))
		self.assertEqual(_int(self.reserve_data_after['borrowRate']), expected_rates['borrow_rate'])
		self.assertEqual(_int(self.reserve_data_after['liquidityRate']), expected_rates['liquidity_rate'])

	# def test_redeem_user_data(self):

		# can borrow less
		self.assertGreater(
			_int(self.user_account_data_before['availableBorrowsUSD']), 
			_int(self.user_account_data_after['availableBorrowsUSD'])
			)

		# health factor will decrease after redeem
		self.assertGreater(
			_int(self.user_account_data_before['healthFactor']), 
			_int(self.user_account_data_after['healthFactor'])
			)

		# collateral should decrease
		self.assertGreater(
			_int(self.user_account_data_before['totalCollateralBalanceUSD']), 
			_int(self.user_account_data_after['totalCollateralBalanceUSD'])
			)

		#sICX should decrease by redeem amount
		self.assertEqual(
			_int(self.sicx_balance_before) + self._redeemAmount,
			_int(self.sicx_balance_after)
			)

		# oICX should increase by deposit amount
		self.assertAlmostEqual(
			_dec(self.oicx_balance_before),
			_dec(self.oicx_balance_after) + self._redeemAmount/10**18
			)

		# icx balance should decrease
		self.assertAlmostEqual(
			(self.icx_balance_before - self._redeemAmount)/10**18,
			(self.icx_balance_after)/10**18,
			places = 0
			)

	def _get_rates(self, totalBorrow, totalLiquidity, reserve) -> dict:
		utilization_rate = exaDiv(totalBorrow, totalLiquidity)

		constants = self.call_tx(
			to=self.contracts['lendingPoolCore'], 
			method="getReserveConstants",
			params={'_reserve': self.contracts['usdb']})

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

	def _redeemICX(self, _from, _redeemAmount):

		params = {
				  "_amount": _redeemAmount,
				  }

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["oICX"],
			method="redeem",
			params=params
			)
		return tx_result
