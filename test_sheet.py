import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Lsdco6nRDpUyQ0QeDMRsW00qjlR1S9wK02Siq4VQoec/edit?usp=sharing"
).sheet1

print(sheet.get_all_records())