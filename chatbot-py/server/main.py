import base64
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from models import Message
from models import WXIncomingMessage, WXOutgoingMessage
from utils.message_util import BotProfile
from utils.responder import Responder
from utils.encryption.wx_msg_crypt import Prpcrypt

logger = logging.getLogger("uvicorn")
responder = Responder()

app = FastAPI()
bot_profile = BotProfile()

@asynccontextmanager
async def lifespan(app: FastAPI):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

@app.get("/")
async def root():
    return {"message" : "The main API for bots."}

@app.post("/v1alpha/apps/{app_id}:chat")
async def chat(app_id: str, message: Message):
    logger.info(f'Got request with encrypted message as: {message.encrypted}')
    cryptor = Prpcrypt(base64.b64decode(bot_profile.getEncodingAesKey() + "="))
    ret, decrypted_message = cryptor.decrypt(message.encrypted)
    logger.info(f'Decrypted result {ret=} and {decrypted_message=}')
    if ret == 0:
        messageDict = WXIncomingMessage(decrypted_message)
        responseMessage = Responder().generateGPTResponse(messageDict.msg)
        outgoingMessage = WXOutgoingMessage(bot_profile.getAppId(), messageDict, responseMessage).buildXmlString()
        logger.info(f'Create responseMessage {outgoingMessage}')
        ret, encryptedOutMessage = cryptor.encrypt(outgoingMessage)
        if ret == 0:
            return {"encrypt" : encryptedOutMessage}
        else:
            return {"errorMsg" : f'Encryption errorcode {ret}'}
    return {"errorMsg": f'Decryption errorcode {ret}'}

