# Distributed File System


## Prerequisites

At least 2 AWS instances
1 for nameserver
At least 1 for storage server
Client can be run locally from your host machine
They should be in one VPC

## Usage

Move nameserver.py to your AWS instance (better to /usr dir)
Move storage_server.py to you AWS instance which will be used as a storage

Run scripts on your instances using python on the nameserver
```bash
sudo python3 nameserver.py
```
And on the storage server

```bash
sudo python3 storage_server.py
```

## Architectural diagram
![alt text](https://i.ibb.co/rFBMVJn/photo-2019-11-19-15-58-03-2.jpg)

