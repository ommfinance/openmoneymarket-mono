from .test_integrate_base import *


def _int(_data):
	return int(_data, 0)

def _dec(_data):
	return int(_data, 0) / 10 ** 18

def _by18(_data):
	return _data / 10**18

EXA = 10 ** 18


class OMMTestCases(OMMTestBase):
	def setUp(self):
		super().setUp()

	def _methods(self, ACTIONS):
		test_cases = ACTIONS

		if test_cases['user'] == "new":
			from_ = KeyWallet.create()
			self.send_icx(self._test1, from_.get_address(), 1000 * EXA )
			tx = self._transferUSDB(self.deployer_wallet, from_.get_address(), 1200 * EXA)
			self.assertEqual(tx['status'], 1)

		for case in test_cases['transactions']:
			print("############################################################")
			print("##################",case["action"], int(case["amount"])/10**18, case["reserve"],"################")
			print("############################################################")

			amount = int(case['amount'])

			if case["reserve"] == "icx":
				case["reserve"] = "sicx"

			if case['user'] == "1":
				from_ = self.deployer_wallet
			elif case['user'] == "2":
				from_ = self._test2
			elif case['user'] == "3":
				from_ = self._test3
			elif case['user'] == "4":
				from_ = self._test4

			#####################################################################
			################### TRANSFER USDB TO ALL WALLETS ####################

			# tx = self._transferUSDB(self.deployer_wallet, self._test2.get_address(), 10000 * EXA )
			# self.assertEqual(tx['status'], 1)
			# tx = self._transferUSDB(self.deployer_wallet, self._test3.get_address(), 10000 * EXA )
			# self.assertEqual(tx['status'], 1)
			# tx = self._transferUSDB(self.deployer_wallet, self._test4.get_address(), 10000 * EXA )
			# self.assertEqual(tx['status'], 1)

			######################################################################

			owner_params = {'_owner':from_.get_address()}

			sicx_reserve_params = {'_reserve': self.contracts[case["reserve"]]}

			user_reserve_params = {
					'_reserve': self.contracts[case["reserve"]], 
					'_user': from_.get_address()
					}

			user_params = {'_user': from_.get_address()}

			self.sicx_rate = self.call_tx(
						to=self.contracts['staking'], 
						method="getTodayRate"
					)

			self.sicx_balance_before = self.call_tx(
				to=self.contracts[case["reserve"]], 
				method="balanceOf",
				params=owner_params
			)

			self.icx_balance_before = self.get_balance(from_.get_address())

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

			################################################################################

			if (case["reserve"] == "sicx" and case['action'] != "deposit"):
				amount = exaDiv(amount, _int(self.sicx_rate))

			tx_result = self._call_method(from_, case['action'], case['reserve'], amount)

			print("EXPECTED: ", case['expectedResult'])
			print("OUTPUT: ", tx_result['status'])

			if case.get('remarks') != None:
				print("Remarks => ", case['remarks'])

			if (tx_result['status'] == 0): 
				print("SCORE MESSAGE: ", tx_result['failure']['message'])
				if case.get('revertMessage') != None:
					print("EXPECTED MESSAGE: ", case['revertMessage'])

			self.assertEqual(tx_result['status'], case['expectedResult'])
			
			################################################################################

			if (tx_result['status'] != 0):

				self.sicx_balance_after = self.call_tx(
					to=self.contracts[case["reserve"]], 
					method="balanceOf",
					params=owner_params
				)

				self.icx_balance_after = self.get_balance(from_.get_address())

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

			if tx_result['status'] == 1:

				if case['reserve'] == "sicx":

					if case['action'] == "deposit":

						## checks for ICX deposit
						expected_rates = self._get_rates(
							_int(self.reserve_data_after['totalBorrows']), 
							_int(self.reserve_data_after['totalLiquidity']), 
							self.contracts[case["reserve"]])		

						self.assertEqual(
							_int(self.reserve_data_after["borrowRate"]), 
							int(expected_rates["borrow_rate"]))

						self.assertEqual(
							_int(self.reserve_data_after["liquidityRate"]), 
							int(expected_rates['liquidity_rate']))

						print("BEFORE: availableLiquidity", _int(self.reserve_data_before['availableLiquidity']))
						print("AFTER: availableLiquidity - amount", _int(self.reserve_data_after['availableLiquidity']) -amount/_int(self.sicx_rate))

						# must be similar, but after value becomes higher because of interest
						self.assertGreaterEqual(
							_int(self.reserve_data_after['availableLiquidity']),
							_int(self.reserve_data_before['availableLiquidity']) + amount/_int(self.sicx_rate)
							)

						# slightly greater because of accured interest
						self.assertGreaterEqual(
							_dec(self.reserve_data_after['totalBorrows']),
							_dec(self.reserve_data_before['totalBorrows'])
							)

						# initially equal, but after borrow, and someone deposit, then borrow rate should be lower
						self.assertGreaterEqual(
							_int(self.reserve_data_before['borrowRate']),
							_int(self.reserve_data_after['borrowRate'])
							)

						# borrow balance should not change
						self.assertEqual(
							_int(self.user_reserve_data_before['principalBorrowBalance']),
							_int(self.user_reserve_data_after['principalBorrowBalance'])
							)

						# principalOToken balance should increase
						self.assertGreaterEqual( 
							_int(self.user_reserve_data_after['principalOTokenBalance']),
							_int(self.user_reserve_data_before['principalOTokenBalance'])
							)

						# more the collateral, can deposit more
						self.assertGreater(
							_int(self.user_account_data_after['availableBorrowsUSD']), 
							_int(self.user_account_data_before['availableBorrowsUSD'])
							)

						# health factor will increase after deposit
						self.assertGreaterEqual(
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
							_dec(self.oicx_balance_before) + exaDiv(amount, _int(self.sicx_rate))/10**18,
							_dec(self.oicx_balance_after),
							places = 3
							)

						# icx balance should decrease
						# self.assertAlmostEqual(
						# 	(self.icx_balance_before - exaDiv(amount, _int(self.sicx_rate)))/10**18,
						# 	(self.icx_balance_after)/10**18,
						# 	places = 0
						# 	)

					if case['action'] == "borrow" :

						# print("Before Borrow: principalBorrowBalance =>", _int(self.user_reserve_data_before['principalBorrowBalance']))
						# print("After Borrow: principalBorrowBalance =>", _int(self.user_reserve_data_after['principalBorrowBalance']))
						# print("\n")

						self.assertGreater(
							_int(self.user_reserve_data_after['principalBorrowBalance']),
							_int(self.user_reserve_data_before['principalBorrowBalance'])
							)

						# print("Before Borrow: borrowRate =>", _int(self.user_reserve_data_before['borrowRate']))
						# print("After Borrow: borrowRate =>", _int(self.user_reserve_data_after['borrowRate']))

						self.assertGreater(
							_int(self.user_reserve_data_after['borrowRate']),
							_int(self.user_reserve_data_before['borrowRate'])
							)

						# print("\n")
						# print("Before Borrow: userBorrowCumulativeIndex =>", _int(self.user_reserve_data_before['userBorrowCumulativeIndex']))
						# print("After Borrow: userBorrowCumulativeIndex =>", _int(self.user_reserve_data_after['userBorrowCumulativeIndex']))
						
						self.assertGreater(
							_int(self.user_reserve_data_after['userBorrowCumulativeIndex']),
							_int(self.user_reserve_data_before['userBorrowCumulativeIndex'])
							)

						# self.assertAlmostEqual(
						# 	_dec(self.user_reserve_data_before['principalBorrowBalance']) + self.borrowAmount/18, 
						# 	_dec(self.user_reserve_data_after['principalBorrowBalance'])
						# 	, 7)

						# print("\n")
						# print("Before Borrow: principalOTokenBalance =>", _int(self.user_reserve_data_before['principalOTokenBalance']))
						# print("After Borrow: principalOTokenBalance =>", _int(self.user_reserve_data_after['principalOTokenBalance']))
						
						self.assertEqual(
							_int(self.user_reserve_data_before['principalOTokenBalance']), 
							_int(self.user_reserve_data_after['principalOTokenBalance'])
							)

						expected_rates = self._get_rates(
							_int(self.reserve_data_after['totalBorrows']), 
							_int(self.reserve_data_after['totalLiquidity']), 
							self.contracts['sicx'])

											
						self.assertGreaterEqual(
							_int(self.reserve_data_before['availableLiquidity']),
							_int(self.reserve_data_after['availableLiquidity']) + amount
							)

						print("\n")
						print("Before Borrow: totalLiquidity =>", _int(self.reserve_data_before['totalLiquidity']))
						print("After Borrow: totalLiquidity =>", _int(self.reserve_data_after['totalLiquidity']))

						self.assertGreaterEqual(
							_int(self.reserve_data_after['totalLiquidity']),
							_int(self.reserve_data_before['totalLiquidity'])
							)

						print("\n")
						print("Before Borrow: totalBorrows =>", _int(self.reserve_data_before['totalBorrows']))
						print("After Borrow: totalBorrows =>", _int(self.reserve_data_after['totalBorrows']))

						self.assertGreaterEqual(
							_int(self.reserve_data_after['totalBorrows']),
							_int(self.reserve_data_before['totalBorrows']) + amount
							)

						self.assertEqual(
							_int(self.reserve_data_after['borrowRate']), 
							expected_rates['borrow_rate']
							)

						self.assertEqual(
							_int(self.reserve_data_after['liquidityRate']), 
							expected_rates['liquidity_rate']
							)

						# after borrow, user can borrow less
						self.assertGreater(
							_int(self.user_account_data_before['availableBorrowsUSD']), 
							_int(self.user_account_data_after['availableBorrowsUSD'])
							)

						# health factor will decrease after borrow
						# self.assertGreater(
						# 	_int(self.user_account_data_before['healthFactor']), 
						# 	_int(self.user_account_data_after['healthFactor'])
						# 	)

						# collateral should remain similar
						self.assertAlmostEqual(
							_dec(self.user_account_data_after['totalCollateralBalanceUSD']), 
							_dec(self.user_account_data_before['totalCollateralBalanceUSD']),
							places = 2
							)

						# sICX should decrease amount
						self.assertGreaterEqual(
							_int(self.sicx_balance_before) + exaMul(amount,_int(self.sicx_rate)),
							_int(self.sicx_balance_after)
							)

						print("1=>",_int(self.sicx_balance_before) + exaMul(amount,_int(self.sicx_rate)))
						print("2=>",_int(self.sicx_balance_after))

						# icx balance should decrease
						self.assertGreaterEqual(
							self.icx_balance_before,
							self.icx_balance_after
							)

					if case['action'] == "redeem":
						# print("\n")
						# print("Redeem Amount",)
						# print("\n")
						# print("Before Redeem: principalBorrowBalance =>", _int(self.user_reserve_data_before['principalBorrowBalance']))
						# print("After Redeem: principalBorrowBalance =>", _int(self.user_reserve_data_after['principalBorrowBalance']))
						
						self.assertEqual(
							_int(self.user_reserve_data_before['principalBorrowBalance']),
							_int(self.user_reserve_data_after['principalBorrowBalance'])
							)

						print("\n")
						print("Before Redeem: principalOTokenBalance =>", _int(self.user_reserve_data_before['principalOTokenBalance']))
						print("After Redeem: principalOTokenBalance =>", _int(self.user_reserve_data_after['principalOTokenBalance']))
						
						self.assertGreaterEqual(
							_int(self.user_reserve_data_before['principalOTokenBalance']),
							_int(self.user_reserve_data_after['principalOTokenBalance'])
							)

						expected_rates = self._get_rates(
							_int(self.reserve_data_after['totalBorrows']), 
							_int(self.reserve_data_after['totalLiquidity']), 
							self.contracts['sicx'])

						# print("\n")
						# print("Before Redeem: availableLiquidity =>", _int(self.reserve_data_before['availableLiquidity']))
						# print("After Redeem: availableLiquidity =>", _int(self.reserve_data_after['availableLiquidity']))
						# print("\n")
						# print("Before Redeem: totalLiquidity =>", _int(self.reserve_data_before['totalLiquidity']))
						# print("After Redeem: totalLiquidity =>", _int(self.reserve_data_after['totalLiquidity']))
						# print("\n")
						# print("Before Redeem: totalBorrows =>", _int(self.reserve_data_before['totalBorrows']))
						# print("After Redeem: totalBorrows =>", _int(self.reserve_data_after['totalBorrows']))

						# self.assertGreaterEqual( # ask dai, SICX or ICX
						# 	_int(self.reserve_data_after['availableLiquidity']) + exaDiv(amount, _int(self.sicx_rate)),
						# 	_int(self.reserve_data_before['availableLiquidity'])
						# 	)
						
						# self.assertGreaterEqual(
						# 	_int(self.reserve_data_after['totalLiquidity']) + exaDiv(amount, _int(self.sicx_rate)),
						# 	_int(self.reserve_data_before['totalLiquidity']) 
						# 	)

						self.assertEqual(
							_int(self.reserve_data_before['totalBorrows']), 
							_int(self.reserve_data_after['totalBorrows'])
							)

						self.assertEqual(
							_int(self.reserve_data_after['borrowRate']), 
							expected_rates['borrow_rate']
							)

						self.assertEqual(
							_int(self.reserve_data_after['liquidityRate']), 
							expected_rates['liquidity_rate']
							)

						self.assertGreaterEqual(
							_int(self.user_account_data_before['availableBorrowsUSD']), 
							_int(self.user_account_data_after['availableBorrowsUSD'])
							)

						# health factor will decrease after redeem
						# self.assertGreater(
						# 	_int(self.user_account_data_before['healthFactor']), 
						# 	_int(self.user_account_data_after['healthFactor'])
						# 	)

						# collateral should decrease
						self.assertGreater(
							_int(self.user_account_data_before['totalCollateralBalanceUSD']), 
							_int(self.user_account_data_after['totalCollateralBalanceUSD'])
							)

						#sICX should decrease by redeem amount
						self.assertGreaterEqual(
							_int(self.sicx_balance_after),
							_int(self.sicx_balance_before) + amount
							)

						# oICX should increase by redeem amount
						self.assertGreaterEqual(
							_int(self.oicx_balance_after) + amount,
							_int(self.oicx_balance_before)
							)

						# icx balance should decrease
						self.assertGreaterEqual(
							self.icx_balance_before,
							self.icx_balance_after - amount
							)

					if case['action'] == "repay":

						# since we pay in sICX, principle borrow balance remains unchanged
						self.assertGreaterEqual(
							_int(self.user_reserve_data_before['principalBorrowBalance']), 
							_int(self.user_reserve_data_after['principalBorrowBalance']))

						self.assertEqual(
							_int(self.user_reserve_data_before['principalOTokenBalance']), 
							_int(self.user_reserve_data_after['principalOTokenBalance'])
							)

						expected_rates = self._get_rates(
							_int(self.reserve_data_after['totalBorrows']), 
							_int(self.reserve_data_after['totalLiquidity']), 
							self.contracts['sicx'])

						# print("Before Repay: availableLiquidity =>", _int(self.reserve_data_before['availableLiquidity']))
						# print("After Repay: availableLiquidity =>", _int(self.reserve_data_after['availableLiquidity']))

						self.assertGreaterEqual(
							_int(self.reserve_data_after['availableLiquidity']),
							_int(self.reserve_data_before['availableLiquidity'])
							)
						# print("\n")
						# print("Before Repay: totalLiquidity =>", _int(self.reserve_data_before['totalLiquidity']))
						# print("After Repay: totalLiquidity =>", _int(self.reserve_data_after['totalLiquidity']))
						self.assertGreaterEqual( 
							_int(self.reserve_data_after['totalLiquidity']),
							_int(self.reserve_data_before['totalLiquidity']))
						# print("\n")
						# print("Before Repay: totalBorrows =>", _int(self.reserve_data_before['totalBorrows']))
						# print("After Repay: totalBorrows =>", _int(self.reserve_data_after['totalBorrows']))

						self.assertGreaterEqual(
							_int(self.reserve_data_before['totalBorrows']),
							_int(self.reserve_data_after['totalBorrows']))

						self.assertEqual(_int(self.reserve_data_after['borrowRate']), expected_rates['borrow_rate'])
						self.assertEqual(_int(self.reserve_data_after['liquidityRate']), expected_rates['liquidity_rate'])

						self.assertGreater(
							_int(self.user_account_data_before["totalBorrowBalanceUSD"]),
							_int(self.user_account_data_after["totalBorrowBalanceUSD"])
							)

						self.assertGreater(
							_int(self.user_account_data_after["availableBorrowsUSD"]),
							_int(self.user_account_data_before["availableBorrowsUSD"])
							)

						# self.assertGreater(
						# 	_int(self.user_account_data_after["healthFactor"]),
						# 	_int(self.user_account_data_before["healthFactor"])
						# 	)

						# collateral should increase
						self.assertGreater(
							_int(self.user_account_data_after['totalCollateralBalanceUSD']), 
							_int(self.user_account_data_before['totalCollateralBalanceUSD'])
							)

						#sICX should decrease on repay
						# self.assertEqual(
						# 	_int(self.sicx_balance_before) - amount,
						# 	_int(self.sicx_balance_after)
						# 	)

						# oICX should 
						self.assertAlmostEqual(
							_dec(self.oicx_balance_before),
							_dec(self.oicx_balance_after),
							4
							)

						# icx balance should decrease
						self.assertGreaterEqual(
							self.icx_balance_before,
							self.icx_balance_after - exaMul(amount, _int(self.sicx_rate))
							)

				if case['reserve'] == "usdb":

					expected_rates = self._get_rates(
							_int(self.reserve_data_after['totalBorrows']), 
							_int(self.reserve_data_after['totalLiquidity']), 
							self.contracts[case['reserve']])

					if (case['action'] == "deposit"):						

						self.assertEqual(
							_int(self.reserve_data_after["totalLiquidity"]), 
							_int(self.reserve_data_before["totalLiquidity"]) + amount)

						self.assertEqual(
							_int(self.reserve_data_after["borrowRate"]), 
							expected_rates["borrow_rate"])

						self.assertEqual(
							_int(self.reserve_data_after["liquidityRate"]), 
							expected_rates['liquidity_rate'])

						oTokenBalance = self.call_tx(
							to=self.contracts["oUSDb"], 
							method="principalBalanceOf",
							params=user_params)

						## interest accured will increase the value after transaction
						self.assertGreaterEqual(
							_int(self.user_reserve_data_after['principalOTokenBalance']),
							_int(self.user_reserve_data_before['principalOTokenBalance']) + amount
							)

						# since someone has already borrowed usdb, on depositing more usdb, the borrow rate should decrease
						self.assertGreaterEqual(
							_int(self.user_reserve_data_before["borrowRate"]),
							_int(self.user_reserve_data_after["borrowRate"])
							)

						# no changes in borrow balances
						self.assertAlmostEqual(
							_dec(self.user_reserve_data_before["currentBorrowBalance"]), 
							_dec(self.user_reserve_data_after["currentBorrowBalance"]),
							places = 3
							)

						self.assertEqual(
							_int(self.user_reserve_data_before["principalBorrowBalance"]), 
							_int(self.user_reserve_data_after["principalBorrowBalance"])
							)

						# asserts
						self.assertGreater(
							_int(self.user_account_data_after["availableBorrowsUSD"]),
							_int(self.user_account_data_before["availableBorrowsUSD"])
							)

					if case['action'] == "borrow":

						self.assertAlmostEqual(
							_dec(self.reserve_data_before['availableLiquidity']), 
							_dec(self.reserve_data_after['availableLiquidity'])+amount/10**18, 
							places = 3
							)

						self.assertAlmostEqual(
							_dec(self.reserve_data_before['totalLiquidity']), 
							_dec(self.reserve_data_after['totalLiquidity']), 
							places = 3
							)

						self.assertAlmostEqual(
							_dec(self.reserve_data_before['totalBorrows']) + amount/10**18, 
							_dec(self.reserve_data_after['totalBorrows']), 
							places = 3
							)

						self.assertEqual(
							_int(self.reserve_data_after['borrowRate']), 
							expected_rates['borrow_rate']
							)

						self.assertEqual(
							_int(self.reserve_data_after['liquidityRate']), 
							expected_rates['liquidity_rate']
							)

					if case['action'] == "redeem":
						self.assertEqual(
							_int(self.user_reserve_data_before['principalBorrowBalance']),
							_int(self.user_reserve_data_after['principalBorrowBalance'])
							)

						self.assertAlmostEqual(
							_dec(self.user_reserve_data_before['principalOTokenBalance']),
							_dec(self.user_reserve_data_after['principalOTokenBalance'])+amount/10**18,
							2
							)

						self.assertEqual(
							_int(self.reserve_data_after['borrowRate']), 
							expected_rates['borrow_rate'])

						self.assertEqual(
							_int(self.reserve_data_after['liquidityRate']), 
							expected_rates['liquidity_rate'])

						self.assertGreaterEqual(							
							_int(self.user_account_data_before['availableBorrowsUSD']), 
							_int(self.user_account_data_after['availableBorrowsUSD']))

						self.assertGreaterEqual(
							_int(self.user_account_data_before['healthFactor']),
							_int(self.user_account_data_after['healthFactor']))

						self.assertGreaterEqual(
							_int(self.user_account_data_after['currentLiquidationThreshold']),
							_int(self.user_account_data_before['currentLiquidationThreshold']))

					if case['action'] == "repay":

						self.assertEqual(
							_int(self.user_reserve_data_before['principalOTokenBalance']), 
							_int(self.user_reserve_data_after['principalOTokenBalance'])
							)

						self.assertGreaterEqual(
							_int(self.reserve_data_after['totalBorrows'])+amount,
							_int(self.reserve_data_after['totalBorrows']))

						self.assertEqual(
							_int(self.reserve_data_after['borrowRate']), 
							expected_rates['borrow_rate'])

						self.assertEqual(
							_int(self.reserve_data_after['liquidityRate']), 
							expected_rates['liquidity_rate'])

						self.assertGreater(
							_int(self.user_account_data_before["totalBorrowBalanceUSD"]),
							_int(self.user_account_data_after["totalBorrowBalanceUSD"])
							)

						self.assertGreater(
							_int(self.user_account_data_after["availableBorrowsUSD"]),
							_int(self.user_account_data_before["availableBorrowsUSD"])
							)

						# self.assertGreater(
						# 	_int(self.user_account_data_after["healthFactor"]),
						# 	_int(self.user_account_data_before["healthFactor"])
						# 	)


	def _call_method(self, _from, method, reserve, amount):
		if reserve == "sicx":
			if method == "deposit":
				tx = self._depositICX(_from, amount)
			if method == "borrow":
				tx = self._borrowICX(_from, amount)
			if method == "redeem":
				tx = self._redeemICX(_from, amount)
			if method == "repay":
				tx = self._repayICX(_from, amount)
		if reserve == "usdb":
			if method == "deposit":
				tx = self._depositUSDB(_from, amount)
			if method == "borrow":
				tx = self._borrowUSDB(_from, amount)
			if method == "redeem":
				tx = self._redeemUSDB(_from, amount)
			if method == "repay":
				tx = self._repayUSDB(_from, amount)

		return tx

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

	def _borrowICX(self, _from, _borrowAmount):

		params ={"_reserve": self.contracts['sicx'], "_amount": _borrowAmount}

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["lendingPool"],
			method="borrow",
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

	def _borrowUSDB(self, _from, _borrowAmount):

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

	def _depositUSDB(self, _from, _depositAmount):

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

	def _redeemUSDB(self, _from, _redeemAmount):

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

	def _repayUSDB(self, _from, _repayAmount):

		repay_data = {'method': 'repay', 'params': {'amount': _repayAmount}}
		data = json.dumps(repay_data).encode('utf-8')
		print(self.contracts['lendingPool'])

		params = {"_to": self.contracts['lendingPool'],
				  "_value": _repayAmount, 
				  "_data": data}

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["usdb"], #USDB contract
			method="transfer",
			params=params
			)
		return tx_result

	def _transferUSDB(self, _from, _to, _transferAmount):

		params = {
			"_to": _to,
			"_value": _transferAmount
		}

		tx_result = self.send_tx(
			from_=_from,
			to=self.contracts["usdb"], #USDB contract
			method="transfer",
			params=params
			)
		return tx_result