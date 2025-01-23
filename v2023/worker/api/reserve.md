For request to reserve the room, send this to REDIS
Redis channel "settag:access_control.profacex.reserve_request"
```
{
    "epoch_start":"",
    "epoch_end":""
}
```


Response message
(Listen to redis channel "tag:access_control.profacex.response")
```
{
    "reserve":{
        "id": "100 (default ID)",
        "otp": "otp value (4-digit)"
    }
}
```
