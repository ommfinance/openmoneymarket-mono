from .test_integrate_omm_cases import OMMTestCases
from ..actions.user_all_txns_multiple_reserve import ACTIONS


class MultipleReserveTest(OMMTestCases):
	def setUp(self):
		super().setUp()

	def test_icx_cases(self):
		print(ACTIONS["description"])
		self._methods(ACTIONS)