import express from 'express';
import { Cipher, createCipheriv, createDecipheriv, randomBytes } from 'crypto';
import { XMLParser, XMLBuilder, XMLValidator } from "fast-xml-parser";
import fetch from 'node-fetch';

const app = express();
const aesBase64Key = 'an7QvFSuAWe4iNE2b6viiGnaMXTVuEBbKUlFWJcYynB';
const sendAPIEndpoint = 'https://chatbot.weixin.qq.com/openapi/sendmsg/fWjBEcv7W6cNEupm0uPssL5O5JBUt3';
const algorithm = 'aes-256-cbc';
const iv = Buffer.alloc(16, 0);
const key = Buffer.from(aesBase64Key + "=", 'base64');

app.use(express.json());

export function decryptToJson(text) {
    //const message = 'CF9ix1B1EPnFz1kFfq9cfIa3Cwai4KgpYnUcoJuB0U8xtPUgeceWhkac9nH0byLFsic4RdYWfMquFIffrILg0dN8CQhOhzS9jNcx/Q9n0mTIYOBauxSvD5u89LNrHYT5SQj3Gxyab8iG3p3CLTC55QNIGQ++kEcnytgxp6U+cM6lwvMO4iG8SvuFNzfmelptR/Wyn8mHtV3m7PmeSldQluCCBS1UrGV30aYvByT0mTyqCFody627Xo86/cyGcteS/CwnMapWFQTlLPVXjkQvB1/eh5tqsIX0Iis7oCqg3WoZCj3T5Vs/vmLMuWgMI5IwMoJ3IUxLz38PT+mptM4DVdEu4rNiUUKaD02RdyN4E7T3I/caRumoCDc7l4ubqzJ/ECrl5ymjjq4deQpxUNt13XzjzOug+TIGB4O0/5a3M20TRJ/j9qKp4APBJYtmFTETIFgqt5ng/D6CEGHciHg8BQp/AgHndff7gD0EgoQ3elFl1TsEIBHChE0DHVoR/Tqa';
    const messagebuf = Buffer.from(text, 'base64');
    const decipher = createDecipheriv(algorithm, key, iv);
    decipher.setAutoPadding(true);
    const xml_padded = decipher.update(messagebuf, 'base64', 'utf8');
    const parser = new XMLParser();
    return parser.parse(xml_padded);
}

export function extractMessageOptions(messageJson) {
    return {
        xml: {
            appid: messageJson.appid,
            openid: messageJson.userid,
            channel: messageJson.channel,
        }
    };
}

export function encryptMessage(content, messageJson) {
    const messageBody = extractMessageOptions(messageJson);
    messageBody.xml.msg = content;
    const builder = new XMLBuilder();
    const xmlString = builder.build(messageBody);
    console.log('Built XML message body as', xmlString);
    const bufferedXml = Buffer.concat([randomBytes(20), Buffer.from(xmlString)]);
    console.log('Buffered bytes: ', bufferedXml);
    const cipher = createCipheriv(algorithm, key, iv);
    cipher.setAutoPadding(true);
    let encrypted = cipher.update(bufferedXml);
    encrypted = Buffer.concat([encrypted, cipher.final()]).toString('base64');
    console.log('encrypted text: ', encrypted);
    return encrypted;
}

export async function sendResponse(messageJson) {
    const content = "haha"; // TODO(fp): add more to dummy content
    var encryptedPayload = encryptMessage(content, messageJson);
    const body = { encrypt: encryptedPayload };
    try {
        const response = await fetch(sendAPIEndpoint, {
            method: 'post',
            body: JSON.stringify(body),
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const data = await response.json();
        console.log('Returned wechat sending message response: ', data);
    } catch (error) {
        console.log('Returned wechat sending message error: ', error);
    }
}

app.post('/', function (req, res) {
    console.log('Get raw body: ', req.body);
    if (req.body.encrypted === undefined) {
        console.log("Empty body!");
        res.send();
        return;
    }
    const messageJson = decryptToJson(req.body.encrypted).xml;
    console.log(messageJson);
    sendResponse(messageJson);
    res.send('OK');
});

app.get('/', function (req, res) {
    console.log(req.body);
    res.send('Get World!');
});

app.listen(8880, function () {
    console.log('Example app listening on port 8880!');
});
