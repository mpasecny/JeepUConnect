import json
import pandas as pd

# Načti JSON soubor
with open('temp', 'r', encoding='utf-8') as f:
    content = f.read()

# Odstraň logovací řádek na začátku
json_start = content.find('{')
json_content = content[json_start:]

# Parse JSON
data = json.loads(json_content)

# Extrahuj services
services = data['vehicles'][0]['services']

# Vytvoř seznam s potřebnými daty
table_data = []
for service in services:
    table_data.append({
        'ServiceCode': service['service'],
        'VehicleCapable': service['vehicleCapable'],
        'ServiceEnabled': service['serviceEnabled']
    })

# Vytvoř DataFrame
df = pd.DataFrame(table_data)

# Ulož jako CSV
df.to_csv('services_table.csv', index=False, encoding='utf-8-sig')

# Ulož také jako HTML tabulku
df.to_html('services_table.html', index=False)

# Vypiš tabulku do konzole
print(df.to_string(index=False))
print(f"\nCelkem služeb: {len(df)}")
print(f"\nTabulka byla uložena jako:")
print("  - services_table.csv")
print("  - services_table.html")
