import json
import pycountry

countries = []
for country in list(pycountry.countries)[:198]:
    countries.append({"code": country.alpha_2.lower(), "name": country.name})

countries.sort(key=lambda x: x["name"])

with open(r"c:\Users\kondr\Desktop\AURALAVDA1\frontend\src\data\countries.json", "w", encoding="utf-8") as f:
    json.dump(countries, f, indent=2, ensure_ascii=False)
print("Saved 198 countries.")
