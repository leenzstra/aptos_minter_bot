import datetime
from aptos_sdk.client import *
from aptos_sdk.account import *
from aptos_sdk.bcs import *
from requests import Session
from aptos_sdk.transactions import *


class Result:
    def __init__(self, data=None, error=None) -> None:
        self.data = data
        self.error = error

rest = Session()
rest.headers.update(
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/5320 (KHTML, like Gecko) Chrome/36.0.875.0 Mobile Safari/5320"})
base_url = "https://fullnode.mainnet.aptoslabs.com/v1"

rest_client = RestClient(base_url)
seq_num = None
gas_price = 250

acc = Account.load_key(
    "private_key")
# acc = Account.load_key(
#     "")

market_addr = "0xd1fd99c1944b84d1670a2536417e997864ad12303d19eac725891691b04d614e"
market = "0x2a1f62a1663fc7e6c08753e8fc925fbcb946c4b80c5c95a95314a16bc3ac24bc"
buy_func = "f{market_addr}::marketplaceV2::batch_buy_script"
list_func = "f{market_addr}::marketplaceV2::batch_list_script"


def get_new_listings(seq: None) -> Result:
    r = rest.get(f"{base_url}/accounts/{market}/events/0xd1fd99c1944b84d1670a2536417e997864ad12303d19eac725891691b04d614e::marketplaceV2::ListedItemsData/listing_events",
                 params={} if seq == 0 else {'start': seq})
    if r.status_code != 200:
        return Result(error=r.text)

    return Result(data=r.json())

def mint_nft_m(factory, count, account):
    args = [
        f"{count}"
    ]

    return transact(account, f"{factory}::factory::mint_with_quantity", [], args)

def list_nft_m(creator, collection, nft_name, price, account, seq):
    args = [
        [creator],
        [collection],
        [nft_name],
        [f"{price}"],
        ["0"]
    ]

    return transact(account, f"{market_addr}::marketplaceV2::batch_list_script", [], args, seq)

def change_price_m(creator, collection, nft_name, price, account, seq):
    args = [
        [creator],
        [nft_name],
        [collection],
        [f"{price}"],
        ["0"]
    ]

    return transact(account, f"{market_addr}::marketplaceV2::change_price_token", [], args, seq)

def list_nft_and_change_price(creator, collection, nft_name, price, new_price, account: Account):
    seq = rest_client.account_sequence_number(account.address())
    tx1 = list_nft_m(creator, collection, nft_name, price, account, seq)
    seq += 1
    tx2 = change_price_m(creator, collection, nft_name, new_price, account, seq)
    return (tx1, tx2)    

def buy_nft_m(creator, collection, nft_name, account: Account):
    args = [
        [creator],
        [collection],
        [nft_name],
        # [f"{price}"],
        ["0"]
    ]

    return transact(account, f"{market_addr}::marketplaceV2::batch_buy_script", [], args, rest_client.account_sequence_number(account.address()))

def transact(sender: Account, function: str, type_args: list, args: list, seq: int = None):

    txn_request = {
        "sender": f"{sender.address()}",
        "sequence_number": f"{seq_num if seq == None else seq}",
        "max_gas_amount": "10000",
        "gas_unit_price": f"{gas_price}",
        "expiration_timestamp_secs": str(int(time.time()) + 600),

        "payload": {
            "type": "entry_function_payload",
            "function": function,
            "type_arguments": type_args,
            "arguments": args
        }}

    response = rest.post(
        f"{base_url}/transactions/encode_submission", json=txn_request
    )
    if response.status_code >= 400:
        raise ApiError(response.text, response.status_code)

    to_sign = bytes.fromhex(response.json()[2:])
    signature = sender.sign(to_sign)
    txn_request["signature"] = {
        "type": "ed25519_signature",
        "public_key": f"{sender.public_key()}",
        "signature": f"{signature}",
    }

    headers = {"Content-Type": "application/json"}
    response = rest.post(
        f"{base_url}/transactions", headers=headers, json=txn_request
    )
    if response.status_code >= 400:
        raise ApiError(response.text, response.status_code)

    return response.json()["hash"]

def monitoring(buy: bool, list: bool, max_price: float, collection: str):
    list_seq = -1
    buy_seq = -1
    first = True

    while True:
        list_events = get_new_listings(list_seq+1)
        # print('search')
        for event in list_events.data:
            seq = event['sequence_number']
            # print(seq)
            list_seq = int(seq)
            price = int(event['data']['amount'])/(
                10**8)
            print("LIST", datetime.datetime.now(), seq, price,
                  event['data']['id']['token_data_id']['name'])

            if not first and buy and event['data']['id']['token_data_id']['collection'] == collection and price <= max_price:
                try:
                    tx = buy_nft_m(event['data']['id']['token_data_id']['creator'],
                                   collection, event['data']['id']['token_data_id']['name'], acc)
                except:
                    print("err")
                print(tx)
                
        time.sleep(1)

        first = False

def get_balance():
    # r = rest_client.account_resources(acc.account_address, "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>")
    r = rest.get(
        f"{base_url}/accounts/{acc.address()}/resources")
    for res in r.json():
        if res['type'] == "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>":
            return int(res['data']['coin']['value'])

def start_mint_wait():
    if not seq_num:
        seq_num = rest_client.account_sequence_number(acc.address())

    print("SEQ =", seq_num)

    now = datetime.datetime.now()
    print(now.hour)
    while True:
        if now.hour == 21:
            break

    print("ITS TIME")
    for _ in range(0, 1):
        tx = mint_nft_m(
                "0x8eafc4721064e0d0a20da5c696f8874a3c38967936f0f96b418e13f2a31dcf4c", 1, acc)
        time.sleep(0.5)
        seq_num+=1
    print(tx)

if __name__ == "__main__":

    start_mint_wait()
    
    # monitoring(True, False, 3.75,"Aptos Wizards")
    
    # list_nft_and_change_price("0x6d4336aeac8441314cacdd42ea7aae57b3fad71ea26a00186a23eb8f1fa19ffb", 
    #                           "Aptos Wizards", "Aptos Wizards #", int(4*(10**8)), int(6*(10**8)), acc)
    
    # exit(0)


# "args":[
#             "0x1d987fb9fda5453d71e5bc3ce57a74d6cddc0b245a0906a6e96b3ac1541aeda69", -creator
#             "0x10c426967466f6f7420546f776e",
#             "0x112426967466f6f7420546f776e202337333438",
#             "0x10000000000000000"
#          ]

# {
#       "name": "batch_buy_script",
#       "visibility": "public",
#       "is_entry": true,
#       "generic_type_params": [],
#       "params": [
#         "&signer",
#         "vector<address>",
#         "vector<0x1::string::String>",
#         "vector<0x1::string::String>",
#         "vector<u64>"
#       ],
#       "return": []
    # },'

# {
#   "function": "0xd1fd99c1944b84d1670a2536417e997864ad12303d19eac725891691b04d614e::marketplaceV2::batch_buy_script",
#   "type_arguments": [],
#   "arguments": [
#     [
#       "0xd987fb9fda5453d71e5bc3ce57a74d6cddc0b245a0906a6e96b3ac1541aeda69"
#     ],
#     [
#       "BigFoot Town"
#     ],
#     [
#       "BigFoot Town #2349"
#     ],
#     [
#       "0"
#     ]
#   ],
#   "type": "entry_function_payload"
# }'

# {
#   "function": "0xd1fd99c1944b84d1670a2536417e997864ad12303d19eac725891691b04d614e::marketplaceV2::batch_list_script",
#   "type_arguments": [],
#   "arguments": [
#     [
#       "0xd987fb9fda5453d71e5bc3ce57a74d6cddc0b245a0906a6e96b3ac1541aeda69"
#     ],
#     [
#       "BigFoot Town"
#     ],
#     [
#       "BigFoot Town #2349"
#     ],
#     [
#       "129000000"
#     ],
#     [
#       "0"
#     ]
#   ],
#   "type": "entry_function_payload"
# }
