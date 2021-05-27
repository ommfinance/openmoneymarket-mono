from .test_integrate_base import *
import os
import json
from pprint import pprint

DIR_PATH = os.path.abspath(os.path.dirname(__file__))

def _int(value):
	return int(value, 0 )

class TestTest(OMMTestBase):

	def setUp(self):
		super().setUp()
		with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
			self.contracts = json.load(file)

		params = {'_reserve': self.contracts['usdb']}

		################################################
		################################################
		self._depositAmount = 5 * 10 ** 18
		################################################
		self._deposit(self.deployer_wallet, self._depositAmount)
		################################################
		################################################

		self.reserve_configs = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'], 
			method="getReserveConfigurationData",
			params=params)

		reserve_params = {'_reserve': self.contracts['usdb']}

		user_reserve_params = {
			'_reserve': self.contracts['usdb'], 
			'_user': self.deployer_wallet.get_address()
			}

		user_account_params = {
			'_user': self.deployer_wallet.get_address()
		}

		self._redeemAmount = 1 * 10 ** 18

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

		self.tx_result = self._redeem(self.deployer_wallet, self._redeemAmount)

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
			to=self.contracts['lendingPoolDataProvider'], 
			method="getUserAccountData",
			params=user_account_params)

	def test_redeem_user_reserve_data(self):

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
			_int(self.user_reserve_data_after['principalOTokenBalance']+self._redeemAmount)
			)
		self.assertEqual(self.user_reserve_data_after['useAsCollateral'], '0x1')

	def test_redeem_reserve_data(self):

		expected_rates = self._get_rates(
			_int(self.reserve_data_after['totalBorrows']), 
			_int(self.reserve_data_after['totalLiquidity']), 
			self.contracts['usdb'])

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

		self.assertEqual(_int(self.reserve_data_after['borrowRate']), expected_rates['borrow_rate'])
		self.assertEqual(_int(self.reserve_data_after['liquidityRate']), expected_rates['liquidity_rate'])

	def test_redeem_user_data(self):
		print("\n")
		print("Redeem Amount: ", self._redeemAmount)
		print("\n")
		# print("Before Redeem: totalBorrowBalanceUSD =>", _int(self.user_account_data_before['totalBorrowBalanceUSD']))
		# print("After Redeem: totalBorrowBalanceUSD =>", _int(self.user_account_data_after['totalBorrowBalanceUSD']))
		# print("\n")
		# print("Before Redeem: totalCollateralBalanceUSD =>", _int(self.user_account_data_before['totalCollateralBalanceUSD']))
		# print("After Redeem: totalCollateralBalanceUSD =>", _int(self.user_account_data_after['totalCollateralBalanceUSD']))
		# print("\n")
		# print("Before Redeem: totalLiquidityBalanceUSD =>", _int(self.user_account_data_before['totalLiquidityBalanceUSD']))
		# print("After Redeem: totalLiquidityBalanceUSD =>", _int(self.user_account_data_after['totalLiquidityBalanceUSD']))
		print("\n")
		print("Before Redeem: availableBorrowsUSD =>", _int(self.user_account_data_before['availableBorrowsUSD']))
		print("After Redeem: availableBorrowsUSD =>", _int(self.user_account_data_after['availableBorrowsUSD']))

		self.assertEqual(
			(
				_int(self.user_account_data_before['availableBorrowsUSD']) > 
				_int(self.user_account_data_after['availableBorrowsUSD'])
			), True )

		self.assertGreaterEqual(
				_int(self.user_account_data_before['healthFactor']),
				_int(self.user_account_data_after['healthFactor'])
			)

		self.assertGreaterEqual(
				_int(self.user_account_data_after['currentLiquidationThreshold']),
				_int(self.user_account_data_before['currentLiquidationThreshold'])
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

	def _redeem(self, _from, _redeemAmount):

		params = {
				  "_amount": _redeemAmount,
				  }

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["oUSDb"],
			method="redeem",
			params=params
			)
		return tx_result
