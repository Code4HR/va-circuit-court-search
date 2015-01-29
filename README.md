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

## Courts that denote felony or misdemeanor in case number
- CharlotteCircuitCourt - case number has F/M after year (i.e. F00001)
- ChesterfieldCircuitCourt - case number has F/M after year (i.e. F00001)
- GoochlandCircuitCourt - case number has F/M before case number (i.e. 0000F1)
- LeeCircuitCourt - case number has F/M after year and one 0 (i.e. 0F0001)
- PageCircuitCourt - case number has F/M after year (i.e. F00001)
- RichmondCityCircuitCourt - case number has F/M after year (i.e. F00001)
- WiseCircuitCourt - case number has F/M after year (i.e. F00001)

## Court with case numbers that don't reset each year
- AmherstCircuitCourt - (2014: 14890 - 15204)
- BedfordCircuitCourt - (2014: 11169 - 11554)
- BristolCircuitCourt - (2014: 1018 - 1483)
- ClarkeCircuitCourt - (2014: 7390 - 7675)
- FranklinCircuitCourt - (2014: 19481 - 19850, 56075 - 56757)
- LoudounCircuitCourt - (2014: 26174 - 27371) (CR00)
- MadisonCircuitCourt - (2014: 5577 - 5705)
- RadfordCircuitCourt - (2014: 12707 - 13605)
- RussellCircuitCourt - (2014: 2681 - 2768, 15845 - 15999, 16959 - 17891)
- WilliamsburgJamesCityCountyCircuitCourt - (2014: 23238 - 24221)
- YorkCountyPoquosonCircuitCourt - (2014: 8011 - 8446)

## Courts without normal case numbers
- AmherstCircuitCourt - cases commenced by reinstatement use original case number with letter (A, B, ...) after CRYY
- BristolCircuitCourt - probation violations have same case number with a V after CRYY
- CliftonForgeCircuitCourt - independent city until 2001, now part of Alleghany County
- VirginiaBeachCircuitCourt - cases from 2014 on different website
- YorkCountyPoquosonCircuitCourt - cases commenced by reinstatement have different numbering 
