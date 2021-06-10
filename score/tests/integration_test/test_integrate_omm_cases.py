from pprint import pprint
from iconsdk.wallet.wallet import KeyWallet
from .test_integrate_omm_utils import OmmUtils
from ..actions.user_all_txn_usds_reserve import ACTIONS as USDB_CASES
from ..actions.user_all_txn_icx_reserve import ACTIONS as ICX_CASES
from ..actions.user_all_txns_multiple_reserve import ACTIONS as BOTH_CASES
from ..actions.steps import Steps

EXA = 10 ** 18
halfEXA = EXA // 2

def _int(_data):
	return int(_data, 0)

def _dec(_data):
	return int(_data, 0) / EXA

def _by18(_data):
	return _data / EXA

def exaDiv(a: int, b: int) -> int:
	halfB = b // 2
	return (halfB + (a * EXA)) // b

def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a * b)) // EXA

class OMMTestCases(OmmUtils):
	def setUp(self):
		super().setUp()

	def test_01_icx_cases(self):
		self._execute(ICX_CASES)

	def test_02_usds_cases(self):
		self._execute(USDB_CASES)

	def test_03_multi_reserve_cases(self):
		self._execute(BOTH_CASES)

	def initialize_user(self, name):
		self.users = {}
		user = KeyWallet.create()
		self.send_icx(self.deployer_wallet, user.get_address(), 1000 * EXA)
		tx = self._transferUSDS(self.deployer_wallet, user.get_address(), 5000 * EXA)
		self.assertEqual(tx['status'], 1)
		# self._transferSICX(self.deployer_wallet, user.get_address(), 1000 * EXA)
		self.users[name] = user

	def _check_tx_result(self, tx_result, case):

		print("EXPECTED: ", case['expectedResult'])
		print("OUTPUT: ", tx_result['status'])

		if case.get('remarks') != None:
			print("Remarks => ", case['remarks'])

		if (tx_result['status'] == 0): 
			print("SCORE MESSAGE: ", tx_result['failure']['message'])
			if case.get('revertMessage') != None:
				print("EXPECTED MESSAGE: ", case['revertMessage'])

		self.assertEqual(tx_result['status'], case['expectedResult'])

	def _set_user_reserve_data(self, key):
		user_sicx_reserve_params = {
					'_reserve': self.contracts["sicx"], 
					'_user': self._user.get_address()
					}
		user_usds_reserve_params = {
					'_reserve': self.contracts["usds"], 
					'_user': self._user.get_address()
					}

		self.values[key][self.user]['reserve_data']['sicx'] = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"],
			method="getUserReserveData",
			params=user_sicx_reserve_params
		)

		self.values[key][self.user]['reserve_data']['usds'] = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"],
			method="getUserReserveData",
			params=user_usds_reserve_params
		)

	def _set_reserve_data(self, key):
		sicx_params = {'_reserve': self.contracts["sicx"]}
		usds_params = {'_reserve': self.contracts["usds"]}

		self.values[key]["reserve"]["sicx"] = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'],
			method="getReserveData",
			params=sicx_params)

		self.values[key]["reserve"]["usds"] = self.call_tx(
			to=self.contracts['lendingPoolDataProvider'],
			method="getReserveData",
			params=usds_params)

	def _set_user_data(self, key):
		user_params = {'_user': self._user.get_address()}
		# user 1 dynamic
		self.values[key][self.user]['account_data'] = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"],
			method="getUserAccountData",
			params=user_params
		)

	def _set_user_balances(self, key):

		self.values[key][self.user]['balances']['sicx'] = self.call_tx(
				to=self.contracts["sicx"], 
				method="balanceOf",
				params={'_owner': self._user.get_address()}
			)

		self.values[key][self.user]['balances']['icx'] = self.get_balance(self._user.get_address())

		self.values[key][self.user]['balances']['oicx'] = self.call_tx(
				to=self.contracts['oICX'], 
				method="balanceOf",
				params={'_owner': self._user.get_address()}
			)

		self.values[key][self.user]['balances']['usds'] = self.call_tx(
				to=self.contracts['usds'], 
				method="balanceOf",
				params={'_owner': self._user.get_address()}
			)

		self.values[key][self.user]['balances']['ousds'] = self.call_tx(
				to=self.contracts['oUSDs'], 
				method="balanceOf",
				params={'_owner': self._user.get_address()}
			)

	def _before_tx(self):
		self._set_user_data("before")
		self._set_user_balances("before")
		self._set_user_reserve_data("before")
		self._set_reserve_data("before")

	def _after_tx(self):
		self._set_user_data("after")
		self._set_user_balances("after")
		self._set_user_reserve_data("after")
		self._set_reserve_data("after")

	def _execute(self, task):
		print("\n", task.get("description"))

		self.values = {
			"before": {
				"user1": {
					"account_data": {},
					"reserve_data": {
						"sicx": {},
						"usds": {}
					},
					"balances": {
						"sicx": {},
						"icx": {},
						"oicx": {},
						"usds": {},
						"ousds": {}
					}
				},
				"reserve": {
					"sicx": {},
					"usds": {}
				}
			},
			"after": {
				"user1":{
					"account_data": {},
					"reserve_data": {
						"sicx": {},
						"usds": {}
					},
					"balances": {
						"sicx": {},
						"icx": {},
						"oicx": {},
						"usds": {},
						"ousds": {}
					}},
				"reserve": {
					"sicx": {},
					"usds": {}
				}
			}
		}

		self.initialize_user("user1")

		for case in task["transactions"]:
			_step = case.get("_step")
			self.user = case.get("user")
			self._user = self.users.get(self.user)
			_user = self.users.get(self.user)
			self.amount = case.get("amount")
			amount = case.get("amount")
			print(f"#################################{_step} by {self.user}####################################")

			user = self.users.get("user1")

			#######################
			# Before transactions #
			#######################
			self.sicx_rate = self.call_tx(
				to=self.contracts['staking'], 
				method="getTodayRate"
			)

			if _step == Steps.DEPOSIT_ICX:

				self._before_tx()

				tx_res = self._depositICX(_user, amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()
					self._deposit_icx_checks()

			elif _step == Steps.BORROW_ICX:
				self._before_tx()

				self.amount = exaDiv(amount, _int(self.sicx_rate))
				tx_res = self._borrowICX(_user, self.amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()
					self._borrow_icx_checks()

			elif _step == Steps.REDEEM_ICX:
				self._before_tx()

				self.amount = exaDiv(amount, _int(self.sicx_rate))
				tx_res = self._redeemICX(_user, self.amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()					
					self._redeem_icx_checks()

			elif _step == Steps.REPAY_ICX:
				self._before_tx()

				self.amount = exaDiv(amount, _int(self.sicx_rate))
				tx_res = self._repayICX(_user, self.amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()					
					self._repay_icx_checks()

			elif _step == Steps.DEPOSIT_USDS:
				self._before_tx()

				tx_res = self._depositUSDS(_user, amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()					
					self._deposit_usds_checks()

			elif _step == Steps.BORROW_USDS:
				self._before_tx()

				tx_res = self._borrowUSDS(_user, amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()					
					self._borrow_usds_checks()

			elif _step == Steps.REDEEM_USDS:
				self._before_tx()

				tx_res = self._redeemUSDS(_user, amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()
					self._redeem_usds_checks()

			elif _step == Steps.REPAY_USDS:
				self._before_tx()

				tx_res = self._repayUSDS(_user, amount)
				self._check_tx_result(tx_res, case)

				if tx_res.get("status") == 1:
					self._after_tx()
					self._repay_usds_checks()

	def _deposit_icx_checks(self):

		sicx_reserve_data_before = self.values["before"]["reserve"]["sicx"]
		sicx_reserve_data_after = self.values["after"]["reserve"]["sicx"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		sicx_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["sicx"]
		sicx_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["sicx"]

		oicx_balance_before = self.values["before"][self.user]['balances']['oicx']
		oicx_balance_after = self.values["after"][self.user]['balances']['oicx']

		amount = self.amount

		expected_rates = self._get_rates(
			_int(sicx_reserve_data_after.get('totalBorrows')), 
			_int(sicx_reserve_data_after.get('totalLiquidity')), 
			self.contracts["sicx"])

		self.assertEqual(
			_int(sicx_reserve_data_after.get("borrowRate")), 
			int(expected_rates["borrow_rate"]))

		self.assertEqual(
			_int(sicx_reserve_data_after.get("liquidityRate")), 
			int(expected_rates['liquidity_rate']))

		# must be similar, but after value becomes higher because of interest
		self.assertGreaterEqual(
			_int(sicx_reserve_data_after['availableLiquidity']),
			_int(sicx_reserve_data_before['availableLiquidity']) + 
			amount/_int(self.sicx_rate)
			)

		# slightly greater because of accured interest
		self.assertGreaterEqual(
			_int(sicx_reserve_data_after['totalBorrows']),
			_int(sicx_reserve_data_before['totalBorrows'])
		)

		# initially equal, but after borrow, and someone deposit, then borrow rate should be lower
		self.assertGreaterEqual(
				_int(sicx_reserve_data_before['borrowRate']),
				_int(sicx_reserve_data_after['borrowRate'])
			)

		# borrow balance should not change
		self.assertEqual(
				_int(sicx_user_reserve_data_before['principalBorrowBalance']),
				_int(sicx_user_reserve_data_after['principalBorrowBalance'])
			)

		# principalOToken balance should increase
		self.assertGreaterEqual( 
			_int(sicx_user_reserve_data_after['principalOTokenBalance']),
			_int(sicx_user_reserve_data_before['principalOTokenBalance'])
		)

		# more the collateral, can deposit more
		self.assertGreater(
			_int(user_account_data_after['availableBorrowsUSD']), 
			_int(user_account_data_before['availableBorrowsUSD'])
		)

		# health factor will increase after deposit
		self.assertGreaterEqual(
			_int(user_account_data_after['healthFactor']), 
			_int(user_account_data_before['healthFactor'])
		)

		# collateral should increase
		self.assertGreater(
			_int(user_account_data_after['totalCollateralBalanceUSD']), 
			_int(user_account_data_before['totalCollateralBalanceUSD'])
		)

		# oICX should increase by deposit amount
		self.assertAlmostEqual(
			_dec(oicx_balance_before) + exaDiv(amount, _int(self.sicx_rate))/10**18,
			_dec(oicx_balance_after),
			places = 3
		)
		
	def _borrow_icx_checks(self):
		sicx_reserve_data_before = self.values["before"]["reserve"]["sicx"]
		sicx_reserve_data_after = self.values["after"]["reserve"]["sicx"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		sicx_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["sicx"]
		sicx_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["sicx"]

		sicx_balance_before = self.values["before"][self.user]['balances']['sicx']
		sicx_balance_after = self.values["after"][self.user]['balances']['sicx']

		amount = self.amount

		self.assertGreater(
			_int(sicx_user_reserve_data_after['principalBorrowBalance']),
			_int(sicx_user_reserve_data_before ['principalBorrowBalance'])
		)

		self.assertGreater(
			_int(sicx_user_reserve_data_after['borrowRate']),
			_int(sicx_user_reserve_data_before ['borrowRate'])
		)

		self.assertGreater(
			_int(sicx_user_reserve_data_after['userBorrowCumulativeIndex']),
			_int(sicx_user_reserve_data_before ['userBorrowCumulativeIndex'])
		)

		self.assertEqual(
			_int(sicx_user_reserve_data_before ['principalOTokenBalance']), 
			_int(sicx_user_reserve_data_after['principalOTokenBalance'])
		)

		expected_rates = self._get_rates(
			_int(sicx_reserve_data_after['totalBorrows']), 
			_int(sicx_reserve_data_after['totalLiquidity']), 
			self.contracts['sicx']
		)
											
		self.assertGreaterEqual(
			_int(sicx_reserve_data_before['availableLiquidity']),
			_int(sicx_reserve_data_after['availableLiquidity']) + amount
		)
		
		self.assertGreaterEqual(
			_int(sicx_reserve_data_after['totalBorrows']),
			_int(sicx_reserve_data_before['totalBorrows']) + amount
		)

		self.assertEqual(
			_int(sicx_reserve_data_after['borrowRate']), 
			expected_rates['borrow_rate']
			)

		self.assertEqual(
			_int(sicx_reserve_data_after['liquidityRate']), 
			expected_rates['liquidity_rate']
			)

		# after borrow, user can borrow less
		self.assertGreater(
			_int(user_account_data_before['availableBorrowsUSD']), 
			_int(user_account_data_after['availableBorrowsUSD'])
			)

		# collateral should remain similar
		self.assertGreaterEqual(
			_dec(user_account_data_after['totalCollateralBalanceUSD']), 
			_dec(user_account_data_before['totalCollateralBalanceUSD'])
		)

		# user gets sicx
		self.assertGreaterEqual(
			_int(sicx_balance_before) + exaMul(amount,_int(self.sicx_rate)),
			_int(sicx_balance_after)
		)
		
	def _redeem_icx_checks(self):
		sicx_reserve_data_before = self.values["before"]["reserve"]["sicx"]
		sicx_reserve_data_after = self.values["after"]["reserve"]["sicx"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		sicx_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["sicx"]
		sicx_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["sicx"]

		sicx_balance_before = self.values["before"][self.user]['balances']['sicx']
		sicx_balance_after = self.values["after"][self.user]['balances']['sicx']

		oicx_balance_before = self.values["before"][self.user]['balances']['oicx']
		oicx_balance_after = self.values["after"][self.user]['balances']['oicx']

		icx_balance_before = self.values["before"][self.user]['balances']['icx']
		icx_balance_after = self.values["after"][self.user]['balances']['icx']

		amount = self.amount

		self.assertEqual(
				_int(sicx_user_reserve_data_before['principalBorrowBalance']),
				_int(sicx_user_reserve_data_after['principalBorrowBalance'])
			)

		self.assertGreaterEqual(
				_int(sicx_user_reserve_data_before['principalOTokenBalance']),
				_int(sicx_user_reserve_data_after['principalOTokenBalance'])
				)

		expected_rates = self._get_rates(
				_int(sicx_reserve_data_after['totalBorrows']), 
				_int(sicx_reserve_data_before['totalLiquidity']), 
				self.contracts['sicx'])

		self.assertEqual(
				_int(sicx_reserve_data_before['totalBorrows']), 
				_int(sicx_reserve_data_after['totalBorrows'])
				)

		# -> CHECK LATER <-
		# self.assertEqual(
		# 		_int(sicx_reserve_data_after['borrowRate']), 
		# 		expected_rates['borrow_rate']
		# 		)

		# self.assertEqual(
		# 		_int(sicx_reserve_data_after['liquidityRate']), 
		# 		expected_rates['liquidity_rate']
		# 		)

		self.assertGreaterEqual(
				_int(user_account_data_before['availableBorrowsUSD']), 
				_int(user_account_data_after['availableBorrowsUSD'])
				)

		# collateral should decrease
		self.assertGreater(
				_int(user_account_data_before['totalCollateralBalanceUSD']), 
				_int(user_account_data_after['totalCollateralBalanceUSD'])
				)

			# sICX should decrease by redeem amount
		self.assertGreaterEqual(
			  _int(sicx_balance_after),
			  _int(sicx_balance_before) + amount
			  )

			# oICX should increase by redeem amount
		self.assertGreaterEqual(
			  _int(oicx_balance_after) + amount,
			  _int(oicx_balance_before)
			  )

			# icx balance should decrease
		self.assertGreaterEqual(
			  icx_balance_before,
			  icx_balance_after - amount
			  )
		
	def _repay_icx_checks(self):
		sicx_reserve_data_before = self.values["before"]["reserve"]["sicx"]
		sicx_reserve_data_after = self.values["after"]["reserve"]["sicx"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		sicx_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["sicx"]
		sicx_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["sicx"]

		oicx_balance_before = self.values["before"][self.user]['balances']['oicx']
		oicx_balance_after = self.values["after"][self.user]['balances']['oicx']

		icx_balance_before = self.values["before"][self.user]['balances']['icx']
		icx_balance_after = self.values["after"][self.user]['balances']['icx']

		amount = self.amount

		self.assertGreaterEqual(
				_int(sicx_user_reserve_data_before['principalBorrowBalance']), 
				_int(sicx_user_reserve_data_after['principalBorrowBalance']))

		self.assertEqual(
				_int(sicx_user_reserve_data_before['principalOTokenBalance']), 
				_int(sicx_user_reserve_data_after['principalOTokenBalance'])
				)

		expected_rates = self._get_rates(
				_int(sicx_reserve_data_after['totalBorrows']), 
				_int(sicx_reserve_data_after['totalLiquidity']), 
				self.contracts['sicx'])

		self.assertGreaterEqual(
				_int(sicx_reserve_data_after['availableLiquidity']),
				_int(sicx_reserve_data_before['availableLiquidity'])
				)
		self.assertGreaterEqual( 
				_int(sicx_reserve_data_after['totalLiquidity']),
				_int(sicx_reserve_data_before['totalLiquidity']))

		self.assertGreaterEqual(
				_int(sicx_reserve_data_before['totalBorrows']),
				_int(sicx_reserve_data_after['totalBorrows']))

		self.assertEqual(
			_int(sicx_reserve_data_after['borrowRate']), 
			expected_rates['borrow_rate']
			)

		self.assertEqual(
			_int(sicx_reserve_data_after['liquidityRate']), 
			expected_rates['liquidity_rate']
			)

		self.assertGreater(
			_int(user_account_data_before["totalBorrowBalanceUSD"]),
			_int(user_account_data_after["totalBorrowBalanceUSD"])
			)

		self.assertGreater(
			_int(user_account_data_after["availableBorrowsUSD"]),
			_int(user_account_data_before["availableBorrowsUSD"])
			)

		self.assertGreater(
			_int(user_account_data_after['totalCollateralBalanceUSD']), 
			_int(user_account_data_before['totalCollateralBalanceUSD'])
			)

		self.assertAlmostEqual(
		  	_dec(oicx_balance_before),
		 	_dec(oicx_balance_after),
		  	4
		  	)

		# icx balance should decrease
		self.assertGreaterEqual(
			icx_balance_before,
			icx_balance_after - exaMul(amount, _int(self.sicx_rate))
			)
		
	def _deposit_usds_checks(self):

		usds_reserve_data_before = self.values["before"]["reserve"]["usds"]
		usds_reserve_data_after = self.values["after"]["reserve"]["usds"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		usds_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["usds"]
		usds_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["usds"]

		usds_balance_before = self.values["before"][self.user]['balances']['usds']
		usds_balance_after = self.values["after"][self.user]['balances']['usds']

		ousds_balance_before = self.values["before"][self.user]['balances']['ousds']
		ousds_balance_after = self.values["after"][self.user]['balances']['ousds']

		amount = self.amount

		expected_rates = self._get_rates(
				_int(usds_reserve_data_after['totalBorrows']), 
				_int(usds_reserve_data_after['totalLiquidity']), 
				self.contracts['usds'])

		self.assertEqual(
			_int(usds_reserve_data_after["totalLiquidity"]), 
			_int(usds_reserve_data_before["totalLiquidity"]) + amount
			)

		## RATES -> 
		self.assertEqual(
			_int(usds_reserve_data_after["borrowRate"]), 
			expected_rates["borrow_rate"])

		self.assertEqual(
			_int(usds_reserve_data_after["liquidityRate"]), 
			expected_rates['liquidity_rate'])

		## interest accured will increase the value after transaction
		self.assertGreaterEqual(
			_int(usds_user_reserve_data_after['principalOTokenBalance']),
			_int(usds_user_reserve_data_before['principalOTokenBalance']) + amount
		)

		# since someone has already borrowed usdb, on depositing more usdb, the borrow rate should decrease
		self.assertGreaterEqual(
			_int(usds_user_reserve_data_before["borrowRate"]),
			_int(usds_user_reserve_data_after["borrowRate"])
		)

		# no changes in borrow balances
		self.assertAlmostEqual(
			_dec(usds_user_reserve_data_before["currentBorrowBalance"]), 
			_dec(usds_user_reserve_data_after["currentBorrowBalance"]),
			places = 3
		)

		self.assertEqual(
			_int(usds_user_reserve_data_before["principalBorrowBalance"]), 
			_int(usds_user_reserve_data_after["principalBorrowBalance"])
		)

		# asserts
		self.assertGreater(
			_int(user_account_data_after["availableBorrowsUSD"]),
			_int(user_account_data_before["availableBorrowsUSD"])
		)

		self.assertEqual(
			_int(usds_balance_after) + amount,
			_int(usds_balance_before)
			)

		# slightly greater
		self.assertGreaterEqual(
			_int(ousds_balance_after),
			int(amount)
			)
		
	def _borrow_usds_checks(self):
		usds_reserve_data_before = self.values["before"]["reserve"]["usds"]
		usds_reserve_data_after = self.values["after"]["reserve"]["usds"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		usds_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["usds"]
		usds_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["usds"]

		usds_balance_before = self.values["before"][self.user]['balances']['usds']
		usds_balance_after = self.values["after"][self.user]['balances']['usds']

		ousds_balance_before = self.values["before"][self.user]['balances']['ousds']
		ousds_balance_after = self.values["after"][self.user]['balances']['ousds']

		amount = self.amount

		expected_rates = self._get_rates(
				_int(usds_reserve_data_after['totalBorrows']), 
				_int(usds_reserve_data_before['totalLiquidity']), 
				self.contracts['usds'])

		self.assertGreaterEqual(
			_int(ousds_balance_after),
			_int(ousds_balance_before))

		self.assertAlmostEqual(
			_dec(usds_reserve_data_before['availableLiquidity']), 
			_dec(usds_reserve_data_after['availableLiquidity'])+amount/10**18, 
			places = 3
			)

		self.assertAlmostEqual(
			_dec(usds_reserve_data_before['totalLiquidity']), 
			_dec(usds_reserve_data_after['totalLiquidity']), 
			places = 3
			)

		self.assertAlmostEqual(
			_dec(usds_reserve_data_before['totalBorrows']) + amount/10**18, 
			_dec(usds_reserve_data_after['totalBorrows']), 
			places = 3
			)

		# RATE CHECKS
		self.assertEqual(
			_int(usds_reserve_data_after['borrowRate']), 
			expected_rates['borrow_rate']
			)

		self.assertEqual(
			_int(usds_reserve_data_after['liquidityRate']), 
			expected_rates['liquidity_rate']
			)

		self.assertEqual(_int(usds_balance_after), _int(usds_balance_before) + amount)
		
	def _redeem_usds_checks(self):
		usds_reserve_data_before = self.values["before"]["reserve"]["usds"]
		usds_reserve_data_after = self.values["after"]["reserve"]["usds"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		usds_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["usds"]
		usds_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["usds"]

		usds_balance_before = self.values["before"][self.user]['balances']['usds']
		usds_balance_after = self.values["after"][self.user]['balances']['usds']

		ousds_balance_before = self.values["before"][self.user]['balances']['ousds']
		ousds_balance_after = self.values["after"][self.user]['balances']['ousds']

		amount = self.amount

		self.assertEqual(_int(usds_balance_after), _int(usds_balance_before) + amount)
		self.assertGreaterEqual(_int(ousds_balance_after) + amount, _int(ousds_balance_before))

		expected_rates = self._get_rates(
				_int(usds_reserve_data_after['totalBorrows']), 
				_int(usds_reserve_data_after['totalLiquidity']), 
				self.contracts['usds'])

		self.assertEqual(
			_int(usds_user_reserve_data_before['principalBorrowBalance']),
			_int(usds_user_reserve_data_after['principalBorrowBalance'])
			)

		self.assertAlmostEqual(
			_dec(usds_user_reserve_data_before['principalOTokenBalance']),
			_dec(usds_user_reserve_data_after['principalOTokenBalance'])+amount/10**18,
			2
			)

		# RATES
		self.assertEqual(
			_int(usds_reserve_data_after['borrowRate']), 
			expected_rates['borrow_rate'])

		self.assertEqual(
			_int(usds_reserve_data_after['liquidityRate']), 
			expected_rates['liquidity_rate'])

		self.assertGreaterEqual(              
			_int(user_account_data_before['availableBorrowsUSD']), 
			_int(user_account_data_after['availableBorrowsUSD']))

		self.assertGreaterEqual(
			_int(user_account_data_before['healthFactor']),
			_int(user_account_data_after['healthFactor']))

		self.assertGreaterEqual(
			_int(user_account_data_after['currentLiquidationThreshold']),
			_int(user_account_data_before['currentLiquidationThreshold']))
		
	def _repay_usds_checks(self):
		usds_reserve_data_before = self.values["before"]["reserve"]["usds"]
		usds_reserve_data_after = self.values["after"]["reserve"]["usds"]

		user_account_data_before = self.values["before"][self.user]["account_data"]
		user_account_data_after = self.values["after"][self.user]["account_data"]

		usds_user_reserve_data_before = self.values["before"][self.user]["reserve_data"]["usds"]
		usds_user_reserve_data_after = self.values["after"][self.user]["reserve_data"]["usds"]

		usds_balance_before = self.values["before"][self.user]['balances']['usds']
		usds_balance_after = self.values["after"][self.user]['balances']['usds']

		ousds_balance_before = self.values["before"][self.user]['balances']['ousds']
		ousds_balance_after = self.values["after"][self.user]['balances']['ousds']

		amount = self.amount

		# if asked to repay more than borrows
		if user_account_data_after.get("totalBorrowBalanceUSD") == "0x0":
			amt_to_return = amount - _int(user_account_data_before.get("totalBorrowBalanceUSD"))

			self.assertAlmostEqual(
				_dec(usds_balance_after) - _by18(amt_to_return),
				_dec(usds_balance_before) - _by18(amount),
				places = 0
				)

		self.assertGreaterEqual(_int(usds_balance_after), _int(usds_balance_before) - amount)
		self.assertGreaterEqual(_int(ousds_balance_after), _int(ousds_balance_before))

		expected_rates = self._get_rates(
			_int(usds_reserve_data_after['totalBorrows']), 
			_int(usds_reserve_data_after['totalLiquidity']), 
			self.contracts['usds'])

		self.assertEqual(
			_int(usds_user_reserve_data_before['principalOTokenBalance']), 
			_int(usds_user_reserve_data_after['principalOTokenBalance'])
			)

		self.assertGreaterEqual(
			_int(usds_reserve_data_after['totalBorrows'])+amount,
			_int(usds_reserve_data_after['totalBorrows']))

		self.assertEqual(
			_int(usds_reserve_data_after['borrowRate']), 
			expected_rates['borrow_rate'])

		self.assertEqual(
			_int(usds_reserve_data_after['liquidityRate']), 
			expected_rates['liquidity_rate'])

		self.assertGreater(
			_int(user_account_data_before["totalBorrowBalanceUSD"]),
			_int(user_account_data_after["totalBorrowBalanceUSD"])
			)

		self.assertGreater(
			_int(user_account_data_after["availableBorrowsUSD"]),
			_int(user_account_data_before["availableBorrowsUSD"])
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