from iconservice import *
from .Math import *
from .utils.checks import * 
TAG = 'Delegation'


class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


class OmmTokenInterface(InterfaceScore):
    @interface
    def details_balanceOf(self, _owner: Address) -> dict:
        pass


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def updatePrepDelegations(self, _delegations:  List[PrepDelegations]):
        pass


class Delegation(IconScoreBase):
    _PREPS ='preps'
    _USER_PREPS = 'userPreps'
    _PERCENTAGE_DELEGATIONS = 'percentageDelegations'
    _PREP_VOTES = 'prepVotes'
    _USER_VOTES = 'userVotes'
    _TOTAL_VOTES = 'totalVotes'
    _VOTED = 'voted'
    _EQUAL_DISTRIBUTION = 'equalDistribution'
    _OMM_TOKEN = 'ommToken'
    _LENDING_POOL_CORE = 'lendingPoolCore'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._preps = ArrayDB(self._PREPS, db, Address)
        self._userPreps = DictDB(self._USER_PREPS, db, value_type=Address, depth=2)
        self._percentageDelegations = DictDB(self._PERCENTAGE_DELEGATIONS, db, value_type=int, depth=2)
        self._prepVotes = DictDB(self._PREP_VOTES, db, value_type=int)
        self._userVotes = DictDB(self._USER_VOTES, db, value_type=int)
        self._totalVotes = VarDB(self._TOTAL_VOTES, db, value_type=int)
        self._voted = DictDB(self._VOTED, db, value_type=bool)
        self._equalDistribution = VarDB(self._EQUAL_DISTRIBUTION, db, value_type=bool)
        self._ommToken = VarDB(self._OMM_TOKEN, db, value_type=Address)
        self._lendingPoolCore = VarDB(self._LENDING_POOL_CORE, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    def _require(self, _condtion: bool, _message: str):
        if not _condtion:
            revert(_message)

    @external(readonly=True)
    def name(self)->str:
        return "OmmDelegation"

    @only_owner
    @external
    def setOmmToken(self, _address: Address):
        self._ommToken.set(_address)

    @external(readonly=True)
    def getOmmToken(self) -> Address:
        return self._ommToken.get()

    @only_owner
    @external
    def setLendingPoolCore(self, _address: Address):
        self._lendingPoolCore.set(_address)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._lendingPoolCore.get()

    def clearPrevious(self):
        user = self.tx.origin
        for index in range(5):

            # removing votes
            prepVote = exaMul(self._percentageDelegations[user][index], self._userVotes[user])
            # print(user,self._userPreps[user][index],prepVote)
            if prepVote > 0:
                self._prepVotes[self._userPreps[user][index]] -= prepVote

            # resetting the preferences
            self._userPreps[user][index] = ZERO_SCORE_ADDRESS
            self._percentageDelegations[user][index] = 0

            # adjusting total votes
            self._totalVotes.set(self._totalVotes.get() - prepVote)
            # self._totalVotes -=prepVote
        self._userVotes[user] = 0

    @external(readonly=True)
    def getPrepList(self) -> list:
        prepList = []
        for prep in self._preps:
            prepList.append(prep)
        return prepList

    @external
    def updateDelegations(self, _delegations: List[PrepDelegations] = None):
        delegations = []
        user = self.tx.origin
        totalPercentage = 0
        if _delegations is None:
            userDelegationDetails = self.getUserDelegationDetails(user)
            for key, value in userDelegationDetails.items():
                delegationDetails = {"prepAddress": key, "prepPercentage": value}
                delegations.append(delegationDetails)
        else:
            self._require(len(_delegations) <= 5, "Delegation SCORE : Add error-Cant take more than 5 preps for a user ")

        if len(delegations) == 0:
            delegations = _delegations
        ommToken = self.create_interface_score(self._ommToken.get(), OmmTokenInterface)
        userStakedToken = ommToken.details_balanceOf(user)['stakedBalance']

        # resetting previous delegation prefereneces
        self.clearPrevious()
        index = 0
        for delegation in delegations:

            # adding delegation to new preps
            prepVote = exaMul(delegation['_votes_in_per'], userStakedToken)
            self._prepVotes[delegation['_address']] += prepVote

            # updating prep list
            if delegation['_address'] not in self._preps:
                self._preps.put(delegation['_address'])

            # updating the delegation preferences
            self._userPreps[user][index] = delegation['_address']
            self._percentageDelegations[user][index] = delegation['_votes_in_per']

            # adjusting total votes
            self._totalVotes.set(self._totalVotes.get() + prepVote)
            # self._totalVotes += prepVote
            totalPercentage += delegation['_votes_in_per']
            index += 1
        self._require(totalPercentage == EXA, "Delegation SCORE :Update error- sum of percentages not equal to 100 ")
        self._userVotes[user] = userStakedToken

        # get updated prep percentages and updating the preference
        updatedDelegation = self.computeDelegationPercentages()
        core = self.create_interface_score(self._lendingPoolCore.get(), LendingPoolCoreInterface)
        core.updatePrepDelegations(updatedDelegation)

    @external(readonly=True)
    def prepVotes(self, _prep: Address):
        return self._prepVotes[_prep]

    @external(readonly=True)
    def getUserDelegationDetails(self, _user: Address) -> dict:
        userDetails = {}
        for index in range(5):
            if self._userPreps[_user][index] != ZERO_SCORE_ADDRESS:
                userDetails[self._userPreps[_user][index]] = self._percentageDelegations[_user][index]
        return userDetails

    @external(readonly=True)
    def computeDelegationPercentages(self) -> List[PrepDelegations]:
        prepDelegations = []
        prepList = self.getPrepList()
        totalPercentage = 0
        for index, prep in enumerate(prepList):
            votesPercentage = {'_address':prep,'_votes_in_per':0}
            if index == len(prepList) - 1:
                votesPercentage['_votes_in_per'] = 100 * EXA - totalPercentage
            else:
                votesPercentage['_votes_in_per'] = exaDiv(self._prepVotes[prep], self._totalVotes.get()) * 100
                totalPercentage+=votesPercentage['_votes_in_per']
            prepDelegations.append(votesPercentage)
        return prepDelegations
