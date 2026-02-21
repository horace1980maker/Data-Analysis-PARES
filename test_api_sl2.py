
import requests
import os

url = "http://localhost:8000/interpret/storyline2"
file_path = "FINAL_ADEL_analysis_ready.xlsx"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

print(f"Sending request to {url} with {file_path}...")
try:
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        print("Success!")
        data = response.json()
        print(f"Duration: {data.get('duration')}")
        print(f"Tables: {data.get('tables_count')}")
        
        html = data.get("report_html", "")
        if "El ecosistema con mayor conectividad es" in html:
            print("Narrative text found in response HTML.")
        else:
            print("WARNING: Narrative text NOT found in response HTML.")
            
        with open("test_api_output.html", "w", encoding="utf-8") as f_out:
            f_out.write(html)
        print("Output saved to test_api_output.html")
    else:
        print(f"Failed with status {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Error: {e}")
