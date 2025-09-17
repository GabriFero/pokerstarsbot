import json
from pokerstars.request_jsons.top_match import *
from pokerstars.request_jsons.alberatura import *
def get_alberatura(clt):
    alb_response = clt.get(url=alberatura_url,
                           headers=alberatura_header,
                           timeout=15)
    #print(alb_response)
    return json.loads(alb_response.text)


def get_top_match(regulator_event_id: str, clt):
    top_response = clt.get(url=f"{top_url}{regulator_event_id}",
                           params=top_params,
                           headers=top_header,
                           timeout=15)
    # print("Top match response:", top_response.text)
    return top_response


def get_alberatura_prematch(clt):  # useless
    url = "https://betting.pokerstars.it/api/lettura-palinsesto-sport/palinsesto/prematch/alberaturaPrematch"
    prematch_response = clt.get(url=url,
                                headers=alberatura_header,
                                timeout=15)
    return prematch_response


def get_every_live_game(alberatura_content, top_pool, clt):
    page_dict = {}

    args = [(key, clt) for key in alberatura_content["avvenimentoFeMap"]]

    for res in top_pool.map_async(call_page_httpx, args).get():
        page_dict[res[0]] = res[1]

    return page_dict


def call_page_httpx(args):
    response = args[1].get(url=f"{top_url}{args[0]}",
                           params=top_params,
                           headers=top_header,
                           timeout=15)
    # print(response.elapsed)
    return args[0], json.loads(response.text)
