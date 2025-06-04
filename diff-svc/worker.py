import redis, json, os, httpx
from fastapi import FastAPI

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), decode_responses=True)
pb = httpx.Client(base_url=os.getenv("PB_URL"))

slack_url = os.getenv("SLACK_WEBHOOK")

def diff(event, contract):
    # naive dict diff – improve later
    return {"breaking": event["command"] == "ALTER TABLE"}

while True:
    _,_,msg = r.xread({"ddl_stream":"0-0"}, count=1, block=5000)[0]
    event = json.loads(msg["payload"])
    contract = pb.get(f"/api/collections/contracts/records/{event['table']}").json()
    result = diff(event, contract)
    if result["breaking"]:
        incident = pb.post("/api/collections/incidents/records", json={
            "table": event["table"], "details": json.dumps(result)
        }).json()
        httpx.post(slack_url, json={"text": f":rotating_light: BREAKING {event}"})
