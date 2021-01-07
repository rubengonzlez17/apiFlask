#!/bin/bash
######################################################
#       Run task       #
# Authored by Ruben Gonzalez, rubengonzlez17 @ GitHub #
######################################################

curl "http://localhost:"$1"/player/update/matches"
curl "http://localhost:"$1"/player/update/players"
curl "http://localhost:"$1"/player/update/teams"