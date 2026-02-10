#!/usr/bin/env python3
"""Test the diagnostic function - write to file."""

import sys
sys.path.insert(0, '.')
from pares_converter.app.converter import diagnose_file, format_diagnostic_report

# Test with ECO_SM file
issues = diagnose_file(r'dabatase_general_ECO_SM.xlsx')
formatted = format_diagnostic_report(issues, lang='es')

errors = [i for i in formatted if i['severity'] == 'error']
warnings = [i for i in formatted if i['severity'] == 'warning']

with open('diagnose_result.txt', 'w', encoding='utf-8') as f:
    f.write(f'Errors: {len(errors)}\n')
    f.write(f'Warnings: {len(warnings)}\n\n')
    f.write('=== ERRORS ===\n')
    for e in errors:
        f.write(f"  [{e['sheet']}] {e['description']}\n")
        f.write(f"    -> {e['suggested_fix']}\n")
    f.write('\n=== WARNINGS ===\n')
    for w in warnings:
        f.write(f"  [{w['sheet']}] {w['description']}\n")

print('Done - see diagnose_result.txt')
