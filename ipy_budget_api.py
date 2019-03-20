import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from pandas import DataFrame, concat, to_datetime, to_numeric

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'ipy-budget api'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-ipy-budget-api.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flags = tools.argparser.parse_args(args=[])
        flow = client.flow_from_clientsecrets(os.path.join(credential_dir,CLIENT_SECRET_FILE), SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials

#https://stackoverflow.com/questions/38245714/get-list-of-sheets-and-latest-sheet-in-google-spreadsheet-api-v4-in-python
def download_sheet_names(spreadsheetId):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
    sheets = sheet_metadata.get('sheets', '')
    return [s.get("properties", {}).get("title", "Sheet1") for s in sheets]

def download_sheet_data(spreadsheetId,rangeName):
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return []
    else:
        return values

def get_budget_data_raw(spreadsheetId,rangeSuffix='A:G'):
    return {sheetName: download_sheet_data(spreadsheetId,sheetName+'!'+rangeSuffix) for sheetName in download_sheet_names(spreadsheetId)}

def get_budget_data(spreadsheetId):
    raw_data = get_budget_data_raw(spreadsheetId)
    budget_data = concat([DataFrame(raw_data[k][1:],columns = raw_data[k][0]) for k in raw_data], sort=True)
    budget_data['date']=to_datetime(budget_data['date'])
    budget_data['amount']=to_numeric(budget_data['amount'],errors='coerce')
    return budget_data


if __name__ == '__main__':
    print ('just a test')
    sheetName = download_sheet_names('1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms')[0]
    print('Sheet Name: '+sheetName)
    sheetData = download_sheet_data('1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',sheetName+'!A:G')
    for row in sheetData:
        # Print columns A and E, which correspond to indices 0 and 4.
        print('%s, %s' % (row[0], row[4]))

