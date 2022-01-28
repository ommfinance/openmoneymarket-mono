# Prep ICX Delegations

This script can be used to get the vote in ICX delegated to a prep by OMM Token staker through OMM Delegation. It fetches the list of OMM token stakers, and calculates their delegation preferences, and saves a json file of all the users who voted for a specific prep, along with their voting power in ICX.

---
## How to
To run this script, you should have python3 and pip installed on your machine.

First, install the required libraries using the following command:
```sh
pip3 install -r requirements.txt
```
Now, once you have the required libraries, you can run the script as:

```sh
python3 prep-icx-delegations.py -prep PREP_ADDRESS
python3 prep-icx-delegations.py -prep hx0000000000000000000000000000000000000000 # example
```
This script will save the list of addresses and votes delegated to them via OMM onto a json file with filename 
```
timestamp_prepaddress_delegations.json
```
A format of output:
```json
{
    "hx04c8c5e5f412aa7c1986514bbbef2d269a2733fc": 466204891016976169228621,
    "hx989fa78200b23ca042e52e370128ee141187f443": 438638739301371746761613,
    "hx1be60841025db1b22126ba08ba519326603029c9": 342672743228696263962315,
    "hx5933fba534f5152ab435e02f7067e4729affa92e": 250278905329592107143901,
    "hx90899b65c16139ad4983a7a570c17db84c5162c4": 217572371437773081042390,
    "hx1747aeab5afbdabd85af027ae249897cd5165146": 199561909138062903960000,
    "hxa777652bb82b6e6a88678f2b5ccda93e3163ebc2": 156338462634667962819797
}
```
The balances are in loop. Divide by 10 ** 18 to get equivalent ICX amount.  
