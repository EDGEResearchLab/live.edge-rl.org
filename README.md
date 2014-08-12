Branch for building and testing a new live site and API structure.  This should simplify sharing logic between the various sites (prediction, vor, chase, live).

# Setup

Prereqs:

* Install `Python2`
* Install `pip`
* Use `pip` to install `virtualenv`

1. Clone the repo
2. Navigate to the cloned directory
3. Created the virtual environment: `virtualenv ./`
4. Activate the virtual environment: `. bin/activate`
5. Using pip, install the requirements: `pip install -U -r requirements.txt`
6. Run it: `python routes.py`

You should now be able to navigate in your browser to [http://localhost:5000](http://localhost:5000) and see our live page.

Note that this is not a production server and this way to run it is meant for dev purposes. There are many resources online on [how to deploy flask apps](http://flask.pocoo.org/docs/deploying/).

# Contributors

* Matt Rasband
* David Hughes
