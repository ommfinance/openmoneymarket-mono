from iconservice import Address
from iconservice.base.exception import InvalidParamsException
from tbears.libs.scoretest.patch.score_patcher import get_interface_score
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from priceOracle.priceOracle import PriceOracle

EXA = 10 ** 18


class TestPriceOracle(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self._owner = self.test_account1
        self.score = self.get_score_instance(PriceOracle, self._owner)

        self.mock_lp_address = Address.from_string(f"cx{'1231' * 10}")
        self.mock_band_oracle = Address.from_string(f"cx{'1232' * 10}")
        self.mock_address_provider = Address.from_string(f"cx{'1234' * 10}")

        self.set_msg(self._owner)
        self.score.setDataSource(self.mock_lp_address)
        self.score.setBandOracle(self.mock_band_oracle)
        self.score.setAddressProvider(self.mock_address_provider)

    def test_get_reference_data_for_omm(self):
        self.set_msg(self._owner)
        self.score.setOraclePriceBool(False)

        self.score.set_reference_data("USDB", "USD", 15 * EXA // 10)
        self.score.set_reference_data("USDS", "USD", 15 * EXA // 10)
        self.score.set_reference_data("USDC", "USD", 12 * EXA // 10)
        self.score.set_reference_data("ICX", "USD", 5 * EXA // 10)
        self.set_msg(None)


        _reserve_address = {
            "USDS": Address.from_string(f"cx{'9841' * 10}"),
            "sICX": Address.from_string(f"cx{'9842' * 10}"),
            "IUSDC": Address.from_string(f"cx{'9843' * 10}")
        }

        self.patch_internal_method(self.mock_address_provider, "getReserveAddresses", lambda: _reserve_address)
        self.patch_internal_method(_reserve_address["USDS"], "decimals", lambda: 18)
        self.patch_internal_method(_reserve_address["sICX"], "decimals", lambda: 18)
        self.patch_internal_method(_reserve_address["IUSDC"], "decimals", lambda: 6)

        def _price_side_effect(_name):
            if _name == 'OMM/USDS':
                return 14 * EXA // 10
            elif _name == 'OMM/IUSDC':
                return 15 * 10 ** 6 / 10
            elif _name == 'OMM/sICX':
                return 75 * EXA // 100
            elif _name == 'sICX/ICX':
                return 85 * EXA // 100
            else:
                raise InvalidParamsException(f"Invalid parameter {_name}")

        self.patch_internal_method(self.mock_lp_address, "getPriceByName", _price_side_effect)

        actual_result = self.score.get_reference_data("OMM", "USD")

        _mock_dex_score = get_interface_score(self.mock_lp_address)

        self.assertEqual(4, _mock_dex_score.getPriceByName.call_count)

        self.assertEqual(140625 * EXA // 100000, actual_result)

