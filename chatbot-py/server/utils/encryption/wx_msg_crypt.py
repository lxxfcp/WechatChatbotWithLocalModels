#!/usr/bin/env python
# -*- encoding:utf-8 -*-

""" 对企业微信发送给企业后台的消息加解密示例代码.
@copyright: Copyright (c) 1998-2014 Tencent Inc.

"""
# ------------------------------------------------------------------------

import base64
import string
import random
import hashlib
import time
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import xml.etree.cElementTree as ET
import socket
from . import ierror
import six

"""
Migrate to cryptography lib, use 'pip install cryptography' to install
"""


class FormatException(Exception):
    pass


def throw_exception(message, exception_class=FormatException):
    """my define raise exception function"""
    raise exception_class(message)


def to_text(value, encoding='utf-8'):
    """Convert value to unicode, default encoding is utf-8
    :param value: Value to be converted
    :param encoding: Desired encoding
    """
    if not value:
        return ''
    if isinstance(value, six.text_type):
        return value
    if isinstance(value, six.binary_type):
        return value.decode(encoding)
    return six.text_type(value)


def to_binary(value, encoding='utf-8'):
    """Convert value to binary string, default encoding is utf-8
    :param value: Value to be converted
    :param encoding: Desired encoding
    """
    if not value:
        return b''
    if isinstance(value, six.binary_type):
        return value
    if isinstance(value, six.text_type):
        return value.encode(encoding)
    return to_text(value).encode(encoding)


def byte2int(c):
    if six.PY2:
        return ord(c)
    return c


class SHA1:
    """计算企业微信的消息签名接口"""

    def getSHA1(self, token, timestamp, nonce, encrypt):
        """用SHA1算法生成安全签名
        @param token:  票据
        @param timestamp: 时间戳
        @param encrypt: 密文
        @param nonce: 随机字符串
        @return: 安全签名
        """
        try:
            """Python3 encrypt is bytes, need to convert to text for sort"""
            sortlist = [token, timestamp, nonce, to_text(encrypt)]
            sortlist.sort()
            sha = hashlib.sha1()
            sha.update("".join(sortlist).encode("ascii"))
            return ierror.WXBizMsgCrypt_OK, sha.hexdigest()
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_ComputeSignature_Error, None


class XMLParse:
    """提供提取消息格式中的密文及生成回复消息格式的接口"""

    # xml消息模板   
    AES_TEXT_RESPONSE_TEMPLATE = """<xml>
<Encrypt><![CDATA[%(msg_encrypt)s]]></Encrypt>
<MsgSignature><![CDATA[%(msg_signaturet)s]]></MsgSignature>
<TimeStamp>%(timestamp)s</TimeStamp>
<Nonce><![CDATA[%(nonce)s]]></Nonce>
</xml>"""

    def extract(self, xmltext):
        """提取出xml数据包中的加密消息 
        @param xmltext: 待提取的xml字符串
        @return: 提取出的加密消息字符串
        """
        try:
            xml_tree = ET.fromstring(xmltext)
            encrypt = xml_tree.find("Encrypt")
            touser_name = xml_tree.find("ToUserName")
            return ierror.WXBizMsgCrypt_OK, encrypt.text, touser_name.text
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_ParseXml_Error, None, None

    def generate(self, encrypt, signature, timestamp, nonce):
        """生成xml消息
        @param encrypt: 加密后的消息密文
        @param signature: 安全签名
        @param timestamp: 时间戳
        @param nonce: 随机字符串
        @return: 生成的xml字符串
        """
        resp_dict = {
            'msg_encrypt': encrypt,
            'msg_signaturet': signature,
            'timestamp': timestamp,
            'nonce': nonce,
        }
        resp_xml = self.AES_TEXT_RESPONSE_TEMPLATE % resp_dict
        return resp_xml


class PKCS7Encoder():
    """提供基于PKCS7算法的加解密接口"""

    block_size = 32

    def encode(self, text):
        """ 对需要加密的明文进行填充补位
        @param text: 需要进行填充补位操作的明文
        @return: 补齐明文字符串
        """
        text_length = len(text)
        # 计算需要填充的位数
        amount_to_pad = self.block_size - (text_length % self.block_size)
        if amount_to_pad == 0:
            amount_to_pad = self.block_size
        # 获得补位所用的字符
        pad = to_binary(chr(amount_to_pad))
        return text + pad * amount_to_pad

    def decode(self, decrypted):
        """删除解密后明文的补位字符
        @param decrypted: 解密后的明文
        @return: 删除补位字符后的明文
        """
        pad = byte2int(decrypted[-1])
        if pad < 1 or pad > 32:
            pad = 0
        return decrypted[:-pad]


class Prpcrypt(object):
    """提供接收和推送给企业微信消息的加解密接口"""

    def __init__(self, key):

        # self.key = base64.b64decode(key+"=")
        self.key = key
        # 设置加解密模式为AES的CBC模式   
        # self.mode = AES.MODE_CBC
        backend = default_backend()
        self.cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(key[:16]),
            backend=backend
        )

    def encrypt(self, text, corpid=None):
        """对明文进行加密
        @param text: 需要加密的明文
        @return: 加密得到的字符串
        """
        # 16位随机字符串添加到明文开头
        text = to_binary(text)
        tmp_list = []
        tmp_list.append(to_binary(self.get_random_str()))
        length = struct.pack(b'I', socket.htonl(len(text)))
        tmp_list.append(length)
        tmp_list.append(text)
        if corpid != None:
            tmp_list.append(to_binary(corpid))

        text = b''.join(tmp_list)

        # 使用自定义的填充方式对明文进行补位填充
        pkcs7 = PKCS7Encoder()
        text = pkcs7.encode(text)
        # 加密    
        # cryptor = AES.new(self.key,self.mode,self.key[:16])
        try:
            encryptor = self.cipher.encryptor()
            ciphertext = to_binary(encryptor.update(text) + encryptor.finalize())
            # 使用BASE64对加密后的字符串进行编码
            return ierror.WXBizMsgCrypt_OK, base64.b64encode(ciphertext)
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_EncryptAES_Error, None

    def decrypt(self, text, corpid=None):
        """对解密后的明文进行补位删除
        @param text: 密文 
        @return: 删除填充补位后的明文
        """
        try:
            # cryptor = AES.new(self.key,self.mode,self.key[:16])
            decryptor = self.cipher.decryptor()
            plain_text = decryptor.update(base64.b64decode(text)) + decryptor.finalize()
            # 使用BASE64对密文进行解码，然后AES-CBC解密
            # plain_text  = cryptor.decrypt(base64.b64decode(text))
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_DecryptAES_Error, None
        try:
            pad = plain_text[-1]
            # 去掉补位字符串 
            # pkcs7 = PKCS7Encoder()
            # plain_text = pkcs7.encode(plain_text)
            # 去除16位随机字符串
            content = plain_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[: 4])[0])
            xml_content = content[4: xml_len + 4]
            from_corpid = content[xml_len + 4:].decode("utf8")
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_IllegalBuffer, None
        if corpid != None and from_corpid != corpid:
            return ierror.WXBizMsgCrypt_ValidateCorpid_Error, None
        return 0, xml_content

    def get_random_str(self):
        """ 随机生成16位字符串
        @return: 16位字符串
        """
        rule = string.ascii_letters + string.digits
        str = random.sample(rule, 16)
        return "".join(str)


class WXBizMsgCrypt(object):
    # 构造函数
    # @param sToken: 企业微信后台，开发者设置的Token
    # @param sEncodingAESKey: 企业微信后台，开发者设置的EncodingAESKey
    # @param sCorpId: 企业号的CorpId
    def __init__(self, sToken, sEncodingAESKey, sCorpId):
        try:
            self.key = base64.b64decode(sEncodingAESKey + "=")
            assert len(self.key) == 32
        except:
            throw_exception("[error]: EncodingAESKey unvalid !", FormatException)
            # return ierror.WXBizMsgCrypt_IllegalAesKey,None
        self.m_sToken = sToken
        self.m_sCorpid = sCorpId

        # 验证URL
        # @param sMsgSignature: 签名串，对应URL参数的msg_signature
        # @param sTimeStamp: 时间戳，对应URL参数的timestamp
        # @param sNonce: 随机串，对应URL参数的nonce
        # @param sEchoStr: 随机串，对应URL参数的echostr
        # @param sReplyEchoStr: 解密之后的echostr，当return返回0时有效
        # @return：成功0，失败返回对应的错误码

    def VerifyURL(self, sMsgSignature, sTimeStamp, sNonce, sEchoStr):
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, sTimeStamp, sNonce, sEchoStr)
        if ret != 0:
            return ret, None
        if not signature == sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        ret, sReplyEchoStr = pc.decrypt(sEchoStr, self.m_sCorpid)
        return ret, sReplyEchoStr

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        # 将企业回复用户的消息加密打包
        # @param sReplyMsg: 企业号待回复用户的消息，xml格式的字符串
        # @param sTimeStamp: 时间戳，可以自己生成，也可以用URL参数的timestamp,如为None则自动用当前时间
        # @param sNonce: 随机串，可以自己生成，也可以用URL参数的nonce
        # sEncryptMsg: 加密后的可以直接回复用户的密文，包括msg_signature, timestamp, nonce, encrypt的xml格式的字符串,
        # return：成功0，sEncryptMsg,失败返回对应的错误码None
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(sReplyMsg, self.m_sCorpid)
        if ret != 0:
            return ret, None
        if timestamp is None:
            timestamp = str(int(time.time()))
        # 生成安全签名 
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, timestamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        xmlParse = XMLParse()
        return ret, xmlParse.generate(encrypt, signature, timestamp, sNonce)

    def DecryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        # 检验消息的真实性，并且获取解密后的明文
        # @param sMsgSignature: 签名串，对应URL参数的msg_signature
        # @param sTimeStamp: 时间戳，对应URL参数的timestamp
        # @param sNonce: 随机串，对应URL参数的nonce
        # @param sPostData: 密文，对应POST请求的数据
        #  xml_content: 解密后的原文，当return返回0时有效
        # @return: 成功0，失败返回对应的错误码
        # 验证安全签名
        xmlParse = XMLParse()
        ret, encrypt, touser_name = xmlParse.extract(sPostData)
        if ret != 0:
            return ret, None
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, sTimeStamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        if not signature == sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        ret, xml_content = pc.decrypt(encrypt, self.m_sCorpid)
        return ret, xml_content
    
if __name__ == '__main__':
    #message = 'QbntrHsYXFC5UNGAkTkFgbP6CkAhCJzCUeGEfbhofTolLI6ZEQbka+4BzwpsXFTFfLQH5jlWaQLm1e2YRunu+nSNhlb3Q+M1FHdIM25ZGIet3fEikD6U8jxIscKKS5osmHx/YiXt2/6FjXa+X4lUFk4XUxqwPSr23QlLZXq408k='
    #message = 'CF9ix1B1EPnFz1kFfq9cfIa3Cwai4KgpYnUcoJuB0U8xtPUgeceWhkac9nH0byLFsic4RdYWfMquFIffrILg0dN8CQhOhzS9jNcx/Q9n0mTIYOBauxSvD5u89LNrHYT5SQj3Gxyab8iG3p3CLTC55QNIGQ++kEcnytgxp6U+cM6lwvMO4iG8SvuFNzfmelptR/Wyn8mHtV3m7PmeSldQluCCBS1UrGV30aYvByT0mTyqCFody627Xo86/cyGcteS/CwnMapWFQTlLPVXjkQvB1/eh5tqsIX0Iis7oCqg3WoZCj3T5Vs/vmLMuWgMI5IwMoJ3IUxLz38PT+mptM4DVdEu4rNiUUKaD02RdyN4E7T3I/caRumoCDc7l4ubqzJ/ECrl5ymjjq4deQpxUNt13XzjzOug+TIGB4O0/5a3M20TRJ/j9qKp4APBJYtmFTETIFgqt5ng/D6CEGHciHg8BQp/AgHndff7gD0EgoQ3elFl1TsEIBHChE0DHVoR/Tqa'
    message = 'QwhtqduQfYSHweN/yH9UUjgc8IUiKDMtYMMWblYoXN2utfoFlvkgrq5mPNiCCZ8BEUoqa3Utw+vVGkpPM2OPXZqaQEwa/Dqe+T3bKsjiJjVtdHBt0hP383Z7hP8iuB63nmLqvp5LT4ykoH+VqDi+W9DFv1pmCm9HgV/e9IMDPPfk2NHY/6RgfUttUSlsBNkQdIbTOYJrrpL88ebiLIznvWpkjq8nVjfVmvBFezC4i1mwF8g5/k+nkpOd2QfIIsLru3jGVvgORpwuTSDceE2ikkwIsHcEiWhm/M6CR/cWahEVfLqGAEb2gqKCK6+rZmlWPUcI1KlpfchkbM7uIrM6kJOBwY4LaxcoA/cFvioqoN0r1lqTAqfWXlZOnqdzla3c'
    aesBase64Key = 'an7QvFSuAWe4iNE2b6viiGnaMXTVuEBbKUlFWJcYynB'
    token = 'fWjBEcv7W6cNEupm0uPssL5O5JBUt3'
    appid = 'TeRqEgcgCHWMK1f'
    decrypt_test = Prpcrypt(base64.b64decode(aesBase64Key + "="))
    ret, message = decrypt_test.decrypt(message)
    if ret == 0:
        print(message)
