import datetime
from pydantic import BaseModel
import xml.etree.ElementTree as ET
from dicttoxml import dicttoxml

class Message(BaseModel):
    encrypted: str | None = None

class WXIncomingMessage():
    user_id: str
    app_id: str
    msg: str | None = None
    event: str | None = None
    source: int | None = None
    kfstate: int | None = None
    channel: int | None = None
    assessment: int | None = None
    create_time: datetime

    def __init__(self, xmlString: str) -> None:
        tree = ET.ElementTree(ET.fromstring(xmlString))
        self.user_id = tree.findtext('userid')
        self.app_id = tree.findtext('appid')
        self.msg = tree.find('content').findtext('msg')
        self.channel = tree.findtext('channel')
        self.event = tree.findtext('event')
        # TODO(fp): find the rest...

class WXOutgoingMessage():
    appid: str
    openid: str
    channel: int | None = None
    msg: str | None = None

    def __init__(self, appid: str, incomingMessage: WXIncomingMessage, responseTextMessage: str) -> None:
        self.appid = appid
        self.openid = incomingMessage.user_id
        self.channel = incomingMessage.channel
        self.msg = responseTextMessage

    def buildXmlString(self):
        return dicttoxml(vars(self), xml_declaration=False, attr_type=False, custom_root='xml') 