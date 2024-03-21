# FailSecureDoor_RP2
Firmware for Fail-secure door controller of access control room. Activate when power outage is occured.

### Fail-Secure Door Controller with Pico W (RP2040)
The firmware is written in micropython, stored in folder `rp2`. `ampy` can be used to upload the codes to MCU.
To upload firmware.
1. Upload micropython firmware .uf2 of Pico W. The latest firmware can be founded in here
    https://micropython.org/download/RPI_PICO_W/
2. `cd` to the repo
```
cd access_control_rpzk
cd rp2
```
3. Run `ampy put` to put the network configuration .json file into MCU
```
ampy -p /dev/ttyACM0 network_config.json
```
4. Run `ampy put` to put the codes into MCU
```
ampy -p /dev/ttyACM0 put umqtt 
ampy -p /dev/ttyACM0 put main.py main.py q_scheduler.py secure_doorlock.py
```
5. Verify the upload files by `ampy ls` or `ampy get`
```
ampy -p /dev/ttyACM0 ls
```
6. Reset MCU and run it.




### Worker for ZKTeco's Access Control & FailSecure Door
To deploy using Docker
1. `cd` to the repo
```
cd access_control_rpzk
```
2. Build worker image
```
sudo docker build -t acworker-image .
```
3. Run container from built image
```
sudo docker run -d --network=host --name=acworker acworker-image
```
