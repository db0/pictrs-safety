# pictrs-safety
Provides an API which can be used by pict-rs `external_validation` option

# Setup
You need to copy .env_template into .env and then edit in your variables, or pass them as env variable

Afterwards you need to set up your pict-rs configuration to send the image valiation to this service's

`PICTRS__MEDIA__EXTERNAL_VALIDATION=http://127.0.0.1:14051/api/v1/scan/IPADDR`

The above assumes this services is running in the same host pict-rs is running. This will allow pict-rs to connect to it with minimum authentication

## Connecting remotely

If your service is running in a different IP, change the `127.0.0.1` above to be your address, and then use either `KNOWN_PICTRS_IDS` or `KNOWN_PICTRS_IPS` in your .env to specify the authentication for pict-rs (or else anyone in the internet can upload images to your checker)

## Serving via http

If you're going to consume this service only from your local pict-rs in localhost, you can just run this as a simply http service. 

Start it with
```python
python -i api_server.py
```

`-i` is insecure and will listen to all IPs by default. You can use `-l` to specify a different listen address

## Serving via https

If you want to run service on https, you will need need to deploy a reverse proxy in front of it

Start it with
```python
python api_server.py
```

This will only listen to 127.0.0.1

# Docker setup

TBD

# fedi-safety

This tool has been also designed to be used along with [fedi-safety](https://github.com/db0/fedi-safety). [Check the relevant instructions](https://github.com/db0/fedi-safety#pictrs-safety) on how to setup this connection.