from ..rewardDistribution import RewardDistributionManager
from tbears.libs.scoretest.score_test_case import ScoreTestCase


class TestRewardDistributionManager(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self.score = self.get_score_instance(RewardDistributionManager, self.test_account1)

    def test_hello(self):
        self.assertEqual(self.score.hello(), "Hello")
