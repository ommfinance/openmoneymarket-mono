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
		# with open(os.path.join(DIR_PATH, "scores_address.json"), "r") as file:
		# 	self.contracts = json.load(file)

		self.sicx_rate = self.call_tx(
				to=self.contracts['staking'], 
				method="getTodayRate"
			)

		################################################
		################################################
		self._depositAmount = 2 * 10 ** 18
		self._borrowAmount = exaDiv(5 * 10 ** 17, _int(self.sicx_rate))
		################################################
		self._depositICX(self.deployer_wallet, self._depositAmount)
		self._borrowICX(self.deployer_wallet, self._borrowAmount)
		################################################
		################################################

		reserve_params = {'_reserve': self.contracts['usdb']}

		user_reserve_params = {
			'_reserve': self.contracts['usdb'], 
			'_user': self.deployer_wallet.get_address()
			}

		user_params = {'_user': self.deployer_wallet.get_address()}

		owner_params = {'_owner':self.deployer_wallet.get_address()}

		self._repayAmount = exaDiv(2 * 10 ** 17, _int(self.sicx_rate))

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
			to=self.contracts["lendingPoolDataProvider"], 
			method="getUserAccountData",
			params=user_params)

		## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

		self.tx_result = self._repayICX(self.deployer_wallet, self._repayAmount)

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
			to=self.contracts["lendingPoolDataProvider"], 
			method="getUserAccountData",
			params=user_params)

	def test_check(self):

	# def test_repay_user_reserve_data(self):

		print("\n")
		print("Repay Amount", self._repayAmount)
		print("\n")
		print("Before Repay: principalBorrowBalance =>", _int(self.user_reserve_data_before['principalBorrowBalance']))
		print("After Repay: principalBorrowBalance =>", _int(self.user_reserve_data_after['principalBorrowBalance']))
		### Since we pay it in siCX, principal borrow balance remains unchanged
		self.assertEqual(
			_dec(self.user_reserve_data_before['principalBorrowBalance']), 
			_dec(self.user_reserve_data_after['principalBorrowBalance']))
		print("\n")
		print("Before Repay: principalOTokenBalance =>", _int(self.user_reserve_data_before['principalOTokenBalance']))
		print("After Repay: principalOTokenBalance =>", _int(self.user_reserve_data_after['principalOTokenBalance']))
		self.assertEqual(
			_int(self.user_reserve_data_before['principalOTokenBalance']), 
			_int(self.user_reserve_data_after['principalOTokenBalance'])
			)

	# def test_repay_reserve_data(self):

		expected_rates = self._get_rates(
			_int(self.reserve_data_after['totalBorrows']), 
			_int(self.reserve_data_after['totalLiquidity']), 
			self.contracts['sicx'])

		print("\n")
		print("Repay Amount", self._repayAmount)
		print("\n")
		print("Before Repay: availableLiquidity =>", _int(self.reserve_data_before['availableLiquidity']))
		print("After Repay: availableLiquidity =>", _int(self.reserve_data_after['availableLiquidity']))
		self.assertEqual(
			_dec(self.reserve_data_before['availableLiquidity']),
			_dec(self.reserve_data_after['availableLiquidity'])
			)
		print("\n")
		print("Before Repay: totalLiquidity =>", _int(self.reserve_data_before['totalLiquidity']))
		print("After Repay: totalLiquidity =>", _int(self.reserve_data_after['totalLiquidity']))
		self.assertEqual(
			_dec(self.reserve_data_before['totalLiquidity']), 
			_dec(self.reserve_data_after['totalLiquidity']))
		print("\n")
		print("Before Repay: totalBorrows =>", _int(self.reserve_data_before['totalBorrows']))
		print("After Repay: totalBorrows =>", _int(self.reserve_data_after['totalBorrows']))
		self.assertEqual(_dec(self.reserve_data_before['totalBorrows']),
		 _dec(self.reserve_data_after['totalBorrows']))

		self.assertEqual(_int(self.reserve_data_after['borrowRate']), expected_rates['borrow_rate'])
		self.assertEqual(_int(self.reserve_data_after['liquidityRate']), expected_rates['liquidity_rate'])

	# def test_user_account_data(self):
		# asserts
		self.assertGreater(
			_int(self.user_account_data_before["totalBorrowBalanceUSD"]),
			_int(self.user_account_data_after["totalBorrowBalanceUSD"])
			)

		self.assertGreater(
			_int(self.user_account_data_after["availableBorrowsUSD"]),
			_int(self.user_account_data_before["availableBorrowsUSD"])
			)

		self.assertGreater(
			_int(self.user_account_data_after["healthFactor"]),
			_int(self.user_account_data_before["healthFactor"])
			)

		# collateral should increase
		self.assertGreater(
			_int(self.user_account_data_after['totalCollateralBalanceUSD']), 
			_int(self.user_account_data_before['totalCollateralBalanceUSD'])
			)

		#sICX should decrease on redeem
		self.assertEqual(
			_int(self.sicx_balance_before) - self._repayAmount,
			_int(self.sicx_balance_after)
			)

		# oICX should decrease by repay amount ?? 
		self.assertAlmostEqual(
			_dec(self.oicx_balance_before),
			_dec(self.oicx_balance_after)
			)

		# icx balance should decrease
		self.assertAlmostEqual(
			(self.icx_balance_before - self._repayAmount)/10**18,
			(self.icx_balance_after)/10**18,
			places = 0
			)

		print("Before Repay: availableBorrowsUSD =>", _int(self.user_account_data_before["availableBorrowsUSD"]))
		print("After Repay: availableBorrowsUSD =>", _int(self.user_account_data_after["availableBorrowsUSD"]))
		print("Repay Amount: =>" , self._repayAmount)

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

	def _borrowICX(self, _from, _borrowAmount):

		params ={"_reserve": self.contracts['sicx'], "_amount": _borrowAmount}

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["lendingPool"],
			method="borrow",
			params=params
			)
		return tx_result

	def _repayICX(self, _from, _repayAmount):

		repay_data = {'method': 'repay', 'params': {'amount': _repayAmount}}
		data = json.dumps(repay_data).encode('utf-8')

		params = {"_to": self.contracts['lendingPool'],
				  "_value": _repayAmount, 
				  "_data": data}

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["sicx"], #USDB contract
			method="transfer",
			params=params
			)
		return tx_result
