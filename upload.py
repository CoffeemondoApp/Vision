import gspread
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

class GoogleSheet():
    def __init__(self):
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        Key = 'Auth/Cred.json'
        self.SpreadsheetId = '1AKZrGn62J9rD6MSiKPEDUj2GF-k0ThigakGzP-xcafc'
        creds = None
        creds = service_account.Credentials.from_service_account_file(Key, scopes=scope)

        service = build('sheets', 'v4', credentials=creds)
        self.sheet = service.spreadsheets()
        self.Entry = 0
        self.Exit = 0

    def ReadData(self):
        result = self.sheet.values().get(spreadsheetId=self.SpreadsheetId,range="A:C").execute()
        values = result.get('values', [])
        self.Entry = len([x for x in values if 'Entry' in x])
        self.Exit = len([x for x in values if 'Exit' in x])
     
    def sendData(self, Fecha,Registo, Hora):
        data = [[Fecha, Registo, Hora]]
        result = self.sheet.values().append(spreadsheetId = self.SpreadsheetId,
                                            range='A1',
                                            valueInputOption='USER_ENTERED',
                                            body={'values': data}).execute()