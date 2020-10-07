from iconservice import *

TAG = 'DaoFund'


# This contract manages the fund for Dao operations

class DaoFund(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
