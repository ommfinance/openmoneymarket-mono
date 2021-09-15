from iconservice import *

from ..snapshot.snapshot import Snapshot


class OMMSnapshot(Snapshot):

    @abstractmethod
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__('omm-token', db)
