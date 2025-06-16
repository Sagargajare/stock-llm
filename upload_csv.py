import sys
import requests

API_URL = 'http://localhost:5001/api/stocks/upload_csv'

def upload_csv(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'text/csv')}
        response = requests.post(API_URL, files=files)
        print('Status code:', response.status_code)
        print('Response:', response.json())

def main():
    if len(sys.argv) != 2:
        print('Usage: python upload_csv.py <path_to_csv_file>')
        sys.exit(1)
    file_path = sys.argv[1]
    upload_csv(file_path)

if __name__ == '__main__':
    main() 