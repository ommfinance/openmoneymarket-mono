#!/bin/bash

service rabbitmq-server start

tbears genconf
tbears clear
tbears sync_mainnet
tbears start

echo "---------******---------"
python3 -m unittest register_preps.RegisterPReps
echo "---------******---------"

exec /bin/bash