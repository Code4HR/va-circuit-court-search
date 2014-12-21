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

* Run the server
```
python courts.py
```

* Browse to `http://0.0.0.0:5000/`
