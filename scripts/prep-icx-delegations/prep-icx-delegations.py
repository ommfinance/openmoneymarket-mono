import requests
import json
import argparse
import time
import concurrent.futures
from pprint import pprint
from retry import retry

# mainnet
BOOSTED_OMM = "cxeaff5a10cb72bf85965b8b4af3e708ab772b7921"
DELEGATION = "cx841f29ec6ce98b527d49a275e87d427627f1afe5"
ENDPOINT = "https://ctz.solidwallet.io/api/v3"

def argumentParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-prep", "--prep", help="PREP", type=str, default="-prep")
    args = parser.parse_args()
    return args

class FetchData(object):
    def __init__(self, prep: str):
        super(FetchData, self).__init__()
        self.prep_address = prep
        self.stakers_list = []
        self.info = {}
    
    @retry(Exception, tries=5, delay=1)
    def get_request(self, payload: str):
        r = requests.post(ENDPOINT, data=payload)
        return json.loads(r.text)['result']
    
    def make_rpc_dict(self, _to_contract: str, method: str, params) -> str:
        rpc_dict = {
                'jsonrpc': '2.0',
                'method': 'icx_call',
                'id': 1234,
                'params': {
                    "from": "hx0000000000000000000000000000000000000000",
                    "to": f"{_to_contract}",  
                    "dataType": "call",
                    "data": {
                        "method": f"{method}",
                        "params": params
                    }
            }
        }
        return json.dumps(rpc_dict)

    
    def populate_stakers_list(self, skip: int = 0):
        params: dict = {
            "start": f'{skip}',
            "end": f'{skip+100}',
        }
        payload: str = self.make_rpc_dict(BOOSTED_OMM, "getUsers", params)
        wallets: list = self.get_request(payload)
        self.stakers_list.extend(wallets)
        if len(wallets) == 100:
            self.populate_stakers_list(skip+100)

    def calculate_delegation_info(self, _user: str):
        params: dict = {"_user": _user}
        payload: str = self.make_rpc_dict(DELEGATION, "getUserICXDelegation", params)
        info: list = self.get_request(payload)
        for i in info:
            if i.get("_address") == self.prep_address:
                self.info[_user] = int(i.get("_votes_in_icx"), 16) ## / 10 ** 18 ICX
    
    def get_stakers_list(self) -> list:
        return self.stakers_list
    
    def get_delegation_info(self) -> dict:
        return self.info

if __name__ == "__main__":
    args = argumentParser()
    prep_address = args.prep
    print(f"OMM Delegation Details for prep: {prep_address}")
    instance = FetchData(prep_address)
    instance.populate_stakers_list()
    stakers_list: list = instance.get_stakers_list()

    # use multithreading to get delegation info of stakers
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        executor.map(instance.calculate_delegation_info, stakers_list)

    delegation_info: dict = instance.get_delegation_info()
    sorted_data: dict = dict(sorted(delegation_info.items(), key=lambda item: item[1], reverse = True))
    # save this delegation_info somewhere
    with open(f"{int(time.time())}_{prep_address}_delegations.json", "w") as outfile:
        json.dump(sorted_data, outfile) 