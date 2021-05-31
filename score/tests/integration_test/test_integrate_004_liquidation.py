from pprint import pprint

from iconsdk.wallet.wallet import KeyWallet

from .test_integrate_omm_cases import OMMTestCases
from ..actions.liquidation_cases import ACTIONS

EXA = 10 ** 18

def _int(_value):
	return int(_value, 0)

class LiquidationTest(OMMTestCases):
	def setUp(self):
		super().setUp()

	def test_liquidation_base(self):
		print(ACTIONS["description"])

		if ACTIONS["user"] == "new":
			self.from_ = KeyWallet.create()
			self.send_icx(self._test1, self.from_.get_address(), 1200 * EXA )
			tx = self._transferUSDB(self.deployer_wallet, self.from_.get_address(), 1200 * EXA)
			self.assertEqual(tx['status'], 1)
		user_params = {'_user': self.from_.get_address()}

		for case in ACTIONS["transaction"]:

			print("######################################################################################")
			print("#################################", case["action"], "######################################")
			print("######################################################################################")

			if case["user"] == "1":
				self.from_ = self._test1

			user_params = {'_user': self.from_.get_address()}
			
			if case.get('contract') != None:

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

		self.user_account_data_after = self.call_tx(
			to=self.contracts["lendingPoolDataProvider"], 
			method="getUserAccountData",
			params=user_params)

		pprint(self.user_account_data_before)
		pprint(self.user_account_data_after)

		self.assertEqual(self.user_account_data_after['healthFactorBelowThreshold'], '0x1')

		self.assertGreater(
			self.user_account_data_before['totalCollateralBalanceUSD'],
			self.user_account_data_after['totalCollateralBalanceUSD'])

		self.assertEqual(
			self.user_account_data_before['currentLiquidationThreshold'],
			self.user_account_data_after['currentLiquidationThreshold'])

