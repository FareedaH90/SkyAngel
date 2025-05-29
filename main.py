from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import requests

app = FastAPI()

# Allow CORS for Vapi or browser-based access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Airtable Configuration
AIRTABLE_API_KEY="pat9W9f13p1LvD6db.a41c444b784d5409e9b8a2482a3f14c7f04a9893b7033e815b1418fd974caf85"
AIRTABLE_BASE_ID = "appFb4bEEgtc3f8Bw"
AIRTABLE_TABLE_NAME = "Passengers"
AIRTABLE_URL=f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# Helper function to get Airtable Record ID by PNR
def get_record_id_by_pnr(pnr: str):
    formula = f"PNR='{pnr}'"
    response = requests.get(f"{AIRTABLE_URL}?filterByFormula={formula}", headers=HEADERS)
    records = response.json().get("records", [])
    return records[0]["id"] if records else None

# 1. Find Passenger by Full Name + PNR
@app.post("/find-passenger")
async def find_passenger(request: Request):
    data = await request.json()
    name = data.get("name", "").strip()
    pnr = data.get("pnr", "").strip().upper()

    formula = f"AND({{Full Name}}='{name}', PNR='{pnr}')"
    response = requests.get(f"{AIRTABLE_URL}?filterByFormula={formula}", headers=HEADERS)
    records = response.json().get("records", [])

    if not records:
        return {"error": "Passenger not found"}

    fields = records[0]["fields"]
   return {
    "seat": fields.get("Seat Number", ""),
    "meal": fields.get("Meal Preference", ""),
    "gate": fields.get("Gate", ""),
    "terminal": fields.get("Terminal", ""),
    "boarding_time": fields.get("Boarding Time", ""),
    "flight_number": fields.get("Flight Number", ""),
    "destination": fields.get("Arrival City (from Flight)", "")
}


# 2. Update Meal
@app.post("/update-meal")
async def update_meal(request: Request):
    data = await request.json()
    pnr = data.get("pnr", "").strip().upper()
    meal = data.get("meal", "")

    record_id = get_record_id_by_pnr(pnr)
    if not record_id:
        return {"error": "PNR not found"}

    update = {"fields": {"Meal Preference": meal}}
    requests.patch(f"{AIRTABLE_URL}/{record_id}", headers=HEADERS, json=update)
    return {"status": "Meal updated"}

# 3. Update Seat
@app.post("/update-seat")
async def update_seat(request: Request):
    data = await request.json()
    pnr = data.get("pnr", "").strip().upper()
    seat = data.get("seat", "")

    record_id = get_record_id_by_pnr(pnr)
    if not record_id:
        return {"error": "PNR not found"}

    update = {"fields": {"Seat Number": seat}}
    requests.patch(f"{AIRTABLE_URL}/{record_id}", headers=HEADERS, json=update)
    return {"status": "Seat updated"}

# 4. Check-in Endpoint
@app.post("/check-in")
async def check_in(request: Request):
    data = await request.json()
    pnr = data.get("pnr", "").strip().upper()

    record_id = get_record_id_by_pnr(pnr)
    if not record_id:
        return {"error": "PNR not found"}

    checkin_time = datetime.now().isoformat()
    boarding_pass_url = f"https://skyangel.fly/boarding-pass/{pnr}"

    update = {
        "fields": {
            "CheckInStatus": "Checked In",
            "CheckInTime": checkin_time,
            "Boarding Pass Link": boarding_pass_url
        }
    }

    requests.patch(f"{AIRTABLE_URL}/{record_id}", headers=HEADERS, json=update)

    record = requests.get(f"{AIRTABLE_URL}/{record_id}", headers=HEADERS).json()
    fields = record.get("fields", {})

    return {
        "gate": fields.get("Gate", ""),
        "terminal": fields.get("Terminal", ""),
        "boarding_time": fields.get("Boarding Time", ""),
        "boarding_pass_url": boarding_pass_url
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
