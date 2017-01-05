#!/usr/bin/env bash
#
# Download protoc and use ./.local as the local install root
#
protoc_version=3.1.0
target_arch=x86_64
local_install_dir=./.local
protoc_local_install_dir=$local_install_dir/protoc
protoc_local_bin_dir=$protoc_local_install_dir/bin
protoc_local_path=$protoc_local_bin_dir/protoc

protoc_binary_pkg=protoc-$protoc_version-linux-$target_arch.zip
protoc_binary_url=https://github.com/google/protobuf/releases/download/v$protoc_version/$protoc_binary_pkg
   
if [[ "$OSTYPE" == darwin* ]]; then
    protoc_binary_pkg=protoc-$protoc_version-osx-$target_arch.zip
    protoc_binary_url=https://github.com/google/protobuf/releases/download/v$protoc_version/$protoc_binary_pkg
fi

if [ ! -e "$protoc_local_path" ]; then
 
    mkdir -p $protoc_local_install_dir
    pushd $protoc_local_install_dir
    wget $protoc_binary_url
    unzip $protoc_binary_pkg 
    rm -fv $protoc_binary_pkg
    popd

fi

echo "Using local protoc install $protoc_local_path"

