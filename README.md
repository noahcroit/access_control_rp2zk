# FailSecureDoor_RP2
Firmware for Fail-secure door controller of access control room. Activate when power outage is occured.




## Worker for ZKTeco's Access Control & FailSecure Door
To deploy using Docker
1. Build worker image
```
cd path/of/this/repo
sudo docker build -t acworker-image .
```
2. Run container from built image
```
sudo docker run -d --network=host --name=acworker acworker-image
```
