#!/bin/bash
GROUP=6
if [ "$GROUP" -eq 0 ]; then
    echo "Error: please update your group number!"
    exit 1  
fi
HOST=$(oc get route acmeair-main-route -n acmeair-group${GROUP} --template='{{ .spec.host }}')
PORT=80

THREAD=10
USER=999
DURATION=60
RAMP=0
DELAY=0

echo HOST=${HOST}
echo PORT=${PORT}
echo THREAD=${THREAD}
echo USER=${USER}
echo DURATION=${DURATION}
echo RAMP=${RAMP}
echo DELAY=${DELAY}

curl http://${HOST}/booking/loader/load
echo ""
curl http://${HOST}/flight/loader/load
echo ""
curl http://${HOST}/customer/loader/load?numCustomers=10000
echo ""

jmeter -n -t scripts/AcmeAir-microservices-mpJwt.jmx \
 -DusePureIDs=true \
 -JHOST=${HOST} \
 -JPORT=${PORT} \
 -JTHREAD=${THREAD} \
 -JUSER=${USER} \
 -JDURATION=${DURATION} \
 -JRAMP=${RAMP} \
 -JDELAY=${DELAY}