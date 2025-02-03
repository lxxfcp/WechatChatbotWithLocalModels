from dotenv import dotenv_values, find_dotenv

APPID_KEY = 'APPID'
TOKEN_KEY = 'TOKEN'
AES_KEY_KEY = 'ENCODING_AES_KEY'
OPENAI_API_KEY = 'OPENAI_API_KEY'

class BotProfile():

    def __init__(self) -> None:
        self.secrets = dotenv_values(find_dotenv())

    def getAppId(self):
        return self.secrets[APPID_KEY]
    
    def getToken(self):
        return self.secrets[TOKEN_KEY]
    
    def getEncodingAesKey(self):
        return self.secrets[AES_KEY_KEY]
    
class OpenAICredential():

    def __init__(self) -> None:
        self.secrets = dotenv_values(find_dotenv())

    def getAPIKey(self):
        return self.secrets[OPENAI_API_KEY]

# if __name__ == '__main__':
#     print(BotProfile().getEncodingAesKey())