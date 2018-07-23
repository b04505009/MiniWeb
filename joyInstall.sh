#! /usr/bin/env bash
pushd ..
git clone http://github.com/cisco/joy
pushd joy/
sudo apt-get install build-essential libssl-dev libpcap-dev libcurl4-openssl-dev -y
./config --lib-path /usr/lib/x86_64-linux-gnu
make
popd
popd
