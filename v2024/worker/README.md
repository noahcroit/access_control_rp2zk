To build the image
``` 
docker build -t img-acworker .
```

Run worker's container with built image
```
docker run --network host -d --name acworker img-acworker
