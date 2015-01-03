Virginia Circuit Court Search
=======================

Virginia Courts Case Information - Statewide Searches ARE Possible

http://VACircuitCourtSearch.com

Developed at the 2014 [Virginia Coalition for Open Government](http://www.opengovva.org) Annual Conference in Roanoke, VA for journalists who need to run statewide searches on the [Virginia Circuit Court site](http://wasdmz2.courts.state.va.us/CJISWeb/circuit.jsp), but don't have the time to search each district individually.

## Running Locally

* Make sure you have Python and Pip installed. On OS X, you can use brew to install Python and you get Pip as well.
```
brew install python
```

* Install the requirements
```
pip install -r requirements.txt
```

* Set MongoDB instance
```
$ export MONGO_URI=mongodb://<dbuser>:<dbpassword>@ds027761.mongolab.com:27761/va-circuit-court-search
```
-OR-  for Windows
```
$ set MONGO_URI=mongodb://<dbuser>:<dbpassword>@ds027761.mongolab.com:27761/va-circuit-court-search
```

* Run the server
```
python courts.py
```

* Browse to `http://0.0.0.0:5000/`

## Courts without normal case numbers
AmherstCircuitCourt - case number does't reset every year
BedfordCircuitCourt - case number does't reset every year
BristolCircuitCourt - case number does't reset every year (resets at 9,999)
CharlotteCircuitCourt - case number has F/M after year (i.e. F00001)
ChesterfieldCircuitCourt - case number has F/M after year (i.e. F00001)
ClarkeCircuitCourt - case number does't reset every year
CliftonForgeCircuitCourt - independent city until 2001, now part of Alleghany County
FranklinCircuitCourt - case number does't reset every year, but there seem to be two different counters
GoochlandCircuitCourt - case number has F/M before case number (i.e. 0000F1)
LeeCircuitCourt - case number has F/M after year and one 0 (i.e. 0F0001)
LoudounCircuitCourt - case number does not start with year (first filed in 2014 is CR00026174-00)
MadisonCircuitCourt - case number does't reset every year
PageCircuitCourt - case number has F/M after year (i.e. F00001)
RadfordCircuitCourt - case number does't reset every year
RichmondCityCircuitCourt - case number has F/M after year (i.e. F00001)
RussellCircuitCourt - case number does't reset every year
VirginiaBeachCircuitCourt - cases from 2014 on different website
WilliamsburgJamesCityCountyCircuitCourt - case number does't reset every year
WiseCircuitCourt - case number has F/M after year (i.e. F00001)
YorkCountyPoquosonCircuitCourt - case number does't reset every year, cases commenced by reinstatement have different numbering 
