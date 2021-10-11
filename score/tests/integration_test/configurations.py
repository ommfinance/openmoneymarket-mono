import os
from iconsdk.wallet.wallet import KeyWallet
from dotenv import dotenv_values

ROOT = os.path.abspath(os.curdir)
# print(ROOT)
ENV_PATH = os.path.abspath(os.path.join(ROOT, ".env.test"))

print(ENV_PATH)
settings = dotenv_values(ENV_PATH)

EXA = 10 ** 18
ICX = 10 ** 18
SECONDS_PER_YEAR = 31536000

OMM_SICX_ID = 4
OMM_USDS_ID = 5

keystore_private_key = settings['KEYSTORE_PRIVATE_KEY']
NETWORK = settings["NETWORK"]
CONTRACT_ADDRESSES = settings["CONTRACT_ADDRESSES"]

PREP_LIST =[
	"hxfe98328ee9f2535d086487026a48122b308612b5",
	"hxfb63e3da56b00a9ed3881857b4a04c37e4c9cdb5"
]


#
#     [
#     "hxfb687d33ab37768678d59ff47710f35348a1a4ec",
#     "hxf539cd3511254468c8944313ac6a74859e6c2bf1",
#     "hxe14cd6170fbf093acad0771e6d20676e9f85bd95"
# ]

# [
# 	"hxfe98328ee9f2535d086487026a48122b308612b5",
# 	"hxfb63e3da56b00a9ed3881857b4a04c37e4c9cdb5"
# ]

TIMESTAMP = int(settings["TIMESTAMP"])

# lending and borrow reward
LENDING_BORROW_PERCENTAGE = int(settings["LENDING_BORROW_PERCENTAGE"]) * EXA // 100
# LP and OMM staking reward
LP_OMM_STAKING_PERCENTAGE = int(settings["LP_OMM_STAKING_PERCENTAGE"]) * EXA // 100
# DAO reward percentage
DAO_DIST_PERCENTAGE = int(settings["DAO_DIST_PERCENTAGE"]) * EXA // 100
# Worker reward
WORKER_DIST_PERCENTAGE = int(settings["WORKER_DIST_PERCENTAGE"]) * EXA // 100

ICX_EMISSION = int(settings["ICX_PERCENTAGE"])
OICX_EMISSION = int(settings["OICX_EMISSION"]) * ICX_EMISSION * EXA // 10000
DICX_EMISSION = int(settings["DICX_EMISSION"]) * ICX_EMISSION * EXA // 10000

USDS_EMISSION = int(settings["USDS_PERCENTAGE"])
OUSDS_EMISSION = int(settings["OUSDS_EMISSION"]) * USDS_EMISSION * EXA // 10000
DUSDS_EMISSION = int(settings["DUSDS_EMISSION"]) * USDS_EMISSION * EXA // 10000

IUSDC_EMISSION = int(settings["IUSDC_PERCENTAGE"])
OIUSDC_EMISSION = int(settings["OIUSDC_EMISSION"]) * IUSDC_EMISSION * EXA // 10000
DIUSDC_EMISSION = int(settings["DIUSDC_EMISSION"]) * IUSDC_EMISSION * EXA // 10000

# LP and OMM staking reward

OMM_SICX_DIST_PERCENTAGE = int(settings["OMM_SICX_DIST_PERCENTAGE"]) * EXA // 100
OMM_USDS_DIST_PERCENTAGE = int(settings["OMM_USDS_DIST_PERCENTAGE"]) * EXA // 100
OMM_USDC_DIST_PERCENTAGE = int(settings["OMM_USDC_DIST_PERCENTAGE"]) * EXA // 100
OMM_DIST_PERCENTAGE = int(settings["OMM_DIST_PERCENTAGE"]) * EXA // 100

FEE_SHARING_TX_LIMIT = int(settings["FEE_SHARING_TX_LIMIT"])
LOAN_ORIGINATION_PERCENT = int(float(settings["LOAN_ORIGINATION_PERCENTAGE"]) * EXA)
MINIMUM_OMM_STAKE = int(settings["MINIMUM_OMM_STAKE"]) * EXA
OMM_UNSTAKING_PERIOD = int(settings["OMM_UNSTAKING_PERIOD"])


BORROW_THRESHOLD = int(settings["BORROW_THRESHOLD"]) * EXA // 100

halfEXA = EXA // 2

connections = {
    "mainnet": {"iconservice": "https://ctz.solidwallet.io", "nid": 1},
    "yeouido": {"iconservice": "https://bicon.net.solidwallet.io", "nid": 3},
    "euljiro": {"iconservice": "https://test-ctz.solidwallet.io", "nid": 2},
    "pagoda": {"iconservice": "https://zicon.net.solidwallet.io", "nid": 80},
    "custom": {"iconservice": "http://18.237.205.52:9000/", "nid": 3},
    "goloop": {"iconservice": "http://18.237.205.52:9082/", "nid": 3},
    "sejong": {"iconservice": "https://sejong.net.solidwallet.io", "nid": 83}
}

env = connections[NETWORK]

SERVER_URL = env["iconservice"]
NID = env["nid"]


def exaMul(a: int, b: int) -> int:
    return (halfEXA + (a * b)) // EXA


def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b


def exaPow(x: int, n: int) -> int:
    if n % 2 != 0:
        z = x
    else:
        z = EXA

    n = n // 2
    while n != 0:
        x = exaMul(x, x)

        if n % 2 != 0:
            z = exaMul(z, x)

        n = n // 2

    return z


def convertToExa(_amount: int, _decimals: int) -> int:
    if _decimals >= 0:
        return _amount * EXA // (10 ** _decimals)


def convertExaToOther(_amount: int, _decimals: int) -> int:
    if _decimals >= 0:
        return _amount * (10 ** _decimals) // EXA



