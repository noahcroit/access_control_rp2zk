For request to delete user, send this to REDIS
Redis channel "settag:access_control.profacex.deluser"
```
{
    "id":"userid_val",
    "username":"username_val"
}
```


Response message
(Listen to redis channel "tag:access_control.profacex.response")
No response yet
