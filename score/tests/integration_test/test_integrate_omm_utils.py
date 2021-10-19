from pprint import pprint
from iconsdk.wallet.wallet import KeyWallet
from .test_integrate_base import *


class OmmUtils(OMMTestBase):
    def setUp(self):
        super().setUp()

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
        params = {"_reserve": self.contracts['sicx'], "_amount": _borrowAmount}

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["lendingPool"],
            method="borrow",
            params=params
        )
        return tx_result

    def _redeemICX(self, _from, _redeemAmount):
        params = {
            "_oToken": self.contracts["oICX"],
            "_amount": _redeemAmount,
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["lendingPool"],
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
            to=self.contracts["sicx"],
            method="transfer",
            params=params
        )
        return tx_result

    def _borrowUSDS(self, _from, _borrowAmount):
        params = {
            "_reserve": self.contracts['usds'],
            "_amount": _borrowAmount,
        }
        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["lendingPool"],
            method="borrow",
            params=params
        )
        return tx_result

    def _depositUSDS(self, _from, _depositAmount):
        depositData = {'method': 'deposit',
            'params': {'amount': _depositAmount}}

        data = json.dumps(depositData).encode('utf-8')
        params = {"_to": self.contracts['lendingPool'],
                  "_value": _depositAmount,
                  "_data": data}
        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["usds"],  # USDB contract
            method="transfer",
            params=params
        )
        return tx_result

    def _mintUSDS(self, _from, _to):
        params = {
            "_to": _to,
            "_value": 1000 * 10 ** 18
        }
        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["usds"],
            method="mintTo",
            params=params
        )
        return tx_result

    def _redeemUSDS(self, _from, _redeemAmount):
        params = {
            "_oToken": self.contracts["oUSDS"],
            "_amount": _redeemAmount,
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["lendingPool"],
            method="redeem",
            params=params
        )
        return tx_result

    def _repayUSDS(self, _from, _repayAmount):
        repay_data = {'method': 'repay', 'params': {'amount': _repayAmount}}
        data = json.dumps(repay_data).encode('utf-8')

        params = {"_to": self.contracts['lendingPool'],
                  "_value": _repayAmount,
                  "_data": data}

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["usds"],  # USDB contract
            method="transfer",
            params=params
        )
        return tx_result

    def _transferUSDS(self, _from, _to, _transferAmount):
        params = {
            "_to": _to,
            "_value": _transferAmount
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["usds"],  # USDS contract
            method="transfer",
            params=params
        )
        return tx_result

    def _transferOMM(self, _from, _to, _transferAmount):
        params = {
            "_to": _to,
            "_value": _transferAmount
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["ommToken"],
            method="transfer",
            params=params
        )
        return tx_result

    def _transferLPTokens(self, _from, _to, _id):
        params = {
            "_to": _to,
            "_id": _id,
            "_value": 10 * 10 ** 18
        }

        tx_result = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts["dex"],
            method="transfer",
            params=params
        )
        return tx_result

    def _stakeLp(self, _from, _amount, _id):
        data = {
            'method': "stake"
        }

        data = json.dumps(data).encode('utf-8')

        params = {
            '_to': self.contracts['stakedLp'],
            '_value': _amount,
            '_id': _id,
            '_data': data
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts['dex'],
            method="transfer",
            params=params
        )
        print(tx_result)

        return tx_result

    def _unstakeLp(self, _from, _amount, _id):
        params = {
            '_id': _id,
            '_value': _amount
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts['stakedLp'],
            method="unstake",
            params=params
        )

        return tx_result

    def _stakeOMM(self, _from, _value):
        params = {
            '_value': _value
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["lendingPool"],
            method="stake",
            params=params
        )

        return tx_result

    def _unstakeOMM(self, _from, _value):
        params = {
            '_value': _value
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["lendingPool"],
            method="unstake",
            params=params
        )
        return tx_result

    def _transferOMM(self, _from, _to, _value):
        params = {
            '_to': _to,
            '_value': _value
        }

        tx_result = self.send_tx(
            from_=_from,
            to=self.contracts["ommToken"],
            method="transfer",
            params=params
        )

        return tx_result

    def _transferOUSDS(self, _from, _to, _value):
        params = {
            '_to': _to,
            '_value': _value
        }

        tx_result = self.send_tx(
                from_=_from,
                to=self.contracts["oUSDS"],
                method="transfer",
                params=params
            )

        return tx_result

    def _transferDICX(self, _from, _to, _value):
        params = {
            '_to': _to,
            '_value': _value
        }

        tx_result = self.send_tx(
                from_=_from,
                to=self.contracts["dICX"],
                method="transfer",
                params=params
            )

        return tx_result
