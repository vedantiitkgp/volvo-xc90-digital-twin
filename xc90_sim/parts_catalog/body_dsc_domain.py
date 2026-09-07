"""
Real Volvo OEM parts researched for the body electronics/DSC domain. See
xc90_sim/parts_catalog/README.md (if present) or STATUS.md for the overall
catalog's scope and honesty rules: a part number here is either here is either a real, source-verified number, exactly the string
"NOT_FOUND" (search didn't confirm one), or exactly the string
"NOT_APPLICABLE" (the real part doesn't exist for this component) --
never a plausible-looking guess.

Car modeled: 2016 Volvo XC90 T6 Momentum AWD, VIN YV4A22PKXG1092057 (second-
generation/SPA-platform XC90, NOT the 2003-2014 first-generation XC90).

IMPORTANT caveat that came up repeatedly during this research: usparts.
volvocars.com and other retailers list plenty of "Volvo XC90" part numbers
that are actually first-generation-only (2003-2014/2015) parts -- these
often show up high in search results because the query "Volvo XC90 <part>"
matches both generations, and the URL slugs frequently don't distinguish
year. Numbers explicitly confirmed fitting a 2016 (or a 2016-inclusive
range) second-gen chassis are recorded as verified; numbers that only
turned up confirmed for 2003-2015 were treated as wrong-generation and
recorded NOT_FOUND rather than reused. Several second-gen parts also have
mid-production-run chassis breakpoints (Volvo's "CH ######" running
changes) that can fall within a single model year -- noted where found.
"""

PARTS = {
    "Horn": {
        "sim_class": "xc90_sim.body.Horn",
        "real_parts": [
            {
                "name": "Horn, low tone (left)",
                "oem_part_number": "31662951",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Horn-Left/71859182/31662951.html",
                "notes": (
                    "Real 2016+ XC90s use a dual-tone horn setup (two physical horns, "
                    "not one) -- this sim's single Horn class maps to BOTH of these "
                    "real parts. Genuine Volvo catalog lists this fitting XC90. Note: "
                    "a later running-change part (32328569, also listed 'Horn (Left)') "
                    "also appears for XC90 2016-2027 -- there may be more than one valid "
                    "SKU across this car's production run; 31662951 is the one this "
                    "search could confirm most directly tied to an XC90 fitment listing."
                ),
            },
            {
                "name": "Horn, high frequency (right)",
                "oem_part_number": "31693611",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Horn-Right/71860042/31693611.html",
                "notes": (
                    "Second horn of the dual-tone pair. A later running-change part "
                    "(32328568) also turns up for the same position across several "
                    "Volvo SPA-platform models -- same running-change caveat as the "
                    "left horn above."
                ),
            },
        ],
    },
    "Ignition": {
        "sim_class": "xc90_sim.body.Ignition",
        "real_parts": [
            {
                "name": "Rotary Start/Stop knob switch assembly",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Candidate 31443818 ('Start/Stop button') is widely resold on eBay "
                    "as fitting XC90/XC60/S90/V90/S60 2016-2021, but Volvo's own genuine "
                    "parts catalog (usparts.volvocars.com) lists 31443818 specifically as "
                    "a Volvo XC60 'Switch Panel', not an XC90 part -- could not confirm "
                    "genuine XC90 fitment for that number. The other number found, "
                    "8650054 ('Ignition Switch/Starter Switch'), is confirmed fitting "
                    "the FIRST-GENERATION XC90 (2003-2015) -- wrong generation for this "
                    "2016 car's rotary knob (which is a completely different mechanism "
                    "than the old key-barrel ignition switch). No source-verified real "
                    "part number found for the actual 2016 second-gen rotary knob "
                    "assembly."
                ),
            },
        ],
    },
    "Closures": {
        "sim_class": "xc90_sim.body.Closures",
        "real_parts": [
            {
                "name": "Door lock actuator motor (left front)",
                "oem_part_number": "32205954",
                "source_url": "https://www.volvopartswebstore.com/products/volvo/XC90/Door-Lock-Actuator-Motor-Left--Front/12877914/32205954.html",
                "notes": "One of 4 door lock actuators (one per door) this sim's Closures.locked/door_open models collectively.",
            },
            {
                "name": "Door lock actuator motor (left rear)",
                "oem_part_number": "31322586",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Door-Lock-Actuator-Motor-Left--Rear/97579911/31322586.html",
                "notes": "Confirmed on a 2016-XC90-specific usparts.volvocars.com listing.",
            },
            {
                "name": "Door lock actuator motor (right rear)",
                "oem_part_number": "31322589",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Door-Lock-Actuator-Motor-Right--Rear/97579879/31322589.html",
                "notes": None,
            },
            {
                "name": "Door lock actuator motor (right front)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": "Left-front, left-rear, and right-rear actuators were each found individually; a distinct right-front-specific listing was not located in this search pass.",
            },
            {
                "name": "Hood latch",
                "oem_part_number": "32226109",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Hood-Latch/71859483/32226109.html",
                "notes": "Confirmed fitting XC90 2016-2025+ across multiple retailers (Volvo Parts Webstore, FCP Euro, TascaParts), including a 2016-XC90-specific usparts.volvocars.com page.",
            },
            {
                "name": "Power tailgate lift motor (variant code L704)",
                "oem_part_number": "31690604",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Tailgate-Lift-Motor/73146870/31690604.html",
                "notes": "Confirmed fitting XC90 2016-2027. Real power tailgates use two lift motors/struts (left+right); this is one of the pair.",
            },
            {
                "name": "Power tailgate lift motor (variant code L702)",
                "oem_part_number": "31690603",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2017_XC90/Tailgate-Lift-Motor/73146955/31690603.html",
                "notes": "The other lift motor of the pair; confirmed on a 2017-XC90-specific listing (adjacent model year, same generation/platform as this 2016 car).",
            },
        ],
    },
    "Lighting": {
        "sim_class": "xc90_sim.body.Lighting",
        "real_parts": [
            {
                "name": "Headlight assembly, LED, composite (left)",
                "oem_part_number": "31677036",
                "source_url": "https://www.volvocarsoempartsdirect.com/oem-parts/volvo-2016-2018-volvo-xc90-headlamp-assembly-left-31677036",
                "notes": (
                    "Confirmed 2016-2018 XC90, LED, code JB05, for chassis up to 344889 "
                    "(from chassis 105098). Volvo made a running change partway through "
                    "this generation's production -- earlier-built cars (before chassis "
                    "105097) need drive units 31446806 + 31468410 replaced alongside it. "
                    "This project has separately confirmed this car has LED headlights; "
                    "which exact chassis-break variant this specific VIN needs isn't "
                    "independently verified here."
                ),
            },
            {
                "name": "Headlight assembly, LED, composite (right)",
                "oem_part_number": "31655784",
                "source_url": "https://www.volvopartscounter.com/oem-parts/volvo-composite-headlamp-31655784",
                "notes": (
                    "Listed fitting XC90 2016-2021, LED, code JB09, from chassis 344890. "
                    "A further running-change part (31655719) shows up for 2020-2025 "
                    "specifically -- there appear to be at least two production breaks "
                    "across this generation's headlight part numbers; not fully "
                    "untangled here, but 31655784 is the one confirmed to include 2016."
                ),
            },
            {
                "name": "Turn signal / indicator light, right",
                "oem_part_number": "31385686",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Turn-Signal-Light-Right-TURN-INDICATOR/65229908/31385686.html",
                "notes": "Confirmed fitting XC90 2016-2027. This is a body-mounted turn indicator (not integrated into the headlight housing or mirror per this listing).",
            },
            {
                "name": "Turn signal / indicator light, left",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": "Only the right-side part number turned up in this search pass; a left-side counterpart almost certainly exists but wasn't independently confirmed.",
            },
            {
                "name": "Fog light",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Candidates found (8693008, 31213647, 8693010) are all REAR fog "
                    "light parts with 'CH -327999'/'CH 328000-' chassis breakpoints "
                    "consistent with the FIRST-GENERATION XC90 (2003-2014), not this "
                    "2016 second-gen car (whose fog lights are integrated into the "
                    "front bumper, not a separate rear housing). No verified front fog "
                    "light part number found for the second-gen XC90."
                ),
            },
            {
                "name": "Dome light / interior roof lamp",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "One candidate (31457644) is advertised on Amazon as fitting XC90 "
                    "2016-2022, but this could not be cross-confirmed on "
                    "usparts.volvocars.com, FCP Euro, or another dealer-parts catalog, "
                    "so it doesn't meet this project's verification bar -- recorded "
                    "NOT_FOUND rather than treated as confirmed."
                ),
            },
        ],
    },
    "Sunroof": {
        "sim_class": "xc90_sim.body.Sunroof",
        "real_parts": [
            {
                "name": "Panoramic sunroof glass/shade motor",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "The only sunroof motor number found with an explicit fitment note "
                    "(30716707, 'Sunroof Motor. ELECTRICAL MOTOR') is confirmed for "
                    "XC90 2003-2014 -- first generation, wrong car. A second candidate "
                    "(31395517, same description text) turned up but without a "
                    "confirmed year range in this search pass, so it isn't recorded as "
                    "verified. No source-verified second-gen (2016+) sunroof motor part "
                    "number found."
                ),
            },
        ],
    },
    "Mirrors": {
        "sim_class": "xc90_sim.body.Mirrors",
        "real_parts": [
            {
                "name": "Power door mirror assembly, heated (left)",
                "oem_part_number": "31402836",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Door-Mirror-Left-REAR-VIEW-MIRROR/65376782/31402836.html",
                "notes": (
                    "Confirmed fitting XC90 2015-2025, includes heating -- matches what "
                    "this project's Mirrors class actually models (folded + heated "
                    "state). Whether this specific assembly also includes an integrated "
                    "turn-signal repeater lens (a common feature on this generation) "
                    "wasn't independently itemized in the listing, and this sim's "
                    "Mirrors class doesn't model a signal function anyway (that's "
                    "Lighting's job), so not claimed here."
                ),
            },
            {
                "name": "Power door mirror assembly, heated (right)",
                "oem_part_number": "31402061",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Door-Mirror-Right/66760938/31402061.html",
                "notes": "Right-side counterpart to the left mirror above; same generation/fitment pattern.",
            },
        ],
    },
    "WasherFluid": {
        "sim_class": "xc90_sim.body.WasherFluid",
        "real_parts": [
            {
                "name": "Washer fluid reservoir (front)",
                "oem_part_number": "31349847",
                "source_url": "https://parts.volvocarsannapolis.com/p/Volvo_2016_XC90/Washer-Fluid-Reservoir-Front/65278425/31349847.html",
                "notes": "Confirmed on a 2016-XC90-specific dealer parts listing; this variant is for vehicles WITHOUT headlight washers.",
            },
            {
                "name": "Windshield washer pump (front)",
                "oem_part_number": "31349390",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Windshield-Washer-Pump-Front-Washer-EquipmentWindshield-Washer-Pump/65210577/31349390.html",
                "notes": "Confirmed fitting XC90 2016-2027.",
            },
        ],
    },
    "Windows": {
        "sim_class": "xc90_sim.body.Windows",
        "real_parts": [
            {
                "name": "Window regulator (left front)",
                "oem_part_number": "31391494",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Window-Regulator-Left--Front-Window-Lift-MechanismWindow-Regulator/65235571/31391494.html",
                "notes": "Confirmed compatible with 2016+ XC90. Front and rear regulators are distinct parts, as expected.",
            },
            {
                "name": "Window regulator (right front)",
                "oem_part_number": "31391495",
                "source_url": "https://parts.volvowinterpark.com/p/Volvo__XC90/Window-Regulator-Right--Front/65235101/31391495.html",
                "notes": "Confirmed compatible with 2016+ XC90.",
            },
            {
                "name": "Window regulator (left rear)",
                "oem_part_number": "31349760",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Window-Regulator-Left--Rear-Window-Lift-Mechanism/65235569/31349760.html",
                "notes": "Confirmed on a 2016-XC90-specific usparts.volvocars.com listing.",
            },
            {
                "name": "Window regulator (right rear)",
                "oem_part_number": "31349761",
                "source_url": "https://www.volvodealerparts.com/oem-parts/volvo-window-regulator-31349761",
                "notes": "Confirmed fitting XC90 2016-2025. (A different number, 31253722, also turned up for this position but is confirmed only for XC90 2003-2015 -- first generation, not used here.)",
            },
        ],
    },
    "Wipers": {
        "sim_class": "xc90_sim.body.Wipers",
        "real_parts": [
            {
                "name": "Front windshield wiper motor",
                "oem_part_number": "31425981",
                "source_url": "https://www.volvopartscounter.com/oem-parts/volvo-windshield-wiper-motor-31425981",
                "notes": (
                    "Confirmed fitting XC90 2016-2024. Note: a different, frequently-"
                    "surfaced number (8693848) is also sold as an 'XC90 windshield "
                    "wiper motor' but its confirmed listings did not specify second-gen "
                    "fitment and its numbering pattern matches this project's other "
                    "confirmed-first-gen-only parts (e.g. the 8638163 rear motor "
                    "below) -- not used here for that reason."
                ),
            },
            {
                "name": "Rear window wiper motor",
                "oem_part_number": "32341523",
                "source_url": "https://www.tascaparts.com/oem-parts/volvo-wiper-motor-32341523",
                "notes": "Confirmed fitting XC90 (and V90/V90 CC) 2016-2025, up to chassis 348732; supersedes earlier part 31349380. (8638163, also sold as an 'XC90 rear wiper motor', is confirmed fitting XC90 2003-2014 only -- first generation, not used here.)",
            },
            {
                "name": "Front wiper blade kit",
                "oem_part_number": "31349377",
                "source_url": "https://www.amazon.com/Genuine-Volvo-31349377-Front-Wiper/dp/B018YAWQ5O",
                "notes": "Genuine Volvo front wiper blade kit, listed for XC90 2016-onward.",
            },
            {
                "name": "Rear wiper blade",
                "oem_part_number": "31349857",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Window-Wiper-Blade-Rear-REAR-WINDOW-WIPER/65453214/31349857.html",
                "notes": "Listing shows chassis ranges (CH -229983, CH -348732) suggesting this part spans multiple running changes/model years including this car's generation.",
            },
        ],
    },
    "ABS": {
        "sim_class": "xc90_sim.dsc.ABS",
        "real_parts": [
            {
                "name": "ABS/ESC hydraulic control unit + control module (combined)",
                "oem_part_number": "31682155",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2020_XC90/ABS-Control-Module/71864740/31682155.html",
                "notes": (
                    "Confirmed via multiple year-specific usparts.volvocars.com listings "
                    "(2017 XC90, 2020 XC90, 2017 V90) spanning this car's 2016-2023 "
                    "second-gen production run. This is a single combined hydraulic "
                    "pump + ECU module (standard on modern cars) that performs BOTH "
                    "ABS and ESC/DSTC functions -- see the ESC entry below, which "
                    "shares this same real part rather than having its own. (Older "
                    "part numbers found, e.g. 30793452/30793454/8671455, are confirmed "
                    "fitting the first-generation XC90/S60/V70/XC70 platform -- not "
                    "used here.)"
                ),
            },
        ],
    },
    "TractionControl": {
        "sim_class": "xc90_sim.dsc.TractionControl",
        "real_parts": [
            {
                "name": "No discrete orderable part -- software function",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "As this project's own module docstring for traction_control.py "
                    "states, TCS on a real modern car is software logic inside the "
                    "same combined ABS/ESC control module (31682155, see ABS above) -- "
                    "it senses wheel speeds over the same CAN broadcasts ABS/ESC use "
                    "and requests a torque-reduction from the engine ECM rather than "
                    "owning any hardware of its own. Not a separate physical part, by "
                    "design, so correctly recorded here as NOT_FOUND rather than "
                    "reusing the ABS/ESC module's part number as if it were a distinct "
                    "TCS-specific part."
                ),
            },
        ],
    },
    "ESC": {
        "sim_class": "xc90_sim.dsc.ESC",
        "real_parts": [
            {
                "name": "ABS/ESC hydraulic control unit + control module (combined) -- same physical part as ABS",
                "oem_part_number": "31682155",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2020_XC90/ABS-Control-Module/71864740/31682155.html",
                "notes": (
                    "Volvo's genuine parts catalog has no separate 'ESC module' or "
                    "'DSTC module' line for this generation distinct from the ABS "
                    "control module -- every hydraulic-unit/control-module listing "
                    "found is labeled as an ABS part, consistent with real modern "
                    "vehicles using one combined ABS+ESC+TCS hydraulic control unit "
                    "(this project's own ESC docstring notes it senses/actuates "
                    "'same as a real module would', over the same bus as ABS/TCS). "
                    "Recorded here as the SAME real part as ABS, not a second one -- "
                    "this sim's ESC/ABS/TractionControl are 3 separate software "
                    "classes mapping to 1 real physical module."
                ),
            },
        ],
    },
}
