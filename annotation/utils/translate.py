import http.client
import hashlib
import urllib
import random
import json


class BDT:
    def __init__(self):
        self.appid = '20200116000375850'
        self.secretKey = 'iDqPKmfLykIvbtp1JWV6'
        self.url = '/api/trans/vip/translate'
        self.fromLang = 'en'
        self.toLang = 'zh'
        self.httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')

    def translate(self, source):
        salt = random.randint(32768, 65536)
        sign = self.appid + source + str(salt) + self.secretKey
        sign = hashlib.md5(sign.encode()).hexdigest()
        url = self.url + '?appid=' + self.appid + '&q=' + urllib.parse.quote(
            source) + '&from=' + self.fromLang + '&to=' + self.toLang + '&salt=' + str(
            salt) + '&sign=' + sign
        self.httpClient.request('GET', url)
        response = self.httpClient.getresponse()
        result = json.loads(response.read().decode("utf-8"))
        return [item['dst'] for item in result['trans_result']]


if __name__ == '__main__':
    translator = BDT()
    print(translator.translate('i argument_mining a dog\ni argument_mining a pig'))
    print(translator.translate('i argument_mining a dog, i argument_mining a pig'))
