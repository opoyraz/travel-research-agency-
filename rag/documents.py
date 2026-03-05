"""
Travel Research Agency — Travel Advisory Documents
Mock data mirroring US State Department format.
In production, replace with real API calls or scraped advisories.
"""

TRAVEL_ADVISORIES = [
    {
        "country": "Japan",
        "code": "JP",
        "advisory_level": 1,
        "title": "Exercise Normal Precautions",
        "last_updated": "2026-02-15",
        "content": """Japan - Level 1: Exercise Normal Precautions.
Japan is generally safe for travelers. Petty crime rates are very low
compared to other developed countries. Public transportation is extremely
reliable and safe. Earthquakes and typhoons are natural hazards — monitor
local weather alerts. The national emergency number is 110 for police
and 119 for fire/ambulance. English signage is common in Tokyo, Osaka,
and Kyoto but limited in rural areas. Japan requires no visa for US
citizens staying up to 90 days for tourism.""",
    },
    {
        "country": "Japan",
        "code": "JP",
        "advisory_level": 1,
        "title": "Health & Safety",
        "last_updated": "2026-02-15",
        "content": """Japan Health Information:
No mandatory vaccinations for US travelers. Tap water is safe to drink.
Healthcare quality is excellent. Travel insurance recommended as hospitals
may require upfront payment. Pharmacies (drugstores) are common but
prescription medications may differ from US equivalents. Carry a copy
of any prescriptions. Food allergies: many dishes contain soy, seafood,
or wheat — carry allergy cards in Japanese. Air quality is generally good.
Summer (June-September) can be extremely hot and humid.""",
    },
    {
        "country": "France",
        "code": "FR",
        "advisory_level": 2,
        "title": "Exercise Increased Caution",
        "last_updated": "2026-01-20",
        "content": """France - Level 2: Exercise Increased Caution.
Exercise increased caution due to terrorism and civil unrest. Terrorist
attacks are possible with little or no warning. Be vigilant in tourist
areas and public transportation. Pickpocketing is common in Paris,
especially near the Eiffel Tower, Louvre, and on the Metro. Emergency
number is 112 (EU standard) or 17 for police. France is part of the
Schengen area — US citizens may stay up to 90 days without a visa
within any 180-day period.""",
    },
    {
        "country": "France",
        "code": "FR",
        "advisory_level": 2,
        "title": "Health & Safety",
        "last_updated": "2026-01-20",
        "content": """France Health Information:
No mandatory vaccinations. European Health Insurance Card (EHIC) not
valid for US citizens — purchase travel insurance. Pharmacies (marked
with green cross) are widely available. Tap water is safe in cities.
Emergency medical service (SAMU): dial 15. Hospitals are excellent but
waiting times can be long. Carry prescription medications in original
packaging with doctor's note. Air pollution alerts may occur in summer
in Paris — check local advisories.""",
    },
    {
        "country": "Brazil",
        "code": "BR",
        "advisory_level": 2,
        "title": "Exercise Increased Caution",
        "last_updated": "2026-02-01",
        "content": """Brazil - Level 2: Exercise Increased Caution.
Exercise increased caution due to crime. Violent crime such as armed
robbery and carjacking occurs in urban areas. Avoid displaying
expensive jewelry or electronics. Use registered taxis or ride-sharing
apps. Stay in well-lit, populated areas at night. US citizens need
an e-Visa — apply at least 72 hours before travel at $80. Emergency
number: 190 for police, 192 for ambulance. The tourist police
(Delegacia de Atendimento ao Turista) can assist in major cities.""",
    },
    {
        "country": "Thailand",
        "code": "TH",
        "advisory_level": 1,
        "title": "Exercise Normal Precautions",
        "last_updated": "2026-01-10",
        "content": """Thailand - Level 1: Exercise Normal Precautions.
Thailand is generally safe for tourists. The southern border provinces
(Yala, Pattani, Narathiwat, Songkhla) have ongoing conflict — avoid
these areas. Petty crime and scams targeting tourists occur in Bangkok
and tourist areas. Always use metered taxis or Grab (ride-sharing).
US citizens can stay up to 30 days visa-free. Emergency: 1155
(Tourist Police, English-speaking). Monsoon season: June-October
(flooding possible). Respect local customs at temples — dress modestly.""",
    },
]
