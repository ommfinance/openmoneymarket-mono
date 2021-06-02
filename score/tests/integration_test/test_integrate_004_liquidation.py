from .test_integrate_omm_cases import OMMTestCases
from ..actions.liquidation_case1 import ACTIONS
from iconsdk.wallet.wallet import KeyWallet
from pprint import pprint
import json

EXA = 10 ** 18

def _int(_value):
	return int(_value, 0)

def _dec(_value):
	return int(_value, 0)/10**18

class LiquidationTest(OMMTestCases):
	def setUp(self):
		super().setUp()

	def _transfer(self, from_, params, loan):

		if loan == "icx":
			loan = "sicx"

		tx_result = self.send_tx(
			from_=from_,
			to=loan, #USDB contract
			method="transfer",
			params=params
			)
		return tx_result


	def test_liquidation_base(self):
		print(ACTIONS["description"])

		if ACTIONS["user"] == "new":
			self.from_ = KeyWallet.create()
			self.send_icx(self._test1, self.from_.get_address(), 1500 * EXA )
			tx = self._transferUSDB(self.deployer_wallet, self.from_.get_address(), 1200 * EXA)
			self.assertEqual(tx['status'], 1)
			print("40 => ",self.from_.get_address())
		user_params = {'_user': self.from_.get_address()}

		# tx_res = self._depositUSDB(self.deployer_wallet, 10000 * EXA)

		for case in ACTIONS["transaction"]:
			
			print("#################################",case.get("call") ,case["action"], "######################################")

			if case.get("borrower") == "new":
				self._to_liquidate = self.from_.get_address()

			if case.get('contract') != "priceOracle" and case.get("liquidator") == "deployer":
				self.liquidator = self.deployer_wallet
				lq_params = {'_user': self.liquidator.get_address()}

			
			if case.get('contract') == "priceOracle":

				params =  {
					'_base': 'ICX', 
					'_quote': 'USD', 
					'_rate': case["rate"]
					}

				tx = self.send_tx(
						from_=self.deployer_wallet,
						to=self.contracts[case["contract"]], 
						method=case["action"],
						params=params
						)

				self.assertEqual(tx["status"], case["expectedResult"])

				icx_usd = self.call_tx(
					to=self.contracts[case["contract"]], 
					method="get_reference_data",
					params={'_base': 'ICX', '_quote':'USD'}
				)

				self.assertEqual(_int(icx_usd), case["rate"])

			if case.get("reserve") != None:

				if case["reserve"] == "icx":

					if case["action"] == "deposit":

						tx = self._depositICX(self.from_, case["amount"])
						if (tx["status"] == 0):
							print(tx["failure"])
						self.assertEqual(tx["status"], case["expectedResult"])

					if case["action"] == "borrow":

						tx = self._borrowICX(self.from_, case["amount"])
						if (tx["status"] == 0):
							print(tx["failure"])
						self.assertEqual(tx["status"], case["expectedResult"])

				if case["reserve"] == "usdb":

					if case["action"] == "deposit":

						tx = self._depositUSDB(self.from_, case["amount"])
						if (tx["status"] == 0):
							print(tx["failure"])
						self.assertEqual(tx["status"], case["expectedResult"])

					if case["action"] == "borrow":

						tx = self._borrowUSDB(self.from_, case["amount"])
						if (tx["status"] == 0):
							print(tx["failure"])
						self.assertEqual(tx["status"], case["expectedResult"])


						self.user_account_data_before = self.call_tx(
									to=self.contracts["lendingPoolDataProvider"], 
									method="getUserAccountData",
									params=user_params)
						print("USER A/C DATA BEFORE")
						pprint(self.user_account_data_before)

				
				if case.get("call") == "liquidation":

					# data where user is now in liquidation state, but liquidation not called yet
					self.user_account_data_after = self.call_tx(
						to=self.contracts["lendingPoolDataProvider"], 
						method="getUserAccountData",
						params=user_params)

					# print("USER A/C DATA AFTER")
					# pprint(self.user_account_data_after)
					
					self.user_liquidation_data_before_liquidation = self.call_tx(
						to=self.contracts["lendingPoolDataProvider"], 
						method="getUserLiquidationData",
						params=user_params)
					
					# print("USER L/Q DATA BEFORE LIQUIDATION")
					# pprint(self.user_liquidation_data_before_liquidation)

					self.liquidator_account_data_before = self.call_tx(
						to=self.contracts["lendingPoolDataProvider"], 
						method="getUserAccountData",
						params=lq_params)

					# print("LIQUIDATOR USER ACCOUNT BEFORE L/Q")
					# pprint(self.liquidator_account_data_before)

					self.usdb_before  = self.call_tx(
						to=self.contracts["usdb"],
						method="balanceOf",
						params={'_owner': self.liquidator.get_address()})

					if case.get("reserve") == "icx":
						res = "sicx"
					else:
						res = case.get("reserve")

					if case.get("_collateral") == "icx":
						col = "sicx"
					else:
						col = case.get("_collateral")

					reserve1_params = {'_reserve': self.contracts[res]}
					reserve2_params = {'_reserve': self.contracts[col]}

					## lq params
					user2_params = {'_user': self.deployer_wallet.get_address()}

					self.reserve1_data_before = self.call_tx(
						to=self.contracts['lendingPoolDataProvider'], 
						method="getReserveData",
						params=reserve1_params) # usdb

					self.reserve2_data_before = self.call_tx(
						to=self.contracts['lendingPoolDataProvider'], 
						method="getReserveData",
						params=reserve2_params) # sicx

					# self.user2_data_before_lq = self.call_txself.call_tx(
					# 	to=self.contracts["lendingPoolDataProvider"], 
					# 	method="getUserAccountData",
					# 	params=user2_params)

					amount_to_liquidate =  _int(self.user_liquidation_data_before_liquidation.get("badDebt")) #/ rate

					# liquidation call starts here
					if case.get("borrower") == "new":
						borrower = self._to_liquidate
					
					self.sicx_balance_before = self.call_tx(
							to=self.contracts["sicx"], 
							method="balanceOf",
							params={'_owner': self.liquidator.get_address()}
						)

					collateral_token_address = self.contracts[col]
					liquidate_token_address = self.contracts[case.get("reserve")] # address for USDB

					# amount_to_liquidate = int(case.get("_purchaseAmount"))

					liquidationData = {'method': 'liquidationCall', 'params': {
						'_collateral': collateral_token_address, # sicx
						'_reserve': liquidate_token_address, # usdb
						'_user': borrower, # addr
						'_purchaseAmount': amount_to_liquidate}}

					data = json.dumps(liquidationData).encode('utf-8')

					params = {"_to": self.contracts["lendingPool"],
							  "_value": amount_to_liquidate, "_data": data}
					
					tx = self._transfer(self.liquidator, params, liquidate_token_address)
					pprint(tx)

					if tx.get("status") == 0:
						print(tx["failure"])

					self.sicx_amt = _int(tx['eventLogs'][7]['data'][0])

					self.assertEqual(tx["status"], case.get("expectedResult"))

					self.reserve1_data_after = self.call_tx(
						to=self.contracts['lendingPoolDataProvider'], 
						method="getReserveData",
						params=reserve1_params)

					self.reserve2_data_after = self.call_tx(
						to=self.contracts['lendingPoolDataProvider'], 
						method="getReserveData",
						params=reserve2_params)

					# self.user2_data__lq = self.call_txself.call_tx(
					# 	to=self.contracts["lendingPoolDataProvider"], 
					# 	method="getUserAccountData",
					# 	params=user2_params)

					# liquidation caller
					self.usdb_after  = self.call_tx(
						to=self.contracts["usdb"],
						method="balanceOf",
						params={'_owner': self.deployer_wallet.get_address()})

		self.user_account_data_after_liquidation = self.call_tx(
						to=self.contracts["lendingPoolDataProvider"], 
						method="getUserAccountData",
						params=user_params)


		self.user_liquidation_data_after_liquidation = self.call_tx(
						to=self.contracts["lendingPoolDataProvider"], 
						method="getUserLiquidationData",
						params=user_params)

		self.liquidator_account_data_after = self.call_tx(
						to=self.contracts["lendingPoolDataProvider"], 
						method="getUserAccountData",
						params=lq_params)

		self.sicx_balance_after = self.call_tx(
				to=self.contracts["sicx"], 
				method="balanceOf",
				params={"_owner": self.liquidator.get_address()}
			)
					
		# print("\n\n")
		# print(self.sicx_balance_before)
		# print("\n\n")
		# print(self.sicx_balance_after)
		# print("\n\n")

		# print("USER L/Q DATA BEFORE LIQUIDATION")
		# pprint(self.user_liquidation_data_before_liquidation)

		# print("USER A/C DATA AFTER LIQUIDATION")
		# pprint(self.user_account_data_after_liquidation)

		# print("USER L/Q DATA AFTER LIQUIDATION")
		# pprint(self.user_liquidation_data_after_liquidation)

		# print("LIQUIDATOR USER ACCOUNT BEFORE L/Q")
		# pprint(self.liquidator_account_data_before)

		# print("LIQUIDATOR USER ACCOUNT AFTER L/Q")
		# pprint(self.liquidator_account_data_after)

		# print("USDB RESERVE DATA BEFORE")
		# pprint(self.reserve1_data_before)

		# print("USDB RESERVE DATA AFTER")
		# pprint(self.reserve1_data_after)

		# print("sICX RESERVE DATA BEFORE")
		# pprint(self.reserve2_data_before)

		# print("sICX RESERVE DATA AFTER")
		# pprint(self.reserve2_data_after)

		# checks for before liquidation call

		self.assertEqual(self.user_account_data_after['healthFactorBelowThreshold'], '0x1')

		# self.assertGreater(
		# 	_int(self.user_account_data_before['healthFactor']),
		# 	_int(self.user_account_data_after['healthFactor']))

		self.assertGreater(
			self.user_account_data_before['totalCollateralBalanceUSD'],
			self.user_account_data_after['totalCollateralBalanceUSD'])

		self.assertEqual(
			self.user_account_data_before['currentLiquidationThreshold'],
			self.user_account_data_after['currentLiquidationThreshold'])

		#####################################
		# checks for after liquidation call #
		#####################################

		self.assertEqual(_int(self.usdb_before), _int(self.usdb_after) + amount_to_liquidate)

		# user 1's collateral should decrease 1.1 times liquidation amount
		self.assertAlmostEqual(
			_dec(self.user_liquidation_data_before_liquidation["collaterals"]['ICX']["underlyingBalanceUSD"]),
			_dec(self.user_liquidation_data_after_liquidation["collaterals"]['ICX']["underlyingBalanceUSD"]) 
			+ amount_to_liquidate * 1.1 / 10 ** 18,
			places = 1
			)

		self.assertGreater(
			_int(self.user_account_data_after_liquidation.get("healthFactor")),
			_int(self.user_account_data_after.get("healthFactor"))
			)
		
		self.assertGreater(
			_int(self.user_account_data_after.get("totalBorrowBalanceUSD")), # before liquidation call
			_int(self.user_account_data_after_liquidation.get("totalBorrowBalanceUSD")) # after liqudation call
			)

		# before borrow balance = after + repaid amount
		self.assertAlmostEqual(
			_dec(self.user_account_data_after_liquidation.get("totalBorrowBalanceUSD")) + (amount_to_liquidate)/10**18,
			_dec(self.user_account_data_after.get("totalBorrowBalanceUSD")) ,
			places = 4
			)


		# reserve parameters
		self.assertAlmostEqual(
			_dec(self.reserve1_data_before["totalBorrowsUSD"]),
			_dec(self.reserve1_data_after["totalBorrowsUSD"])+amount_to_liquidate/10**18,
			places=3)

		# liquidator supplies more liquidity
		# supplies amount, not amount * 1.1
		self.assertAlmostEqual(
			_dec(self.reserve1_data_before["availableLiquidityUSD"])+int(amount_to_liquidate)/10**18, # 1.1
			_dec(self.reserve1_data_after["availableLiquidityUSD"]),
			places=3)

		# icx borrows should remain same
		self.assertEqual(
			_dec(self.reserve2_data_before.get("totalBorrowsUSD")),
			_dec(self.reserve2_data_after.get("totalBorrowsUSD")),
			)

		# total liquidity should decrease on liquidation
		self.assertAlmostEqual(
			_dec(self.reserve2_data_after["totalLiquidityUSD"]) + int(amount_to_liquidate * 1.1) / 10 ** 18,
			_dec(self.reserve2_data_before["totalLiquidityUSD"]),
			places=0
			)

		# collateral of user 2 should remain similar
		self.assertAlmostEqual(
			_dec(self.liquidator_account_data_before["totalCollateralBalanceUSD"]),
			_dec(self.liquidator_account_data_after["totalCollateralBalanceUSD"]),
			places = 2
			)

		# liquidator should get sicx
		self.assertEqual(
			_int(self.sicx_balance_before),
			_int(self.sicx_balance_after) - self.sicx_amt
			)
