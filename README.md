# Activation Steps
1. Change ```.env.txt``` into ```.env```
2. Change ```JMETER_PATH``` into TA's or Professor's JMeter path
3. Get the token from Open Shift Token and copy paste the info behind ```oc login``` such as ```--token=sha256~cCS4OwPYo9l9o8TwLJn3TlALVy8A_oALfWHlO8xpwFo --server=https://c104-e.ca-tor.containers.cloud.ibm.com:30689```
4. Paste the Open Shift Token into ```OPENSHIFT_TOKEN``` in ```.env```
5. Execute ```runEnv.sh``` and it will build a virtual Python env and login in to Open Shift
6. Execute ```driver.py``` to activate the while self-adaptive system
