import json

with open("enlaces.json") as f:
    data = json.loads(f.read())
    urls = data["urls"]
    for url in urls:
        print(url["loc"])
