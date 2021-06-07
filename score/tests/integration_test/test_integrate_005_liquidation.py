from .test_integrate_omm_cases import OMMTestCases
from ..actions.liquidation_cases_others import ACTIONS
from iconsdk.wallet.wallet import KeyWallet
from pprint import pprint
import json

EXA = 10 ** 18
halfEXA = EXA // 2

def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b

def _int(_value):
	return int(_value, 0)

def _dec(_value):
	return int(_value, 0)/10**18

class LiquidationTest(OMMTestCases):
	def setUp(self):
		super().setUp()

	def _transfer(self, from_, params, loan):
		tx_result = self.send_tx(
			from_=from_,
			to=loan,
			method="transfer",
			params=params
			)
		return tx_result

	def _usdb_to_sicx(self, amount):


		icx_usd = _int(self.call_tx(
						to=self.contracts["priceOracle"], 
						method="get_reference_data",
						params={'_base': 'ICX', '_quote':'USD'}
					))

		sicx_rate = _int(self.call_tx(
						to=self.contracts['staking'], 
						method="getTodayRate"
					))

		sicx =  exaDiv(exaDiv(amount, icx_usd), sicx_rate)

		return sicx

	def test_methods(self):
		for action in ACTIONS:
			print(action.get("description"))


			if action.get("user") == "new":
				self.from_ = KeyWallet.create()
				self.send_icx(self._test1, self.from_.get_address(), 1200 * EXA )
				tx = self._transferUSDB(self.deployer_wallet, self.from_.get_address(), 1200 * EXA)
				self.assertEqual(tx['status'], 1)

			for case in action["transaction"]:

				print("\n################",case.get("action"),case.get("reserve"),"###############")

				user_params = {"_user": self.from_.get_address()}

				if case.get('contract') == "priceOracle":

					params =  {
						'_base': 'ICX', 
						'_quote': 'USD', 
						'_rate': case.get("rate")
						}

					tx = self.send_tx(
							from_=self.deployer_wallet,
							to=self.contracts["priceOracle"], 
							method="set_reference_data",
							params=params
							)

					self.assertEqual(tx["status"], case["expectedResult"])

					icx_usd = self.call_tx(
						to=self.contracts[case["contract"]], 
						method="get_reference_data",
						params={'_base': 'ICX', '_quote':'USD'}
					)

					self.assertEqual(_int(icx_usd), case.get("rate"))

				if case.get("reserve") != None:

					if case["reserve"] == "icx":

						if case["action"] == "deposit":

							tx = self._depositICX(self.from_, case.get("amount"))
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

					if case.get("call") == "liquidation":

						if case.get("liquidator") == "deployer":
							self.liquidator = self.deployer_wallet
							lqdtr_params = {'_user': self.liquidator.get_address()}

						if case.get("reserve") == "icx":
							res = "sicx"
						else:
							res = case.get("reserve")

						sicx_address = self.contracts["sicx"]
						usdb_address = self.contracts["usdb"]

						reserve1_params = {'_reserve': sicx_address} # sicx
						reserve2_params = {'_reserve': usdb_address} # usdb

						self.user1_lq_data_before = self.call_tx( 
							to=self.contracts["lendingPoolDataProvider"], 
							method="getUserLiquidationData",
							params=user_params)

						self.user1_account_data_before_lqdn = self.call_tx(
							to=self.contracts["lendingPoolDataProvider"], 
							method="getUserAccountData",
							params=user_params)

						self.reserve1_data_before = self.call_tx(
							to=self.contracts['lendingPoolDataProvider'], 
							method="getReserveData",
							params=reserve1_params) # sicx

						self.reserve2_data_before = self.call_tx(
							to=self.contracts['lendingPoolDataProvider'], 
							method="getReserveData",
							params=reserve2_params) # usdb

						self.lqdtr_account_data_before = self.call_tx(
							to=self.contracts["lendingPoolDataProvider"], 
							method="getUserAccountData",
							params=lqdtr_params)

						self.lqdtr_usdb_balance_before = self.call_tx(
							to=self.contracts["usdb"], 
							method="balanceOf",
							params={'_owner': self.liquidator.get_address()}
						)

						self.lqdtr_sicx_balance_before = self.call_tx(
							to=self.contracts["sicx"], 
							method="balanceOf",
							params={'_owner': self.liquidator.get_address()}
						)			

						if self.user1_account_data_before_lqdn.get("healthFactorBelowThreshold") == "0x0" :
							print("NOT IN LIQUIDATION STATE ")	
							print("ACCOUNT: => ", self.from_.get_address())	

						while (self.user1_account_data_before_lqdn.get("healthFactorBelowThreshold") != "0x0"):
							print("\n IN LIQUIDATION LOOP \n")

							amount_to_liquidate = _int(self.user1_lq_data_before.get("badDebt"))

							# get maximum underlying collateral

							icx_collateral = 0
							usdb_collateral = 0

							# liquidate it
							collaterals = self.user1_lq_data_before.get("collaterals")

							if collaterals is not None:
								if collaterals.get("ICX") is not None:
									icx_collateral = _int(collaterals.get("ICX").get("underlyingBalanceUSD"))
								if collaterals.get("USDb") is not None:
									usdb_collateral = _int(collaterals.get("USDb").get("underlyingBalanceUSD"))

							max_collateral_amt = max(icx_collateral, usdb_collateral)
							collateral = "sicx" if max_collateral_amt == icx_collateral else "usdb"
							coin = "ICX" if max_collateral_amt == icx_collateral else "USDb"

							collateral_token_address = self.contracts[collateral] # usdb
							liquidate_token_address = self.contracts[res] # usdb
							borrower = self.from_.get_address()

							liquidationData = {'method': 'liquidationCall', 'params': {
								'_collateral': collateral_token_address, # sicx
								'_reserve': liquidate_token_address, # usdb
								'_user': borrower, # addr
								'_purchaseAmount': amount_to_liquidate}}

							data = json.dumps(liquidationData).encode('utf-8')

							params = {"_to": self.contracts["lendingPool"],
									  "_value": amount_to_liquidate, "_data": data}
							
							tx = self._transfer(self.liquidator, params, liquidate_token_address)

							if tx.get("status") == 0:
								print(tx["failure"])

							self.assertEqual(tx["status"],  case.get("expectedResult"))

							self.user1_lq_data_after = self.call_tx(
								to=self.contracts["lendingPoolDataProvider"], 
								method="getUserLiquidationData",
								params=user_params)

							self.user1_account_data_after_lqdn = self.call_tx(
								to=self.contracts["lendingPoolDataProvider"], 
								method="getUserAccountData",
								params=user_params)

							self.reserve1_data_after = self.call_tx(
								to=self.contracts['lendingPoolDataProvider'], 
								method="getReserveData",
								params=reserve1_params) # sicx

							self.reserve2_data_after = self.call_tx(
								to=self.contracts['lendingPoolDataProvider'], 
								method="getReserveData",
								params=reserve2_params) # usdb

							self.lqdtr_account_data_after = self.call_tx(
								to=self.contracts["lendingPoolDataProvider"], 
								method="getUserAccountData",
								params=lqdtr_params)

							self.lqdtr_usdb_balance_after = self.call_tx(
								to=self.contracts["usdb"], 
								method="balanceOf",
								params={'_owner': self.liquidator.get_address()}
							)

							self.lqdtr_sicx_balance_after = self.call_tx(
								to=self.contracts["sicx"], 
								method="balanceOf",
								params={'_owner': self.liquidator.get_address()}
							)			

							# borrower's collateral should decrease 1.1 times
							self.assertAlmostEqual(
								_dec(self.user1_lq_data_before["collaterals"][coin]["underlyingBalanceUSD"]),
								_dec(self.user1_lq_data_after["collaterals"][coin]["underlyingBalanceUSD"])
								+ amount_to_liquidate * 1.1 / 10**18,
								places = 0)

							# health factor increases after being liquidated
							self.assertGreater(
								_int(self.user1_account_data_after_lqdn.get("healthFactor")),
								_int(self.user1_account_data_before_lqdn.get("healthFactor"))
								)

							# total borrow balance decreases
							self.assertGreater(
								_int(self.user1_account_data_before_lqdn.get("totalBorrowBalanceUSD")), # before liquidation call
								_int(self.user1_account_data_after_lqdn.get("totalBorrowBalanceUSD")) # after liqudation call)
								)

							# total borrow balance decreases by amount_to_liquidate
							self.assertAlmostEqual(
								_dec(self.user1_account_data_after_lqdn.get("totalBorrowBalanceUSD")) + (amount_to_liquidate)/10**18,
								_dec(self.user1_account_data_before_lqdn.get("totalBorrowBalanceUSD")),
								places = 1
							)

							if res == "sicx":

								print(" PAY SICX LOAN")

								if collateral == "sicx":

									print(" TAKE SICX COLLATERAL ")

									# if liq takes sicx as collateral, 
									self.assertGreaterEqual(
										_int(self.reserve1_data_after["totalLiquidityUSD"]) + amount_to_liquidate * 1.1,
										_int(self.reserve1_data_before["totalLiquidityUSD"])
									)

									self.assertGreaterEqual(
										_int(self.reserve2_data_after["totalLiquidityUSD"]),
										_int(self.reserve2_data_before["totalLiquidityUSD"])
									)

									self.assertAlmostEqual(
										_int(self.lqdtr_usdb_balance_before),
										_int(self.lqdtr_usdb_balance_after),
										places=2)

									self.assertAlmostEqual(
										_dec(self.lqdtr_sicx_balance_after) - self._usdb_to_sicx(amount_to_liquidate) * 0.1 / 10 ** 18, # need to convert usd to sicx
										_dec(self.lqdtr_sicx_balance_before),
										places=1
										)

								elif collateral == 'usdb':

									print(" TAKE USDB COLLATERAL")
									self.assertGreaterEqual(
										_dec(self.reserve2_data_before["totalLiquidityUSD"]),
										_dec(self.reserve2_data_after["totalLiquidityUSD"]) + int(amount_to_liquidate * 1.1) / 10 ** 18
										)

									self.assertGreaterEqual(
										_int(self.reserve1_data_after["totalLiquidityUSD"]),
										_int(self.reserve1_data_before["totalLiquidityUSD"]))

									self.assertAlmostEqual(
										_dec(self.lqdtr_usdb_balance_before),
										_dec(self.lqdtr_usdb_balance_after) - amount_to_liquidate * 1.1/10**18,
										places=1
										)

									self.assertAlmostEqual(
										_dec(self.lqdtr_sicx_balance_after) + self._usdb_to_sicx(amount_to_liquidate)/10**18,
										_dec(self.lqdtr_sicx_balance_before),
										places=1)


								#  sicx total borrow goes down
								self.assertAlmostEqual(
									_dec(self.reserve1_data_after.get("totalBorrowsUSD")) + amount_to_liquidate/10**18,
									_dec(self.reserve1_data_before.get("totalBorrowsUSD")),
									places=1
									)

								# no change in borrow balance for USDB
								self.assertAlmostEqual(
									_dec(self.reserve2_data_before.get("totalBorrowsUSD")),
									_dec(self.reserve2_data_after.get("totalBorrowsUSD")),
									places = 2
									)

								# user collateral should decrease by 1.1
								self.assertAlmostEqual(
									_dec(self.user1_account_data_before_lqdn.get("totalCollateralBalanceUSD")),
									_dec(self.user1_account_data_after_lqdn.get("totalCollateralBalanceUSD")) + ( amount_to_liquidate * 1.1 )/10**18,
									places=0)

							elif res == "usdb":	

								print("PAY USDB LOAN")

								if collateral == "sicx":

									print("TAKE SICX COLLATERAL")

									# if liq takes sicx as collateral, 
									self.assertAlmostEqual(
										_dec(self.reserve1_data_after["totalLiquidityUSD"]) + amount_to_liquidate * 1.1/10**18,
										_dec(self.reserve1_data_before["totalLiquidityUSD"]),
										places=0
									)

									self.assertGreaterEqual(
										_int(self.reserve2_data_after["totalLiquidityUSD"]),
										_int(self.reserve2_data_before["totalLiquidityUSD"]))

									# liquidator balance

									self.assertAlmostEqual(
										_dec(self.lqdtr_usdb_balance_after) + amount_to_liquidate / 10 ** 18,
										_dec(self.lqdtr_usdb_balance_before),
										places = 0
										)

									# TODO
									# CHECK THIS

									self.assertAlmostEqual(
										_dec(self.lqdtr_sicx_balance_after) - self._usdb_to_sicx(amount_to_liquidate) * 1.1/ 10 ** 18, # amount to be converted to sicx
										_dec(self.lqdtr_sicx_balance_before),
										places = 0
										)

								elif collateral == 'usdb':

									print("TAKE USDB COLLATERAL")
									self.assertAlmostEqual(
										_dec(self.reserve2_data_after["totalLiquidityUSD"]) + int(amount_to_liquidate * 1.1) / 10 ** 18,
										_dec(self.reserve2_data_before["totalLiquidityUSD"]),
										places=1
										)

									## lqdtr balance: before lqdn : x USDB
									## lqdtr balance: lqdn call: x - amount USDB
									## lqdtr balance: rewards call: x - amount +  amount * 1.1 USDB
									self.assertAlmostEqual(
										_dec(self.lqdtr_usdb_balance_after) - amount_to_liquidate * 0.1/10**18,
										_dec(self.lqdtr_usdb_balance_before),
										places = 0
										)

									self.assertAlmostEqual(
										_dec(self.lqdtr_sicx_balance_after),
										_dec(self.lqdtr_sicx_balance_before),
										places=1)

									self.assertGreaterEqual(
										_int(self.reserve1_data_after["totalLiquidityUSD"]),
										_int(self.reserve1_data_before["totalLiquidityUSD"]))

								# icx borrows should remain same
								self.assertEqual(
									_dec(self.reserve1_data_before.get("totalBorrowsUSD")),
									_dec(self.reserve1_data_after.get("totalBorrowsUSD")),
									)

								# usdb loan repaid, total borrow should go down
								self.assertAlmostEqual(
									_dec(self.reserve2_data_before.get("totalBorrowsUSD")) - amount_to_liquidate/10**18,
									_dec(self.reserve2_data_after.get("totalBorrowsUSD")),
									places = 2
									)

								# user collateral should decrease by 1.1
								self.assertAlmostEqual(
									_dec(self.user1_account_data_before_lqdn.get("totalCollateralBalanceUSD")),
									_dec(self.user1_account_data_after_lqdn.get("totalCollateralBalanceUSD")) + ( amount_to_liquidate * 1.1 )/10**18,
									places=1)

							# collateral of liquidator should remain similar
							self.assertAlmostEqual(
								_dec(self.lqdtr_account_data_before["totalCollateralBalanceUSD"]),
								_dec(self.lqdtr_account_data_after["totalCollateralBalanceUSD"]),
								places = 2
								)

							## before -> new for new case

							self.user1_account_data_before_lqdn = self.user1_account_data_after_lqdn
							self.user1_lq_data_before = self.user1_lq_data_after
							self.reserve1_data_before = self.reserve1_data_after
							self.reserve2_data_before = self.reserve2_data_after
							self.lqdtr_account_data_before = self.lqdtr_account_data_after
							self.lqdtr_usdb_balance_before = self.lqdtr_usdb_balance_after
							self.lqdtr_sicx_balance_before = self.lqdtr_sicx_balance_after

							print(" LOOP OVER ")
							
							if (self.user1_account_data_before_lqdn.get("healthFactorBelowThreshold") == "0x1"):
								print(" AGAIN IN LIQUIDATION STATE ")
