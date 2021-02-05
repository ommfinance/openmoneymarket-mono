from iconservice import *
from .Math import *


TAG = 'Delegation'

class PrepDelegationDetails(TypedDict):
    prepAddress: Address
    prepPercentage : int

class OmmTokenInterface(InterfaceScore):
    @interface
    def details_balanceOf(self, _owner: Address) -> dict:
        pass



class Delegation(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._preps = ArrayDB('preps',db,Address)
        self._userPreps = DictDB('userPreps',db,value_type=Address,depth=2)
        self._percentageDelegations = DictDB('precentageDelegations',db,value_type=int,depth=2)
        self._prepVotes = DictDB('userPrepVotes',db,int)
        self._userVotes = DictDB('userVotes',db,int)
        self._totalVotes = VarDB('totalVotes',db,int)
        self._voted = DictDB('userVoted',db,bool)
        self._equalDistribution = VarDB('equla',db,bool)
        self._ommTokenAddress = VarDB('ommAddress',db,Address)
    

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    def _require(self,_condtion:bool,_message:str):
        if not  _condtion:
            revert(_message)
    
    def userPrefix(self,_user: Address,_prep:Address)->bytes:
        prefix = b'|'.join([USER_PREFIX, str(_user).encode(),str(_prep).encode()])
        return prefix

    @external
    def setOmmToken(self,_address:Address):
        self._require(self.msg.sender == self.owner,"Cant set address:You are not authorized")
        self._ommTokenAddress.set(_address)

    @external(readonly = True)
    def getOmmToken(self)->Address:
        return self._ommTokenAddress.get()

    def clearPrevious(self):
        user = self.tx.origin
        for index in range (5):
            #removing votes 
            
            prepVote = exaMul(self._percentageDelegations[user][index],self._userVotes[user])
            # print(user,self._userPreps[user][index],prepVote)
            if prepVote > 0:
                self._prepVotes[self._userPreps[user][index]] -= prepVote
            
            #resetting the preferences 
            self._userPreps[user][index] = ZERO_SCORE_ADDRESS
            self._percentageDelegations[user][index] = 0

            #adjusting total votes 
            self._totalVotes.set(self._totalVotes.get()- prepVote)
            # self._totalVotes -=prepVote
        self._userVotes[user] = 0

    @external(readonly = True)
    def getPrepList(self)->list:
        prepList = []
        for prep in self._preps:
            prepList.append(prep)
        return prepList

    @external
    def updateDelegations(self,_delegations:List[PrepDelegationDetails] = None)->dict:
        delegations =[]
        user = self.tx.origin  
        totalPercentage = 0
        if _delegations is None:
            userDelegationDetails = self.getUserDelegationDetails(user)
            for key,value in userDelegationDetails.items():
                delegationDetails = {"prepAddress":key,"prepPercentage":value}
                delegations.append(delegationDetails)
        else:
            self._require(len(_delegations)<=5,"Add error:Cant take more than 5 preps ")
        
        if len(delegations) == 0:
            delegations = _delegations
        ommToken = self.create_interface_score(self._ommTokenAddress.get(),OmmTokenInterface)
        userStakedToken = ommToken.details_balanceOf(user)['stakedBalance']

        #resetting previous delegation prefereneces
        self.clearPrevious()
        index = 0 
        for delegation in delegations:
            
            #adding delegation to new preps
            prepVote = exaMul(delegation['prepPercentage'],userStakedToken)
            self._prepVotes[delegation['prepAddress']] += prepVote
            
            #updating prep list 
            if delegation['prepAddress'] not in self._preps:
                self._preps.put(delegation['prepAddress'])

            #updating the delegation preferences
            self._userPreps[user][index]= delegation['prepAddress']
            self._percentageDelegations[user][index] = delegation['prepPercentage']

            #adjusting total votes 
            self._totalVotes.set(self._totalVotes.get() + prepVote)
            # self._totalVotes += prepVote
            totalPercentage+= delegation['prepPercentage']
            index += 1
        self._require(totalPercentage == EXA,"update error:percentage error ")
        self._userVotes[user] = userStakedToken
        return self.computeDelegationPercentages()

    @external(readonly = True)
    def prepVotes(self,_prep:Address):
        return self._prepVotes[_prep]
            
    @external(readonly = True)
    def getUserDelegationDetails(self,_user:Address)-> dict :
        userDetails = {}
        for index in range(5):
            if self._userPreps[_user][index] != ZERO_SCORE_ADDRESS:
                userDetails[self._userPreps[_user][index]] = self._percentageDelegations[_user][index]
        return userDetails
            
    @external(readonly = True)
    def computeDelegationPercentages(self) -> dict:
        votesPercentage = {}
        prepList = self.getPrepList()
        for index,prep in enumerate(prepList):
            if index ==  len(prepList)-1:
                votesPercentage[prep] = 100 * EXA - sum(votesPercentage.values())
            else:
                votesPercentage[prep]=exaDiv(self._prepVotes[prep],self._totalVotes.get())* 100

        return votesPercentage

        
        
        

        
        
        
