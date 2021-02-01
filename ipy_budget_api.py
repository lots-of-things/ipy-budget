import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from pandas import DataFrame, concat, to_datetime, to_numeric

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'sheets_secret.json'
APPLICATION_NAME = 'ipy-budget api'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_path = 'sheets.googleapis.com-ipy-budget-api.json'

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flags = tools.argparser.parse_args(args=[])
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
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

def update_sheet_data(spreadsheet_id,range_name,df=None):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    body = {
        "majorDimension": "ROWS",
        "values": [
            df.columns.tolist(),
            ] + df.values.tolist(),
    }
    return service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        body=body,
        valueInputOption='USER_ENTERED'
    ).execute()

def get_budget_data_raw(spreadsheetId,rangeSuffix='A:G'):
    return {sheetName: download_sheet_data(spreadsheetId,sheetName+'!'+rangeSuffix) for sheetName in download_sheet_names(spreadsheetId)}

def get_budget_data(spreadsheetId):
    raw_data = get_budget_data_raw(spreadsheetId)
    budget_data = concat([DataFrame(raw_data[k][1:],columns = raw_data[k][0]) for k in raw_data], sort=True)
    budget_data['date']=to_datetime(budget_data['date'])
    budget_data['amount']=to_numeric(budget_data['amount'],errors='coerce')
    return budget_data


quarter_month = {'Q1':'-01','Q2':'-04','Q3':'-07','Q4':'-10'}
def update_summary_budget_data():
    budget_data = get_budget_data('')
    budget_data['month'] = budget_data['date'].dt.to_period('Q')
    # budget_data = budget_data[budget_data['person']=='w']
    income = budget_data.loc[~budget_data['category'].isin(('invest','redis','wedding'))].copy()
    income['income'] = 'expenses'
    income.loc[income['category'].isin(('inc','tax')),'income']='income'
    res = income.groupby(['month','income'])['amount'].sum().reset_index()
    res['amount'] = (res['amount'].abs()/10).astype(int)*10
    res['month']=res['month'].astype(str).apply(lambda x: x[:4]+quarter_month[x[4:]])
    output = res.pivot(index='month', columns='income', values='amount').fillna(0).reset_index()
    cols = list(set(output.columns.tolist())-set('month'))
    order = output[cols].mean().sort_values(ascending=False).index.tolist()
    range_name = 'Income!A:C'

    update_sheet_data('',range_name,output)

    split = budget_data.loc[(budget_data['person']=='w') & ~budget_data['category'].isin(('invest','wedding'))].copy()
    split['income'] = 'expenses'
    split.loc[split['category'].isin(('inc','tax')),'income']='income'
    split_res = split.groupby(['month','income'])['amount'].sum().reset_index()
    split_res['amount'] = (split_res['amount'].abs()/10).astype(int)*10
    split_res['month']=split_res['month'].astype(str).apply(lambda x: x[:4]+quarter_month[x[4:]])
    split_output = split_res.pivot(index='month', columns='income', values='amount').fillna(0).reset_index()
    combo = output.merge(split_output,on='month')
    combo['will_income']=combo['income_y'].cumsum()/combo['income_x'].cumsum()
    combo['will_expenses']=combo['expenses_y'].cumsum()/combo['expenses_x'].cumsum()
    cols = ['month', 'will_income', 'will_expenses']
    range_name = 'Split!A:E'

    update_sheet_data('',range_name,combo[cols])

    expenses = budget_data[~budget_data['category'].isin(('inc','tax','invest','redis','wedding'))]
    res = expenses.groupby(['month','category'])['amount'].sum().reset_index()
    res['amount'] = (res['amount'].apply(lambda x: x if x < 0 else 0).abs()/10).astype(int)*10
    res['month']=res['month'].astype(str).apply(lambda x: x[:4]+quarter_month[x[4:]])
    output = res.pivot(index='month', columns='category', values='amount').fillna(0).reset_index()
    cols = list(set(output.columns.tolist())-set('month'))
    order = output[cols].mean().sort_values(ascending=False).index.tolist()
    range_name = 'Main!A:T'

    update_sheet_data('',range_name,output[['month']+order])



if __name__ == '__main__':
    update_summary_budget_data()
