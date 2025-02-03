import express from 'express';
import fetch from 'node-fetch';

const app = express();
const appId = 'TeRqEgcgCHWMK1f'
const sendAPIEndpoint = 'https://chatbot.weixin.qq.com/openapi/sendmsg/fWjBEcv7W6cNEupm0uPssL5O5JBUt3';


app.use(express.json());

export async function processMessage(encryptedMessage) {
    let chatBackend = `http://127.0.0.1:8000/v1alpha/apps/${appId}:chat`
    const body = { encrypted: encryptedMessage };
    const response = await fetch(chatBackend, {
        method: 'post',
        body: JSON.stringify(body),
        // http default is not json
        headers: {
            'Content-Type': 'application/json',
        },
    });
    const data = await response.json();
    console.log('Returned backend response: ', data);
    return data.encrypt;
}

export async function sendResponse(encryptedMessage) {
    try {
        var encryptedPayload = await processMessage(encryptedMessage);
        if (encryptedPayload === undefined) {
            return;
        }
        const body = { encrypt: encryptedPayload };
        console.log('Created encrypted payload as ', body);
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
        console.log('Returned wechat error: ', error);
    }
}

app.post('/', function (req, res) {
    console.log('Get raw body: ', req.body);
    if (req.body.encrypted === undefined) {
        console.log("Empty body!");
        res.send();
        return;
    }
    sendResponse(req.body.encrypted);
    res.send();
});

app.listen(8880, function () {
    console.log('Chat proxy is listening on port 8880!');
});
