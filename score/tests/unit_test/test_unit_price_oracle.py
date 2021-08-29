from iconservice import Address
from iconservice.base.exception import InvalidParamsException
from tbears.libs.scoretest.patch.score_patcher import get_interface_score, ScorePatcher
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from priceOracle.priceOracle import PriceOracle

EXA = 10 ** 18


class TestPriceOracle(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self._owner = self.test_account1
        self.mock_address_provider = Address.from_string(f"cx{'1239' * 10}")
        self.score = self.get_score_instance(PriceOracle, self._owner, on_install_params={
            "_addressProvider": self.mock_address_provider
        })

        self.mock_band_oracle = Address.from_string(f"cx{'1232' * 10}")
        self.mock_dex = Address.from_string(f"cx{'1235' * 10}")

        self.set_msg(self.mock_address_provider)

        self.score.setAddresses([
            {"name": "bandOracle", "address": self.mock_band_oracle},
            {"name": "dex", "address": self.mock_dex}
        ])

    def test_get_reference_data_for_omm(self):
        """
        OMM5/USDS=1.5 # from dex
        _total(OMM5/USDS)=13
        OMM5/IUSDC=1.7 # from dex
        _total(OMM5/IUSDC)=11
        OMM5/sICX=1.9  # from dex
        _total(OMM5/sICX)=23
        sICX/ICX= 1.2 # from dex
        OMM5/ICX=2.28  ## (1.9* 1.2)
        USDS price is short circuit to 1 USD
        OMM5/USDS=1.5 # in USD
        USDC price =1 #in USD from bandOracle
        OMM5/IUSDC=1.7 # in USD
        ICX price = 0.9 #in USD from bandOracle
        OMM5/ICX=2.052 # in USD (0.9*2.28)
        OMM price=(1.5*13+1.7*11+2.052*23)/(13+11+23)
        OMM5=1.816936170212766 # in USD average of OMM5/USDS,OMM5/IUSDC and OMM5/ICX
        :return:
        """
        self.set_msg(self._owner)

        # self.score.set_reference_data("USDS", "USD", 1 * EXA)
        # self.score.set_reference_data("USDC", "USD", 1 * EXA)
        # self.score.set_reference_data("ICX", "USD", 9 * EXA // 10)
        self.set_msg(None)

        self.register_interface_score(self.mock_dex)
        self._mock_lookupPid()
        self._mock_poolStats()
        self.patch_internal_method(self.mock_band_oracle, "get_reference_data",
                                   lambda _base, _quote: {"rate": 9 * EXA // 10})

        def _price_side_effect(_name):
            if _name == 'sICX/ICX':
                return 12 * EXA // 10
            else:
                raise InvalidParamsException(f"Invalid parameter {_name}")

        ScorePatcher.patch_internal_method(self.mock_dex, "getPriceByName", _price_side_effect)

        actual_result = self.score.get_reference_data("OMM", "USD")

        _mock_dex_score = get_interface_score(self.mock_dex)

        self.assertEqual(1, _mock_dex_score.getPriceByName.call_count)
        self.assertEqual(3, _mock_dex_score.lookupPid.call_count)
        self.assertEqual(3, _mock_dex_score.getPoolStats.call_count)
        #USDS 1.5*1
        #IUSDC 1.7*0.9
        #ICX 2.9*1.2*0.9
        self.assertAlmostEqual((1.5 * 13 + 1.53 * 11 + 2.052 * 23) / (13 + 11 + 23), actual_result / EXA, 10)

    def _mock_lookupPid(self):
        def _lookupPid_side_effect(_name):
            if _name == 'OMM/USDS':
                return 0x1
            elif _name == 'OMM/IUSDC':
                return 0x2
            elif _name == 'OMM/sICX':
                return 0x3
            else:
                raise InvalidParamsException(f"Invalid parameter {_name}")

        ScorePatcher.patch_internal_method(self.mock_dex, "lookupPid", _lookupPid_side_effect)

    def _mock_poolStats(self):
        def _poolStats_side_effect(_id):
            if _id == 1:
                return {
                    "base": 13 * EXA,
                    "price": 15 * EXA // 10,
                    "base_decimals": 0x12,
                    "quote_decimals": 0x12
                }
            elif _id == 2:
                return {
                    "base": 11 * EXA,
                    "price": 17 * 10 ** 6 // 10,
                    "base_decimals": 0x12,
                    "quote_decimals": 0x6,
                }
            elif _id == 3:
                return {
                    "base": 23 * EXA,
                    "price": 19 * EXA // 10,
                    "base_decimals": 0x12,
                    "quote_decimals": 0x12,
                }
            else:
                raise InvalidParamsException(f"Invalid parameter {_id}")

        ScorePatcher.patch_internal_method(self.mock_dex, "getPoolStats", _poolStats_side_effect)
