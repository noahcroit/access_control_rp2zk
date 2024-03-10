For request to add users and their info, send this to REDIS
Redis channel "settag:access_control.profacex.adduser"
```
{
    "id":"userid_val",
    "username":"username_val",
    "password":"password_val"
}
```


Response message
(Listen to redis channel "tag:access_control.profacex.response")
No response yet
