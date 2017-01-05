# gotham
grpc toolchain prototypes


# Running

- Clone repo
- Install GO
- Create a virtual env (preferably python 3+)
- make clean
- make compile-python

If it is successful there should be a python wheel in the build/ directory.
- Try to install it to your venv `pip install tiger-1.0.0.py3.whl`
- Ensure the proxy server will run `tiger-rest-proxy` 
  - You should see a lot of log lines about not being able to connect to the upstream rpc service, this is expected

