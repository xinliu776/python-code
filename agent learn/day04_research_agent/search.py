import requests


def search(query):

    response=requests.get(
        "https://httpbin.org/get",
        params={
            "query":query
        }
    )

    data=response.json()

    return data

def retrieve(query):

    with open(
        "knowledge.txt",
        "r",
        encoding="utf-8"
    ) as f:
        documents=f.readlines()


    results=[]

    for doc in documents:
        if query in doc:
            results.append(doc)


    return results

