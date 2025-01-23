For request to get the list of users and their info, send this to REDIS
Redis channel "settag:access_control.profacex.userinfo"
```
{
    "request":"1"
}
```


Response message
(Listen to redis channel "tag:access_control.profacex.response")
```
{
    "users":{
        "id1":{
            "username":"user1",
            "password":"pwd1",
            "privilege":""
        },

        "id2":{
            "username":"user2",
            "password":"pwd2",
            "privilege":""
        },

        "id3":{
            "username":"user3",
            "password":"pwd3",
            "privilege":""
        }

        .
        .
        .
    }
}
```
