# ipy-budget
a simple python package to grab multi-sheet budget data from Google Sheets

### format
Budget format assumes columns A:G used with labels {date, notes, amount, category, person, shared, recreational}.  

### example usage
See the [jupyter notebook](https://github.com/lots-of-things/ipy-budget/blob/master/budget_viz.ipynb) for inspiration on graphing expenses and per person splits.  Also included a [notebook](https://github.com/lots-of-things/ipy-budget/blob/master/budget_table.ipynb) using [qgrid](https://github.com/quantopian/qgrid) for filtering and sorting the table via GUI (not available online, only when running kernel).

### package implementation
Uses the [Gsheets python API](https://developers.google.com/sheets/api/quickstart/python).  Added a  [trick](https://stackoverflow.com/questions/24890146/how-to-get-google-analytics-credentials-without-gflags-using-run-flow-instea
) so that it only has to be run from the command line once (hopefully).
