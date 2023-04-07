from __future__ import print_function

import os.path
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheet:
    SPREADSHEET_ID = '1VXAyixt_Xt0SBfFw6g3-jDPBr9WIXw4XpJY0OgeP9-g'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = None
    def __init__(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print('flow')
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('sheets', 'v4', credentials=creds)
    def updateRangeValues(self, range, values):
        data = [{'range': range, 'values': values}]
        body = {'valueInputOption': 'USER_ENTERED', 'data': data}
        result = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.SPREADSHEET_ID, body=body).execute()
        print('{0} cells update.'.format(result.get('totalUpdatedCells')))
        # print(result)
    def reedRangeValues(self, range, fio, user_id, user_full_name, phone_number, login):
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=range).execute()
        values = result.get('values', [])
        if not values:
            print('No data found.')
            return
        for row in values:
            try:
                _ = row[0], row[1], row[2]
            except:
                update(str(int(row[0])+1), fio, user_id, user_full_name, phone_number, login)
                break

def main(fio, user_id, user_full_name, phone_number, login):
    gs = GoogleSheet()
    test_range = 'April 2023!A2:C104'
    gs.reedRangeValues(test_range, fio, user_id, user_full_name, phone_number, login)

def update(row, fio, user_id, user_full_name, phone_number, login):
    gs = GoogleSheet()
    test_range = 'April 2023!B'+row+':F'+row
    test_values = [[fio, user_id, user_full_name, phone_number, login]]
    gs.updateRangeValues(test_range, test_values)

# if __name__ == '__main__':
#     main.py()