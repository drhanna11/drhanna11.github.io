#!/usr/bin/env python3
"""Write /workspace/site/data/listings.json with verified Phoenix-metro shops."""
import json
from pathlib import Path

DATE = "2026-11-18"

def src(url, facts):
    return {"url": url, "accessed": DATE, "facts": facts}

listings = [
  {
    "id": "robbys-appliance-repair",
    "name": "Robby's Appliance Repair",
    "slug": "robbys-appliance-repair",
    "citySlug": "phoenix",
    "phone": "6026358586",
    "phoneDisplay": "(602) 635-8586",
    "website": "https://www.robbysappliancerepair.com/",
    "email": None,
    "address": {"street": None, "city": "Phoenix", "state": "AZ", "zip": "85024"},
    "serviceAreas": ["Phoenix", "Glendale", "Scottsdale", "Peoria", "Sun City West", "Surprise", "Anthem", "Desert Hills", "Cave Creek", "Avondale"],
    "appliances": ["refrigerator", "washer", "dryer", "dishwasher", "oven-range"],
    "brands": [],
    "brandsNote": "The company website says it works with all major brands and handles electric and gas kitchen and laundry equipment.",
    "hours": "Monday–Friday 8:00 a.m.–5:00 p.m.; Saturday–Sunday 9:00 a.m.–2:00 p.m.",
    "flags": ["owner-operated"],
    "license": None,
    "facts": [
      "The company describes itself as owner-operated and says every call is handled by the same person who shows up.",
      "The website says the business has been serving the Phoenix metro for 10 years.",
      "The website lists a $75 service fee, waived if repairs are done (accessed 2026-11-18; confirm when you call).",
      "The website says same-day appointments are often available.",
      "The website lists a 10% discount for veterans and a 5% discount for senior citizens."
    ],
    "sources": [
      src("https://www.robbysappliancerepair.com/", "name, phone, ZIP 85024, hours, owner-operated claim, service areas, appliances mentioned, $75 service fee, same-day claim, veteran/senior discounts, 10 years in the metro")
    ]
  },
  {
    "id": "arizona-freeze",
    "name": "Arizona Freeze",
    "slug": "arizona-freeze",
    "citySlug": "phoenix",
    "phone": "6024997053",
    "phoneDisplay": "(602) 499-7053",
    "website": "https://azfreeze.com/",
    "email": "service@azfreeze.com",
    "address": {"street": None, "city": "Phoenix", "state": "AZ", "zip": None},
    "serviceAreas": ["Phoenix", "Tempe", "Mesa", "Chandler", "Gilbert", "Scottsdale"],
    "appliances": ["refrigerator", "freezer", "ice-maker", "washer", "dryer", "dishwasher", "oven-range", "microwave"],
    "brands": ["Samsung", "LG", "Whirlpool", "Maytag", "GE", "Frigidaire", "Bosch"],
    "brandsNote": "The company website says it repairs all major brands and specifically lists Samsung, LG, Whirlpool, Maytag, GE, Frigidaire, Bosch, and more.",
    "hours": None,
    "flags": ["owner-operated"],
    "license": None,
    "facts": [
      "The company describes itself as a direct owner-operator: you talk to the technician who does the repair, not a call center.",
      "The website says the business is EPA 608 certified and fully insured.",
      "The website says same-day service is available in most areas if you call before noon.",
      "The website states that all repairs come with a 12-month warranty on parts and labor.",
      "The website lists a $100 service call, waived if you proceed with repairs, and says estimates are free (accessed 2026-11-18; confirm when you call)."
    ],
    "sources": [
      src("https://azfreeze.com/", "name, phone, email, owner-operator claim, service areas, appliances, brands, EPA 608 and insured claim, same-day policy, 12-month warranty, $100 service call")
    ]
  },
  {
    "id": "early-bird-appliance-repair",
    "name": "Early Bird Appliance Repair",
    "slug": "early-bird-appliance-repair",
    "citySlug": "phoenix",
    "phone": "4804331766",
    "phoneDisplay": "(480) 433-1766",
    "website": "https://www.earlybirdappliancerepair.com/",
    "email": "service@earlybirdappliancerepair.com",
    "address": {"street": "3104 E Camelback Rd #1115", "city": "Phoenix", "state": "AZ", "zip": "85016"},
    "serviceAreas": ["Phoenix"],
    "appliances": ["refrigerator", "washer", "dryer", "dishwasher", "ice-maker"],
    "brands": ["Maytag", "Whirlpool", "Sub-Zero", "Wolf"],
    "brandsNote": "The company website says it repairs most brands of residential appliances, including Maytag and Whirlpool, and also services high-end brands such as Sub-Zero and Wolf.",
    "hours": None,
    "flags": ["owner-operated", "family-owned", "locally-owned"],
    "license": None,
    "facts": [
      "The company says it is a locally owned Arizona business and a small family team.",
      "The website names Chip as business owner and appliance technician. It says he has been repairing appliances since 2016 and founded Early Bird in 2017.",
      "The website advertises early-bird service calls starting at 6 a.m. and a convenient 2-hour arrival window, with reminder and en-route messages.",
      "Besides major appliances, the site also lists dryer vent cleaning, under-sink drinking-water system installation and filter changes, wine coolers, trash compactors, and warming drawers.",
      "The pages we opened list a Phoenix mailing address but do not publish a broader city-by-city service map; confirm coverage when you call or text."
    ],
    "sources": [
      src("https://www.earlybirdappliancerepair.com/", "name, locally owned claim, early-bird 6 a.m. calls, 2-hour window, address, email, phone"),
      src("https://www.earlybirdappliancerepair.com/appliance-repair", "appliances, brands including Sub-Zero and Wolf, owner Chip, founded 2017, family team")
    ]
  },
  {
    "id": "promaster-az",
    "name": "ProMaster AZ",
    "slug": "promaster-az",
    "citySlug": "phoenix",
    "phone": "6028332095",
    "phoneDisplay": "(602) 833-2095",
    "website": "https://promasteraz.com/phoenix-appliance-repair/",
    "email": "contact@promasteraz.com",
    "address": {"street": None, "city": "Phoenix", "state": "AZ", "zip": None},
    "serviceAreas": ["Phoenix", "Downtown Phoenix", "Arcadia", "Biltmore", "Ahwatukee", "Laveen", "Desert Ridge", "Encanto-Palmcroft", "Sunnyslope"],
    "appliances": ["refrigerator", "freezer", "oven-range", "dishwasher"],
    "brands": ["Whirlpool", "Samsung", "LG", "GE", "KitchenAid", "Maytag", "Sub-Zero"],
    "brandsNote": "The company website says it services all major brands, including Whirlpool, Samsung, LG, GE, KitchenAid, Maytag, and Sub-Zero.",
    "hours": None,
    "flags": ["locally-owned"],
    "license": None,
    "facts": [
      "The company website says it was founded by a technician, not a franchise, and is locally owned.",
      "The Phoenix page says the company is licensed and bonded and offers a parts and labor warranty (terms not copied here; confirm when you call).",
      "The website says same-day service is offered across Phoenix when you call before 4 p.m.",
      "The website lists a diagnostic visit of $55–$125 that applies toward the repair, and typical repair ranges for refrigerators, ovens, and laundry (accessed 2026-11-18; these are the company's published ranges, not our quotes)."
    ],
    "sources": [
      src("https://promasteraz.com/phoenix-appliance-repair/", "name, locally owned / not a franchise claim, phone, email, Phoenix service neighborhoods, appliances, brands, same-day before 4 p.m., published diagnostic fee range")
    ]
  },
  {
    "id": "frost-appliance",
    "name": "Frost Appliance",
    "slug": "frost-appliance",
    "citySlug": "phoenix",
    "phone": "6022537678",
    "phoneDisplay": "(602) 253-7678",
    "website": "https://www.frostappliancerepair.com/",
    "email": "frostappliance1981@gmail.com",
    "address": {"street": "6819 North 21st Avenue, Suite R", "city": "Phoenix", "state": "AZ", "zip": "85015"},
    "addressNotes": "The website also lists 8390 E Via de Ventura, Suite F-110, Scottsdale, AZ 85258, and a West Valley phone number, (623) 247-5400.",
    "serviceAreas": ["Phoenix", "Anthem", "Carefree", "Cave Creek", "Scottsdale", "Chandler", "Fountain Hills", "Gilbert", "Mesa", "Avondale", "Goodyear", "Litchfield Park", "Sun City", "Surprise", "Tolleson", "Glendale", "Paradise Valley", "Peoria", "Tempe"],
    "appliances": ["refrigerator", "freezer", "washer", "dryer", "dishwasher", "oven-range", "microwave", "ice-maker"],
    "brands": ["Dacor", "Whirlpool", "Wolf", "Sub-Zero", "Cove", "Bosch", "Thermador", "Asko", "Speed Queen", "GE", "True", "Scotsman", "Vulcan", "KitchenAid", "Maytag", "Blodgett", "Jenn-Air", "Electrolux", "Heatcraft"],
    "brandsNote": "The company website says it has repaired appliances of more than 50 brands and lists the brands above, plus more.",
    "hours": "Monday–Friday 9:00 a.m.–5:00 p.m.; Saturday–Sunday closed.",
    "flags": ["family-owned"],
    "license": "Arizona Registrar of Contractors #319575 (listed on the company website)",
    "facts": [
      "The company describes itself as family-owned and serving the Phoenix area since 1981.",
      "The website says the company serves both residential and commercial clients, including restaurants, schools, hospitals, and property managers.",
      "A second phone number for the West Valley, (623) 247-5400, is listed on the site.",
      "The website lists Arizona Registrar of Contractors number 319575."
    ],
    "sources": [
      src("https://www.frostappliancerepair.com/", "name, phones, addresses, email, hours, family-owned since 1981, ROC #319575, service areas, appliances, brands, residential and commercial scope")
    ]
  },
  {
    "id": "beyer-appliance-service",
    "name": "Beyer Appliance Service",
    "slug": "beyer-appliance-service",
    "citySlug": "phoenix",
    "phone": "4806591400",
    "phoneDisplay": "(480) 659-1400",
    "website": "https://beyerapplianceservice.com/",
    "email": "dispatch@beyerapplianceservice.com",
    "address": {"street": "2400 W Southern Ave #101", "city": "Tempe", "state": "AZ", "zip": "85282"},
    "serviceAreas": ["Tempe", "Mesa", "Chandler", "Scottsdale", "Gilbert"],
    "appliances": ["refrigerator", "washer", "dryer", "dishwasher", "oven-range"],
    "brands": [],
    "brandsNote": None,
    "hours": "Monday, Tuesday, Thursday, Friday 8:00 a.m.–5:00 p.m.; Wednesday 9:00 a.m.–5:00 p.m.; Saturday–Sunday closed.",
    "flags": [],
    "license": "ROC #342422 (listed on the company website)",
    "facts": [
      "The company website says Beyer Appliance Service has been part of the local community since 1992, with a home base in Tempe.",
      "Besides in-home repair, the site advertises a 3,000 sq ft warehouse of refurbished appliances and a parts counter for original and aftermarket parts.",
      "The website says the company offers same-day service.",
      "The website lists ROC #342422."
    ],
    "sources": [
      src("https://beyerapplianceservice.com/", "name, phone, address, email, hours, since 1992, service areas, appliances, used appliances and parts, same-day claim, ROC #342422")
    ]
  },
  {
    "id": "red-and-white-appliance-service",
    "name": "Red & White Appliance Service",
    "slug": "red-and-white-appliance-service",
    "citySlug": "phoenix",
    "phone": "6029388116",
    "phoneDisplay": "(602) 938-8116",
    "website": "https://www.redandwhiteappliance.com/",
    "email": None,
    "address": {"street": None, "city": "Glendale", "state": "AZ", "zip": None},
    "addressNotes": "The company's own homepage did not publish a street address in the version we opened. Public business directories place the shop in Glendale; confirm the address when you call. We did not treat third-party directory addresses as verified.",
    "serviceAreas": ["Valley of the Sun"],
    "appliances": ["refrigerator", "freezer", "ice-maker", "oven-range", "microwave", "washer", "dryer"],
    "brands": [],
    "brandsNote": "The company homepage says it is factory trained and authorized for 18 high-quality brands but does not list the brand names on the page we opened.",
    "hours": None,
    "flags": ["family-owned"],
    "license": None,
    "facts": [
      "The company website says it is family owned and operated since 1995.",
      "The homepage says technicians service ranges, ovens, microwaves, ventilation, refrigeration, laundry, and outdoor kitchen appliances, including refrigerators, freezers, ice machines, and wine coolers (under-counter and full size).",
      "The website states that the company provides a one-year parts and labor warranty."
    ],
    "sources": [
      src("https://www.redandwhiteappliance.com/", "name, phone, family owned since 1995, Valley of the Sun, appliance types, 18-brand authorized claim without a named list, one-year parts and labor warranty")
    ]
  },
  {
    "id": "appliance-works",
    "name": "Appliance Works",
    "slug": "appliance-works",
    "citySlug": "phoenix",
    "phone": "6028007468",
    "phoneDisplay": "(602) 800-7468",
    "website": "https://applianceworksaz.com/",
    "email": None,
    "address": {"street": "9605 N Cave Creek Rd", "city": "Phoenix", "state": "AZ", "zip": "85020"},
    "addressNotes": "The website also lists a West Valley office at 12630 N 103rd Ave #115, Sun City, AZ 85351, and a Cave Creek/Carefree office at 37608 N Cave Creek Rd #201, Cave Creek, AZ 85331, plus offices in Tucson, Casa Grande, and Prescott. Phoenix Valley phone is (602) 800-7468; Cave Creek/Carefree is listed as (480) 795-7240.",
    "serviceAreas": ["Phoenix", "Peoria", "Goodyear", "Cave Creek", "Gilbert", "Scottsdale", "Fountain Hills", "Sun City"],
    "appliances": ["refrigerator", "washer", "dryer", "dishwasher", "oven-range", "microwave"],
    "brands": ["Samsung", "GE", "LG", "Whirlpool", "Maytag", "Kenmore", "Sub-Zero", "True"],
    "brandsNote": "Brand names above appeared in recent-job examples on the company homepage we opened, not as a complete official brand list.",
    "hours": None,
    "flags": ["locally-owned"],
    "license": "ROC #323128 (listed on the company website)",
    "facts": [
      "The company describes itself as a local Arizona appliance repair company and lists multiple Arizona offices (Phoenix Valley, Cave Creek/Carefree, West Valley/Sun City, Northern Tucson, Casa Grande/Maricopa, and Prescott).",
      "The website lists Arizona Registrar of Contractors number 323128.",
      "This is a multi-office Arizona company, not a national franchise. Confirm which office and technician will handle a Phoenix-metro job when you call."
    ],
    "sources": [
      src("https://applianceworksaz.com/", "name, Phoenix Valley phone, main office address, other Arizona offices and phones, ROC #323128, local Arizona company positioning, appliance types and brands seen in homepage job examples")
    ]
  },
  {
    "id": "lux-appliance-care",
    "name": "Lux Appliance Care",
    "slug": "lux-appliance-care",
    "citySlug": "phoenix",
    "phone": "6028949472",
    "phoneDisplay": "(602) 894-9472",
    "website": "https://luxappliancecare.com/",
    "email": "contact@luxappliancecare.com",
    "address": {"street": None, "city": "Phoenix", "state": "AZ", "zip": None},
    "serviceAreas": ["Phoenix", "Scottsdale", "Paradise Valley", "Glendale", "Mesa", "Chandler", "Peoria", "Cave Creek", "Fountain Hills", "Queen Creek", "Sun City", "Tempe", "Gilbert", "Apache Junction", "Tolleson", "San Tan Valley"],
    "appliances": ["refrigerator", "freezer", "ice-maker", "oven-range", "microwave", "washer", "dryer", "dishwasher"],
    "brands": ["Sub-Zero", "Wolf", "Viking", "Thermador", "KitchenAid"],
    "brandsNote": "The about page says technicians have deep expertise in Sub-Zero, Wolf, Viking, Thermador, KitchenAid, and beyond. The homepage also says 'all major brands.'",
    "hours": "Monday–Friday 8:00 a.m.–6:00 p.m.; Saturday–Sunday 9:00 a.m.–6:00 p.m.",
    "flags": ["family-owned", "locally-owned"],
    "license": None,
    "facts": [
      "The about page says the company was founded in 2021 as a small, family-owned business by Eli Sabayev, and describes itself as a proud Phoenix-based, locally owned and operated company.",
      "The homepage says the company strives to offer same-day service based on availability.",
      "The site says a service call fee is charged and is applied to the repair cost if you proceed.",
      "The site also lists outdoor appliances (grills, outdoor refrigeration) and wine coolers."
    ],
    "sources": [
      src("https://luxappliancecare.com/", "name, phone, hours, appliances, service cities, same-day availability claim, service-call fee policy"),
      src("https://luxappliancecare.com/about-us", "founded 2021, family-owned, founder Eli Sabayev, locally owned claim, email, brands including Sub-Zero, Wolf, Viking, Thermador, KitchenAid")
    ]
  },
  {
    "id": "a-and-d-appliance-repair",
    "name": "A & D Appliance Repair",
    "slug": "a-and-d-appliance-repair",
    "citySlug": "phoenix",
    "phone": "4808182052",
    "phoneDisplay": "(480) 818-2052",
    "website": "https://ad-appliance.com/",
    "email": None,
    "address": {"street": None, "city": "Mesa", "state": "AZ", "zip": None},
    "addressNotes": "The homepage we opened did not publish a street address. The company describes itself as an East Valley shop; we used Mesa only as a representative East Valley city for local-business markup, not as a verified street location. Confirm the service area when you call or text.",
    "serviceAreas": ["Mesa", "Tempe", "Chandler", "Gilbert", "Queen Creek", "San Tan Valley", "Scottsdale", "Ahwatukee"],
    "appliances": ["washer", "dryer", "oven-range", "dishwasher", "refrigerator", "ice-maker"],
    "brands": ["Admiral", "Amana", "Electrolux", "Frigidaire", "GE", "Hotpoint", "Jenn-Air", "Kenmore", "KitchenAid", "LG", "Maytag", "Samsung", "Whirlpool"],
    "brandsNote": "Brand list taken from the company homepage.",
    "hours": None,
    "flags": ["family-owned"],
    "license": None,
    "facts": [
      "The company describes itself as family-owned and operated, with 30+ years of experience.",
      "The homepage says the company serves homeowners, property managers, and home warranty companies, and that it uses factory-authorized parts.",
      "The site invites customers to call or text (480) 818-2052."
    ],
    "sources": [
      src("https://ad-appliance.com/", "name, phone, family-owned claim, 30+ years experience, East Valley service cities, appliances, brands")
    ]
  },
  {
    "id": "appliance-care-and-repair",
    "name": "Appliance Care & Repair",
    "slug": "appliance-care-and-repair",
    "citySlug": "phoenix",
    "phone": "4804669606",
    "phoneDisplay": "(480) 466-9606",
    "website": "https://www.appliancecareandrepair.com/",
    "email": None,
    "address": {"street": "1526 W Windsor Ave", "city": "Phoenix", "state": "AZ", "zip": "85007"},
    "addressNotes": "The website also lists a Mesa address: 3707 E Southern Ave Ste 1049, Mesa, AZ 85206.",
    "serviceAreas": ["Phoenix", "Scottsdale", "Queen Creek", "Mesa", "Chandler", "Gilbert", "Tempe", "Glendale", "Peoria", "Surprise", "Avondale", "Goodyear", "Buckeye", "Cave Creek", "Fountain Hills", "Sun City", "Paradise Valley", "Tolleson", "Apache Junction", "San Tan Valley", "Litchfield Park", "Ahwatukee"],
    "appliances": ["refrigerator", "microwave", "washer", "dryer", "oven-range", "dishwasher", "ice-maker"],
    "brands": ["GE", "Samsung", "Kenmore", "Whirlpool"],
    "brandsNote": "The website says technicians are familiar with most every popular brand and specifically mentions GE, Samsung, Kenmore, and Whirlpool as commonly stocked or serviced brands. It does not publish a complete brand list on the page we opened.",
    "hours": "Monday–Friday 7:00 a.m.–6:00 p.m.; Saturday 8:00 a.m.–2:00 p.m.; Sunday closed.",
    "flags": ["family-owned"],
    "license": None,
    "facts": [
      "The company describes itself as family-owned and operated. The site says the company has been tackling appliance repair in Phoenix, Scottsdale, and surrounding areas since 2021, and refers to over 20 years of appliance repair experience.",
      "The website says work comes with a 1-year warranty on labor and a 'Lifetime Part' warranty for residential services, with stated exclusions (confirm current terms when you call).",
      "The site says the company aims to turn most appointments around in under 72 hours and that trucks are stocked with commonly needed parts."
    ],
    "sources": [
      src("https://www.appliancecareandrepair.com/", "name, phone, Phoenix and Mesa addresses, hours, family-owned claim, since 2021, appliances, example brands, service cities, warranty claims")
    ]
  },
  {
    "id": "scottsdale-refrigeration",
    "name": "Scottsdale Refrigeration",
    "slug": "scottsdale-refrigeration",
    "citySlug": "phoenix",
    "phone": "6232577531",
    "phoneDisplay": "(623) 257-7531",
    "website": "https://scottsdalerefrigeration.com/",
    "email": "service@scottsdalerefrigeration.com",
    "address": {"street": None, "city": "Scottsdale", "state": "AZ", "zip": None},
    "addressNotes": "The homepage we opened did not publish a street address. Confirm the address and dispatch location when you call.",
    "serviceAreas": ["Scottsdale", "Tempe", "Mesa", "Cave Creek", "Carefree", "Paradise Valley", "Fountain Hills", "Phoenix"],
    "appliances": ["refrigerator", "freezer", "ice-maker", "dishwasher", "oven-range", "microwave", "washer", "dryer"],
    "brands": ["U-Line", "Marvel", "Asko", "Summit", "Scotsman", "CellarPro", "Z-Line", "Hestan", "Zephyr"],
    "brandsNote": "The website says the company services most major brands and all major appliances, and it specifically describes factory-authorized or full-line service for U-Line, Marvel, Asko, Summit, Scotsman, CellarPro, Z-Line, Hestan, and Zephyr.",
    "hours": None,
    "flags": ["family-owned"],
    "license": None,
    "facts": [
      "The company describes itself as a third-generation family-owned and operated appliance repair company, licensed and insured, with a warranty on repairs.",
      "The homepage advertises same-day evening and weekend service at no extra charge.",
      "The site says you can schedule online or by call, text, or email, and asks that you have the model and serial number available when possible."
    ],
    "sources": [
      src("https://scottsdalerefrigeration.com/", "name, phone, email, family-owned third-generation claim, service areas, appliances, specialty brands, same-day evening/weekend claim")
    ]
  },
  {
    "id": "anderson-appliance",
    "name": "Anderson Appliance LLC",
    "slug": "anderson-appliance",
    "citySlug": "phoenix",
    "phone": "4804228495",
    "phoneDisplay": "(480) 422-8495",
    "website": "https://andersonappliancellc.com/",
    "email": "Info@AndersonAppliancellc.com",
    "address": {"street": None, "city": "Scottsdale", "state": "AZ", "zip": None},
    "addressNotes": "The pages we opened describe the company as a Scottsdale, Arizona residential appliance provider but did not publish a street address.",
    "serviceAreas": ["Scottsdale", "Phoenix"],
    "appliances": ["refrigerator", "oven-range", "microwave", "dishwasher", "washer", "dryer", "ice-maker"],
    "brands": ["Viking", "AGA", "Marvel", "U-Line"],
    "brandsNote": "The website says Anderson Appliance Service is a Viking Platinum Preferred Service Company and provides authorized factory service for AGA, Marvel, and U-Line, and that it also services most other major brands.",
    "hours": None,
    "flags": ["owner-operated"],
    "license": None,
    "facts": [
      "The website names Steve Anderson as owner-operator. It says the business moved to Phoenix, AZ in 1996 and focuses on luxury residential appliance repair, including premium refrigeration, cooking, wine preservation, and ice making products.",
      "The site says the company provides Viking warranty service throughout the state of Arizona.",
      "The site also says technicians strive to complete repairs in one service call when parts are available on site."
    ],
    "sources": [
      src("https://andersonappliancellc.com/", "name, phone, email, owner-operator Steve Anderson, Phoenix move in 1996, Scottsdale positioning, Viking / AGA / Marvel / U-Line authorization claims, appliances")
    ]
  },
  {
    "id": "kaelric-appliance-solutions",
    "name": "Kaelric Appliance Solutions",
    "slug": "kaelric-appliance-solutions",
    "citySlug": "phoenix",
    "phone": "4805168155",
    "phoneDisplay": "(480) 516-8155",
    "website": "https://www.kappliancesolutions.com/",
    "email": "support@kappliancesolutions.com",
    "address": {"street": None, "city": "Phoenix", "state": "AZ", "zip": None},
    "addressNotes": "The website describes Kaelric as a Phoenix-area company and publishes coverage by ZIP code rather than a public shop street address.",
    "serviceAreas": ["Phoenix", "Scottsdale", "Paradise Valley", "Fountain Hills", "Cave Creek", "Tempe", "Mesa", "Chandler", "Gilbert", "Queen Creek", "San Tan Valley", "Apache Junction", "Peoria", "Goodyear", "Avondale", "Buckeye", "Litchfield Park", "Tolleson", "El Mirage", "Youngtown", "Waddell", "Sun City", "Sun City West"],
    "appliances": ["refrigerator", "freezer", "washer", "dryer", "dishwasher", "oven-range", "ice-maker"],
    "brands": [],
    "brandsNote": None,
    "hours": "Monday–Friday 8:00 a.m.–6:00 p.m. Arizona time.",
    "flags": [],
    "license": None,
    "facts": [
      "The company describes itself as a Phoenix-area company. Coverage is by an approved ZIP-code list, not only by city name; the site says to check a ZIP before scheduling.",
      "The website says the service call fee is waived if you approve and complete a repair; if you decline, only the service call fee applies. The fee amount is given when the company confirms the visit — it is not published as a single number on the homepage we opened.",
      "The site is explicit about work it does not take on: microwaves, garbage disposals, sealed-system or refrigerant work, washer transmissions or bearings, and repairs on double built-in wall ovens.",
      "The site says Carefree, Coolidge, Maricopa, Rio Verde, Wickenburg, and Wittmann are outside the current service area."
    ],
    "sources": [
      src("https://www.kappliancesolutions.com/", "name, phone, email, hours, Phoenix-area positioning, appliances, service-call fee policy, work the company does not take on"),
      src("https://www.kappliancesolutions.com/service-areas", "city and ZIP coverage list, cities currently outside the area")
    ]
  },
  {
    "id": "jerrys-affordable-appliance-repair",
    "name": "Jerry's Affordable Appliance Repair",
    "slug": "jerrys-affordable-appliance-repair",
    "citySlug": "phoenix",
    "phone": "4807706885",
    "phoneDisplay": "(480) 770-6885",
    "website": "https://jerrysaffordableappliancerepair.com/",
    "email": None,
    "address": {"street": None, "city": "Mesa", "state": "AZ", "zip": "85212"},
    "serviceAreas": ["Mesa", "Gold Canyon", "Tolleson"],
    "appliances": ["microwave", "refrigerator", "dryer", "dishwasher", "washer", "oven-range"],
    "brands": [],
    "brandsNote": "The website says the owner can repair virtually any major appliance and does not publish a brand-by-brand list on the pages we opened.",
    "hours": "Monday–Friday 7:00 a.m.–6:00 p.m.; Saturday 7:00 a.m.–12:00 p.m. by appointment; Sunday closed.",
    "flags": ["owner-operated"],
    "license": None,
    "facts": [
      "The about page says the company is solely owned and operated by Jerry, opened in 2016, and that he has more than 30 years of experience in the trade.",
      "The homepage describes the business as a one-man company based in Mesa, AZ 85212, and says it serves a 30-mile radius. The only additional cities named on the homepage we opened are Gold Canyon and Tolleson; confirm whether your address is in range.",
      "The website says the business is fully licensed and insured, and that it offers free estimates for potential clients."
    ],
    "sources": [
      src("https://jerrysaffordableappliancerepair.com/", "name, phone, Mesa 85212, hours, one-man-show description, appliances, 30-mile radius, Gold Canyon and Tolleson"),
      src("https://jerrysaffordableappliancerepair.com/about-us/", "solely owned and operated, opened 2016, 30 years of experience, licensed and insured claim, free estimates")
    ]
  },
  {
    "id": "elite-sub-zero-appliance-repair",
    "name": "Elite Sub-Zero Appliance Repair",
    "slug": "elite-sub-zero-appliance-repair",
    "citySlug": "phoenix",
    "phone": "6027800903",
    "phoneDisplay": "(602) 780-0903",
    "website": "https://www.subzerorepairtempe.com/about/",
    "email": None,
    "address": {"street": None, "city": "Tempe", "state": "AZ", "zip": None},
    "addressNotes": "The about page we opened did not publish a street address. The site's domain and copy emphasize Tempe and the Phoenix metro; confirm the dispatch location when you call.",
    "serviceAreas": ["Phoenix", "Tempe", "Scottsdale", "Paradise Valley", "Chandler"],
    "appliances": ["refrigerator", "oven-range", "dishwasher"],
    "brands": ["Sub-Zero", "Wolf", "Thermador", "Viking", "Miele", "Gaggenau"],
    "brandsNote": "The about page says the company specializes exclusively in luxury brands such as Sub-Zero, Wolf, Thermador, Viking, Miele, Gaggenau, and other high-end brands, and that it is not affiliated with any manufacturer.",
    "hours": "Monday–Saturday 7:00 a.m.–8:00 p.m.; Sunday 9:00 a.m.–5:00 p.m.",
    "flags": ["independent-specialist"],
    "license": "The about page says the company is registered with the Arizona Registrar of Contractors but does not publish the license number on that page.",
    "facts": [
      "The about page says the company has been serving the Phoenix metro area for over 15 years and specializes exclusively in premium / luxury brands.",
      "The company states it is not affiliated with any manufacturer — it is an independent specialist.",
      "The page says the company is Arizona ROC licensed, fully insured, and EPA 608 certified, and that repairs are backed by a 90-day warranty on parts and labor (confirm current terms when you call).",
      "The page advertises same-day service throughout the Phoenix metro area."
    ],
    "sources": [
      src("https://www.subzerorepairtempe.com/about/", "name, phone, hours, luxury-brand specialty, independence claim, service cities named, ROC/insured/EPA 608 claims, 90-day warranty, same-day claim")
    ]
  },
  {
    "id": "united-appliances-and-air",
    "name": "United Appliances & Air",
    "slug": "united-appliances-and-air",
    "citySlug": "phoenix",
    "phone": "6027546303",
    "phoneDisplay": "(602) 754-6303",
    "website": "https://unitedapplianceandair.com/",
    "email": "unitedappliancesandair@gmail.com",
    "address": {"street": "4722 E Bell Rd", "city": "Phoenix", "state": "AZ", "zip": "85032"},
    "serviceAreas": ["Phoenix", "Scottsdale", "Goodyear", "Mesa", "Buckeye", "Paradise Valley", "Surprise", "Tolleson", "Waddell", "Chandler", "Gilbert", "Litchfield Park", "Peoria", "Glendale", "El Mirage", "Cave Creek", "Sun City", "Sun City West", "Ahwatukee"],
    "appliances": ["refrigerator", "freezer", "ice-maker", "oven-range", "dishwasher", "washer", "dryer"],
    "brands": [],
    "brandsNote": None,
    "hours": "The website lists hours as 24/7, every day of the week.",
    "flags": ["locally-owned"],
    "license": "ROC #348336 (listed on the company website). Legal name listed as United Appliances And Air LLC.",
    "facts": [
      "The company describes itself as a local Arizona appliance repair and HVAC/refrigeration contractor, licensed, bonded, and insured, ROC #348336.",
      "In addition to household appliances, the site lists commercial refrigeration (walk-in coolers and freezers, prep-table coolers, kegerators, and similar equipment) and HVAC installation and repair.",
      "Confirm whether a given appointment is for appliance repair or HVAC when you call."
    ],
    "sources": [
      src("https://unitedapplianceandair.com/", "name, legal name, phone, email, address, 24/7 hours claim, ROC #348336, appliances and HVAC scope, service cities")
    ]
  },
  {
    "id": "az-major-appliance",
    "name": "AZ Major Appliance Repair LLC",
    "slug": "az-major-appliance",
    "citySlug": "phoenix",
    "phone": "4802558780",
    "phoneDisplay": "(480) 255-8780",
    "website": "https://azmajor.com/",
    "email": None,
    "address": {"street": None, "city": "Gilbert", "state": "AZ", "zip": None},
    "addressNotes": "The homepage we opened says the company is based in Gilbert, Arizona, but did not publish a street address.",
    "serviceAreas": ["Gilbert", "Queen Creek", "San Tan Valley", "Chandler", "Tempe", "Ahwatukee", "Mesa", "Apache Junction", "Scottsdale", "Fountain Hills"],
    "appliances": ["refrigerator", "dishwasher", "washer", "dryer", "microwave", "oven-range"],
    "brands": [],
    "brandsNote": "The website says technicians are experienced with most major appliance brands and that the company services all major household appliance brands.",
    "hours": "The website says the company operates primarily Monday through Friday, 9:00 a.m.–4:00 p.m., by appointment.",
    "flags": ["family-owned"],
    "license": None,
    "facts": [
      "The company describes itself as family-owned and family-run, based in Gilbert, Arizona.",
      "The website lists a $100 service call, which it says applies toward the cost of necessary repairs and parts (accessed 2026-11-18; confirm when you call).",
      "The site says the company accepts debit, credit, and Venmo."
    ],
    "sources": [
      src("https://azmajor.com/", "name, phone, Gilbert base, family-owned claim, service cities, appliances, hours, $100 service call policy")
    ]
  },
  {
    "id": "hometech-appliance-repair",
    "name": "Hometech Appliance Repair",
    "slug": "hometech-appliance-repair",
    "citySlug": "phoenix",
    "phone": "6024861901",
    "phoneDisplay": "(602) 486-1901",
    "website": "https://hometechappliancerepair.com/about/",
    "email": None,
    "address": {"street": "451 W Ranch Rd", "city": "Chandler", "state": "AZ", "zip": "85225"},
    "serviceAreas": ["Chandler", "Gilbert", "Mesa", "Tempe", "Scottsdale", "Queen Creek", "Ahwatukee", "Phoenix", "Glendale", "Fountain Hills", "Cave Creek"],
    "appliances": ["refrigerator", "freezer", "ice-maker", "washer", "dryer", "dishwasher", "oven-range"],
    "brands": [],
    "brandsNote": "The site footer says 'Independent service. Brand names do not imply factory authorization.' The about page we opened does not publish a complete brand list.",
    "hours": "Monday–Saturday 8:00 a.m.–8:00 p.m.; Sunday: emergencies only.",
    "flags": ["owner-operated", "locally-owned"],
    "license": None,
    "facts": [
      "The about page says Hometech Appliance Repair LLC is a small, owner-operated company based in Chandler, Arizona, founded by Joe, who has more than 20 years in appliance repair.",
      "The page says you get the same person from the first call to the finished repair.",
      "Besides household appliances, the site also lists water heaters, walk-in coolers and freezers, ice machines, commercial equipment, and heating and cooling. Confirm the type of job when you call or book.",
      "The footer on the about page, which the site marked as updated November 7, 2026, states that brand names do not imply factory authorization."
    ],
    "sources": [
      src("https://hometechappliancerepair.com/about/", "name, owner-operated claim, founder Joe, 20+ years, address, phone, hours, service cities, appliance types, independent-service footer note, page updated November 7, 2026")
    ]
  },
  {
    "id": "all-city-appliance-repair",
    "name": "All City Appliance Repair",
    "slug": "all-city-appliance-repair",
    "citySlug": "phoenix",
    "phone": "4802438003",
    "phoneDisplay": "(480) 243-8003",
    "website": "https://www.allcityappliancerepairservice.com/",
    "email": None,
    "address": {"street": None, "city": "Scottsdale", "state": "AZ", "zip": None},
    "addressNotes": "The homepage we opened positions the company as a Scottsdale-area service and did not publish a street address or hours.",
    "serviceAreas": ["Scottsdale", "Tempe", "Mesa", "Chandler", "Phoenix", "Glendale", "Gilbert"],
    "appliances": ["refrigerator", "washer", "dryer", "dishwasher", "oven-range"],
    "brands": ["Amana", "Bosch", "Gibson", "GE", "Samsung", "Whirlpool", "Kenmore", "LG", "KitchenAid", "Maytag", "Frigidaire", "Sub-Zero"],
    "brandsNote": "Brand list taken from the company homepage, which also says to call if your brand is not listed.",
    "hours": None,
    "flags": [],
    "license": None,
    "facts": [
      "The homepage says the company provides appliance repair and maintenance in the Scottsdale, Tempe, Mesa, Chandler, Phoenix, and Glendale area, and later also names Gilbert.",
      "The website says the service call is always free with the repair, and that most service calls receive same-day service.",
      "The pages we opened did not state whether the company is owner-operated or family-owned, so we do not make that claim."
    ],
    "sources": [
      src("https://www.allcityappliancerepairservice.com/", "name, phone, service cities, brands, service-call-free-with-repair claim, same-day claim")
    ]
  },
  {
    "id": "a-quality-refrigeration",
    "name": "A-Quality Refrigeration",
    "slug": "a-quality-refrigeration",
    "citySlug": "phoenix",
    "phone": "4808446144",
    "phoneDisplay": "(480) 844-6144",
    "website": "https://www.aqualityrefrigeration.com/appliances",
    "email": "info@aqualityrefrigeration.com",
    "address": {"street": "835 W. Warner Rd. Ste. 101-625", "city": "Gilbert", "state": "AZ", "zip": "85233"},
    "serviceAreas": ["Mesa", "Tempe", "Chandler", "Gilbert", "Ahwatukee", "Sun Lakes", "South Scottsdale"],
    "appliances": ["washer", "dryer", "oven-range", "refrigerator", "freezer", "ice-maker"],
    "brands": ["Admiral", "Amana", "Bosch", "Caloric", "Crosley", "Electrolux", "Estate", "Frigidaire", "GE", "Hotpoint", "InSinkErator", "Jenn-Air", "Kenmore", "Kirkland", "KitchenAid", "LG", "Magic Chef", "Maytag", "Norge", "Roper", "Samsung", "Sub-Zero", "Tappan", "Westinghouse", "Whirlpool"],
    "brandsNote": "Brand list taken from the company's appliances page.",
    "hours": "Monday–Friday 8:00 a.m.–5:00 p.m.; Saturday emergency repairs only upon availability; Sunday closed.",
    "flags": [],
    "license": None,
    "facts": [
      "Legal name on the appliances page is A-Quality Refrigeration, Inc., with a Gilbert mailing/suite address.",
      "The company also advertises HVAC service. The appliances page lists washers, dryers, ovens and cooktops, range hoods, refrigerators and freezers, garbage disposals, ice makers, and water heaters.",
      "The page says technicians carry a large inventory of parts and can complete most repairs in one trip.",
      "The page mentions a $79 preventative dryer-maintenance special (accessed 2026-11-18; confirm current pricing when you call).",
      "The pages we opened did not use the words 'family-owned' or 'owner-operated,' so we do not make that claim."
    ],
    "sources": [
      src("https://www.aqualityrefrigeration.com/appliances", "name, legal name, phone, email, address, hours, Southeast Valley cities and ZIP list, appliances, brands, one-trip parts claim, $79 dryer maintenance special")
    ]
  }
]

def main():
    out = Path("/workspace/site/data/listings.json")
    # sanity
    ids = [l["id"] for l in listings]
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert len(listings) == 21, len(listings)
    for l in listings:
        assert l["phone"].isdigit()
        assert l["website"].startswith("http")
        assert l["sources"]
        assert l["citySlug"] == "phoenix"
    out.write_text(json.dumps(listings, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(listings)} listings to {out}")

if __name__ == "__main__":
    main()
