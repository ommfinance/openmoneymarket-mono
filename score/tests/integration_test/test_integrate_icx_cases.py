from .test_integrate_omm_cases import OMMTestCases
from ..actions.user_all_txn_icx_reserve import ACTIONS


class ICXTest(OMMTestCases):

	def setUp(self):
		super().setUp()

	def test_icx_cases(self):
		print(ACTIONS["description"])
		self._methods(ACTIONS)