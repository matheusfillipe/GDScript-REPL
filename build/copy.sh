#!/usr/bin/env bash
# Copies the godot build from the host

id=$(docker create build_godot)
docker cp $id:/godot/bin .
docker rm -v $id
