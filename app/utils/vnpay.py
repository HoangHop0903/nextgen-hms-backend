import hashlib
import hmac
import urllib.parse

class vnpay:
    def __init__(self):
        self.requestData = {}
        self.responseData = {}

    def get_mac(self, secret_key, data):
        hasher = hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha512)
        return hasher.hexdigest()

    def get_payment_url(self, vnpay_payment_url, secret_key):
        inputData = sorted(self.requestData.items())
        queryString = ''
        seq = 0
        for key, val in inputData:
            if seq == 1:
                queryString = queryString + "&" + key + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                queryString = key + '=' + urllib.parse.quote_plus(str(val))

        hashValue = self.get_mac(secret_key, queryString)
        return vnpay_payment_url + "?" + queryString + '&vnp_SecureHash=' + hashValue

    def validate_response(self, secret_key):
        vnp_SecureHash = self.responseData.get('vnp_SecureHash')
        # Xoá mã hash khỏi dữ liệu để tính toán lại
        if 'vnp_SecureHash' in self.responseData:
            self.responseData.pop('vnp_SecureHash')
        if 'vnp_SecureHashType' in self.responseData:
            self.responseData.pop('vnp_SecureHashType')

        inputData = sorted(self.responseData.items())
        queryString = ''
        seq = 0
        for key, val in inputData:
            if str(key).startswith('vnp_'):
                if seq == 1:
                    queryString = queryString + "&" + str(key) + '=' + urllib.parse.quote_plus(str(val))
                else:
                    seq = 1
                    queryString = str(key) + '=' + urllib.parse.quote_plus(str(val))

        hashValue = self.get_mac(secret_key, queryString)
        return vnp_SecureHash == hashValue
