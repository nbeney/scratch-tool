#!/usr/bin/bash

function run_all() {
    local project_id=$1
    echo "========== Processing project ID: ${project_id}"
    echo "----- Metadata"
    ../main.py metadata ${project_id}
    echo "----- Download"
    ../main.py download ${project_id} --code
    echo "----- Document"
    ../main.py document ${project_id}
}

mkdir -p samples/
cd samples/

run_all 1259204833 # All Blocks
run_all 1252755893 # Snowball fight
# run_all 566019518 # Memory Blocks
run_all 592795173 # Treasure Clicker
run_all 566383445 # Hangman
run_all 566086782 # Memory
run_all 560784879 # Asteroids
run_all 565744492 # Firework
run_all 555715093 # Example - clone & video
