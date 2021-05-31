#!/bin/bash

service rabbitmq-server start

tbears genconf
tbears clear
tbears sync_mainnet
tbears start

exec /bin/bash