#!/usr/bin/env python3
"""Test the diagnose endpoint with multiple files."""
import requests

files_to_test = ['OK.xlsx', 'dabatase_general_ECO_SM.xlsx', 'FAILED.xlsx']

for filename in files_to_test:
    try:
        with open(filename, 'rb') as f:
            resp = requests.post('http://localhost:8000/diagnose', files={'file': f}, data={'lang': 'es'})
            data = resp.json()
            status = '✓' if data.get('can_convert') else '✗'
            print(f'{status} {filename}: {data.get("error_count")} errors, {data.get("warning_count")} warnings')
    except FileNotFoundError:
        print(f'? {filename}: File not found')
