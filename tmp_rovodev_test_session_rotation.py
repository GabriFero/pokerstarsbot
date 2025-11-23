import requests

url = "https://areaprivata.pokerstars.it/api/authentication-ms/v1/logout"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Authorization": "Bearer eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwidGFnIjoiZXIzRXVjT2xGd0g1alhLTEQ0dzNadyIsImFsZyI6IkEyNTZHQ01LVyIsIml2IjoiZXhvdWdXRjNfcTBXSFkxSSJ9.obcM9BgcwKZnt1M3jqq22QOBadg1CWYtze7IN1YbmM0.LSOwugPiBD_1-04r.rIFdMKbPUn7wcSGg2iXdJH48Z5nKQFeozOtiCD4JyxSVV-AORYrcc7kc0CzkasOQ9tFIgfHcHBO4M_bj9BbLu5GSH4Bccrw2NlqBED3tnesQt2mht79TUYg4m8thxYfKHB_XbcHniQ9TbWlWST6BA-mgjzihphnWqjqDGlzDJFPn6Bsi8EyiYFijmiFtv7Xy8JgNxCChFa88oWcQ1IYoihaolYFM10SMeAPmuCvbXHk8VHu0j7SILpWvWqcGfB4fTBQSibHV3oxLGLXym52BxTrYFad8iKwLnrnXcG0o-qwDNRecLbTJi67kTPqTSCRXaDfk9_Iu89LHBtgCLC11_qkKfw5RiSCTIP9w305Pg3bfoz0hRMXDQHC-H_Lw5S5A7lW6avco1zEu-6yIoibRez9_Ebf3E9xvhI2cAAmMdOW8sziJwtLO_JcsHiPnbZLvVFfLM20h_UxQ1Gc6peSPEvggE_7n84TlwmDZuNfQZaxStRCNprSN-4pqVfIs-VQ5EhcofFZ0wSQ5q-xoeG6CEgAEBgJ2v1ijOFC-GOGnE0EnYA.DJia_4b3HmU58MCJHGfIFg",
    "Content-Type": "application/json",
    "Origin": "https://areaprivata.pokerstars.it",
    "Referer": "https://areaprivata.pokerstars.it/area-riservata/?endcallbackurl=https%3A%2F%2Fwww.pokerstars.it%2F&cancelcallbackurl=https%3A%2F%2Fwww.pokerstars.it%2F",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "x-channel-id": "62",
    "x-call-id": "0bb572ee-7d7f-4b06-8d46-5ef09475b4cb",
    "x-channel-info": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "x-xsrf-token": "f6c0b4dc-46dd-48e5-bd02-005403cfec4c",
}

# Prendi solo i cookie che ti servono davvero; qui è un esempio
cookies = {
    "XSRF-TOKEN": "f6c0b4dc-46dd-48e5-bd02-005403cfec4c",
    "JWT_ar": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwidGFnIjoiZXIzRXVjT2xGd0g1alhLTEQ0dzNadyIsImFsZyI6IkEyNTZHQ01LVyIsIml2IjoiZXhvdWdXRjNfcTBXSFkxSSJ9.obcM9BgcwKZnt1M3jqq22QOBadg1CWYtze7IN1YbmM0.LSOwugPiBD_1-04r.rIFdMKbPUn7wcSGg2iXdJH48Z5nKQFeozOtiCD4JyxSVV-AORYrcc7kc0CzkasOQ9tFIgfHcHBO4M_bj9BbLu5GSH4Bccrw2NlqBED3tnesQt2mht79TUYg4m8thxYfKHB_XbcHniQ9TbWlWST6BA-mgjzihphnWqjqDGlzDJFPn6Bsi8EyiYFijmiFtv7Xy8JgNxCChFa88oWcQ1IYoihaolYFM10SMeAPmuCvbXHk8VHu0j7SILpWvWqcGfB4fTBQSibHV3oxLGLXym52BxTrYFad8iKwLnrnXcG0o-qwDNRecLbTJi67kTPqTSCRXaDfk9_Iu89LHBtgCLC11_qkKfw5RiSCTIP9w305Pg3bfoz0hRMXDQHC-H_Lw5S5A7lW6avco1zEu-6yIoibRez9_Ebf3E9xvhI2cAAmMdOW8sziJwtLO_JcsHiPnbZLvVFfLM20h_UxQ1Gc6peSPEvggE_7n84TlwmDZuNfQZaxStRCNprSN-4pqVfIs-VQ5EhcofFZ0wSQ5q-xoeG6CEgAEBgJ2v1ijOFC-GOGnE0EnYA.DJia_4b3HmU58MCJHGfIFg",
    "AUTH_SESSION": "false",
    "username": "ilPazzoide",
}

# Nel tuo request originale body = {} -> content-length: 2
payload = {}  # oppure payload = None se l’endpoint accetta POST vuoto

response = requests.post(
    url,
    headers=headers,
    cookies=cookies,
    json=payload  # usa json={} per mandare "{}" come body
)

print("Status:", response.status_code)
print("Body:", response.text)
