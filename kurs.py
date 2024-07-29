import requests


def return_currency():

    respose = requests.get('https://nbu.uz/en/exchange-rates/json/')

    return respose.json()[18]["cb_price"]

print(return_currency())