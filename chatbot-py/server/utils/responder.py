import openai

class Responder():
    
    def generateEchoResponse(self, message):
        if message != None and len(message) > 0:
            return message
        return 'haha'
    
    def generateGPTResponse(self, message, event='userEnter'):
        if message == None or len(message) == 0:
            if event == 'userEnter':
                return "说点啥吧! 我好无聊。。"
            else:
                return "再见！祝你今天过得愉快！"
        cl=openai.OpenAI(api_key='{env.key}') # TODO: replace env key
        cc=cl.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a knowledgable FunnyBot. Your answer should be short and in instant message style."},
                {"role": "user", "content": message}
            ], 
            stream=True, max_tokens=120, top_p=.69, model="gpt-3.5-turbo"
        )
        generated_texts = "".join([
            ck.choices[0].delta.content or "" for ck in cc
        ])
        return generated_texts

if __name__ == '__main__':
    responder = Responder()
    print(responder.generateGPTResponse("Do penguin farts propel?"))