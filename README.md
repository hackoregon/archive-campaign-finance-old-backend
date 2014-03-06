Hack Oregon
=======
Welcome to Hack Oregon's official github repository.  Hack Oregon is a new kind of civic action group emerging to tackle tough questions arising between the current political establishment and the evolving landscape.  We strive to use data as a medium to spark engagement in Oregon's political process.


# Our Technical Goals
* Scrape raw data from https://secure.sos.state.or.us/orestar/CommitteeSearchFirstPage.do?startup=2 and make it easier to consume
* Visualize results


To run the demo locally you will need the following data file:

https://s3-us-west-2.amazonaws.com/mp-orestar-dump/all.pickle

Then just run 'python demo.py' and the server will run locally on port 5000.

The data is also available in CSVs. https://s3-us-west-2.amazonaws.com/mp-orestar-dump/orestar.tgz
