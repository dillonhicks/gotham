# gotham
grpc toolchain prototypes


# Running

- Clone repo
- Install GO
- Create a virtual env (preferably python 3+)
- make clean
- make compile-python

If it is successful there should be a python wheel in the build/ directory.
- Try to install it to your venv `pip install tiger-1.0.0-py3-none-any.whl`
- Ensure the proxy server will run `tiger-rest-proxy` 
  - You should see a lot of log lines about not being able to connect to the upstream rpc service, this is expected. This is the grpc-gateway-proxy service that is automatically generated go server. Since you have yet to start the actual grpc server, theses errors makes sense.

If you can't get it to build, you should still checkout the release page and download the wheel uploaded from this package: https://github.com/dillonhicks/gotham/releases/tag/v0.0.1

You should be able to `pip install tiger-1.0.0-py3-none-any.whl`

