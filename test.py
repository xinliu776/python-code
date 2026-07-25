import os
from openai import OpenAI

client = OpenAI(
    api_key=('sk-5e11b687b59c46bf995e58926d551847'),
    base_url="https://api.deepseek.com")


messages=[{"role": "system", "content": "你是一个教agent开发的老师,对话时不会一次性说很多字,而是在对话中逐步教对方"}]
while True:
    print("输入内容")
    user_input=input()
    if user_input=="1122345":
        break

    messages.append({"role":"user","content":user_input})
    response=client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=messages,
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking":{"type":"enabled"}}
    )
    print(response.choices[0].message.content)
    messages.append({"role":"system","content":response.choices[0].message.content})