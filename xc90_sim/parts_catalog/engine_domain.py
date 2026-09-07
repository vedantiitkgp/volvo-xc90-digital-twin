"""
Real Volvo OEM parts researched for the engine/fuel/exhaust/cooling domain.
See xc90_sim/parts_catalog/README.md (if present) or STATUS.md for the
overall catalog's scope and honesty rules: a part number here is either a
real, source-verified number, exactly the string "NOT_FOUND" (search
didn't confirm one), or exactly the string "NOT_APPLICABLE" (the real
part doesn't exist for this component) -- never a plausible-looking guess.

Vehicle: 2016 Volvo XC90 T6 Momentum AWD, VIN YV4A22PKXG1092057, Drive-E
B4204T9 2.0L twincharged (turbo + supercharger) engine (confirmed real
engine code for this car -- see xc90_sim/specs/cylinder.py's own citation
of mymotorlist.com's B4204T9 spec page, checked 2026-08-22).

Research method: read each sim class's actual code/docstrings to identify
the real physical part(s) it models, then searched for the genuine Volvo
OEM part number for that exact part on this exact engine/trim. Many
individual pages on Volvo's own parts site (usparts.volvocars.com) list a
part number generically under "Volvo XC90" without distinguishing this
2016 second-generation (SPA-platform, Drive-E) XC90 from the older
2003-2015 first-generation XC90 (inline 5/6-cylinder "white block"
engines) -- several candidate numbers turned up during this research were
explicitly for those older/other engines and were REJECTED (not recorded
as the answer) rather than reported as a match. Where that ambiguity could
not be resolved from the search results actually returned, the entry is
NOT_FOUND with a note on what was found and why it was rejected.
"""

PARTS = {
    "Engine": {
        "sim_class": "xc90_sim.engine.Engine",
        "real_parts": [
            {
                "name": "Engine long block / complete engine assembly (Drive-E B4204T9)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Candidates found: 36010442 ('Volvo XC90 Engine Complete') and "
                    "36050975 ('Volvo XC60 Engine Short Block'), neither of which could "
                    "be confirmed as specifically the B4204T9 twincharged variant rather "
                    "than a sibling Drive-E code (B4204T20/T27/T35 etc.) sharing the same "
                    "parts-catalog family. A full engine assembly is too high-stakes/"
                    "variant-specific to report without that confirmation."
                ),
            },
        ],
    },
    "Cylinder": {
        "sim_class": "xc90_sim.engine.cylinder.Cylinder",
        "real_parts": [
            {
                "name": "Piston kit (piston + pin, complete, one per cylinder)",
                "oem_part_number": "32240863",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Engine-Piston-Piston-Kit-Complete-StandardEngine-Piston/97587946/32240863.html",
                "notes": (
                    "Genuine Volvo part, listed for '2016 Volvo XC90' and separately as "
                    "'Volvo XC90 2.0l 4 cylinder Turbo Engine Piston'. Alt/superseded "
                    "number 32213693. The B4204T9 engine code itself wasn't visible in "
                    "the page snippet (Volvo's Drive-E 2.0T family shares this piston "
                    "across several turbo variants/models -- XC40, S80 also listed), so "
                    "this is a good but not 100%-certain match to the T6 twincharged "
                    "code specifically rather than a related turbo-only sibling."
                ),
            },
            {
                "name": "Piston ring set (standalone)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "The one genuine Volvo ring kit found, 31330724, is explicitly listed "
                    "as 'B4204T/B5252S ... without TURBO' -- i.e. the naturally-aspirated "
                    "engine variant, not our twincharged B4204T9 -- so it was rejected. No "
                    "correctly-matched standalone ring set was found (may only be sold "
                    "bundled into the piston kit above)."
                ),
            },
            {
                "name": "Connecting rod",
                "oem_part_number": "31460516",
                "source_url": "https://usparts.volvocars.com/p/Volvo__S60/Engine-Connecting-Rod/65222286/31460516.html",
                "notes": (
                    "RESOLVED 2026-09-01 (previously NOT_FOUND -- 31355860 was correctly "
                    "rejected as an older, wrong-era part). 31460516 is listed directly on "
                    "usparts.volvocars.com (Volvo's own parts site) for 'Volvo S60' with "
                    "'2015-2025' fitment -- the Drive-E era, not overlapping the older "
                    "pre-2015 engine families this project has repeatedly had to exclude "
                    "elsewhere. Lower-than-usual confidence flagged: S60 spans several "
                    "Drive-E engine tunes (T4/T5/T6/T8) across those years and this rod "
                    "wasn't independently confirmed as the B4204T9 twincharged variant "
                    "specifically (connecting rods can differ between tunes of the same "
                    "block under higher peak loads, same reasoning already noted for the "
                    "already-verified rod bearing set above) -- also not independently "
                    "confirmed as sold for XC90 itself vs. only S60 in the listings found."
                ),
            },
            {
                "name": "Connecting rod big-end bearing set",
                "oem_part_number": "31401093",
                "source_url": "https://www.fcpeuro.com/products/volvo-engine-connecting-rod-bearing-kit-pair-genuine-volvo-31401093",
                "notes": (
                    "Genuine Volvo part described as for '2.0L engines with supercharger "
                    "and hybrid applications', fitting XC90/XC60 2015-2021 -- matches the "
                    "twincharged (turbo+supercharger) Drive-E family this engine belongs "
                    "to. A different bearing number, 30777466, also turned up for 'XC90' "
                    "generically but is explicitly for 2.3L-3.2L 5/6-cylinder engines and "
                    "was rejected as the wrong engine family."
                ),
            },
        ],
    },
    "Camshaft": {
        "sim_class": "xc90_sim.engine.camshaft.Camshaft",
        "real_parts": [
            {
                "name": "Intake camshaft",
                "oem_part_number": "32298831",
                "source_url": "https://www.volvopartscounter.com/oem-parts/volvo-intake-camshaft-32298831",
                "notes": (
                    "Described as fitting the SPA-platform 2016-2021 Volvo XC90 2.0L "
                    "4-cylinder gasoline T5/T6 engines specifically, explicitly excluding "
                    "the T8 plug-in-hybrid/mild-hybrid variants -- a good match for this "
                    "non-hybrid T6."
                ),
            },
            {
                "name": "Exhaust camshaft",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Only found a genuine exhaust camshaft (32298649) for 2022-2025 model "
                    "years, not our 2016 model -- likely a different revision/casting -- so "
                    "not recorded as a match. No 2016-specific exhaust camshaft number "
                    "was found."
                ),
            },
        ],
    },
    "Valve": {
        "sim_class": "xc90_sim.engine.valve.Valve",
        "real_parts": [
            {
                "name": "Intake valve",
                "oem_part_number": "31375630",
                "source_url": "https://www.fcpeuro.com/products/volvo-engine-intake-valve-trw-31375630",
                "notes": (
                    "RESOLVED 2026-09-01 (previously NOT_FOUND -- the earlier rejected "
                    "candidate, 9454607, correctly was a different, older CVVT-engine "
                    "part). 31375630 is listed by FCP Euro (TRW-manufactured, a genuine "
                    "OE supplier) explicitly under 'Volvo XC90 Intake Valve Parts', and "
                    "independently cross-referenced by many aftermarket sets naming this "
                    "exact number for the Drive-E 2.0T (B4204T family) engine across S60/"
                    "V60/V90/XC40/XC60/XC90. One source describes it as fitting 'B4204T "
                    "2.0 T4/T5' specifically rather than T6 by name -- moderate rather than "
                    "absolute confidence, since T4/T5/T6 share the same physical block/"
                    "valve architecture (differences are in boost/ECU tuning, not valve "
                    "geometry), but the T6 twincharged variant wasn't named explicitly in "
                    "any source found."
                ),
            },
            {
                "name": "Exhaust valve",
                "oem_part_number": "31375493",
                "source_url": "https://www.fcpeuro.com/Volvo-parts/XC90/Intake-Valve/",
                "notes": (
                    "RESOLVED 2026-09-01 (previously NOT_FOUND -- same rejected-candidate "
                    "situation as the intake valve above, 9454610 was the wrong, older "
                    "CVVT part). 31375493 is the paired exhaust valve to 31375630 above, "
                    "cited identically across the same set of aftermarket cross-references "
                    "explicitly naming Volvo XC90 among the fitting models. Same T4/T5-"
                    "named-not-T6-named confidence caveat as the intake valve."
                ),
            },
        ],
    },
    "Flywheel": {
        "sim_class": "xc90_sim.engine.flywheel.Flywheel",
        "real_parts": [
            {
                "name": "Automatic transmission flexplate (this car has an 8-speed automatic, "
                        "so the real part is a flexplate, not a clutch flywheel)",
                "oem_part_number": "32249215",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Automatic-Transmission-Flexplate/97586513/32249215.html",
                "notes": (
                    "Genuine Volvo part, listed with variant code DF02 and (D104 or D105), "
                    "fitting XC90 2016-2023. Alt/superseded number 31437545."
                ),
            },
        ],
    },
    "TimingBelt": {
        "sim_class": "xc90_sim.engine.timing_belt.TimingBelt",
        "real_parts": [
            {
                "name": "Timing belt kit (belt + tensioner + idler roller)",
                "oem_part_number": "32213096",
                "source_url": "https://www.ipdusa.com/products/22247/1530/2018-Volvo-XC90-T6-Timing-Belt-Kit-20-4cyl-VEA-P3-P5-P6-XC40-S60-V60-XC60-V90-XC90-Genuine-Volvo-32213096",
                "notes": (
                    "RESOLVED 2026-09-01 (previously NOT_FOUND -- the earlier rejection of "
                    "32213096 was itself a mistake: that number is NOT the older Ford-"
                    "derived Duratec/VEP kit, it's the genuine Drive-E VEA 2.0 4-cylinder "
                    "kit). Explicitly listed by ipd (a well-known genuine-Volvo-parts "
                    "retailer) for '2018 Volvo XC90 T6 - Timing Belt Kit, 2.0 4cyl VEA', "
                    "and identically for 2015-2020 XC60 T5/T6 -- same VEA engine family "
                    "this 2016 XC90 T6's B4204T9 belongs to (one shared kit across model "
                    "years/models using this engine, consistent with how Volvo catalogs "
                    "this part elsewhere). A 2016-XC90-specific listing title wasn't the "
                    "one that came back first, but the engine-family match (VEA 2.0 "
                    "4-cylinder T5/T6) is exact and well-corroborated across many ipd "
                    "listings for adjacent model years."
                ),
            },
        ],
    },
    "PCVValve": {
        "sim_class": "xc90_sim.engine.pcv_valve.PCVValve",
        "real_parts": [
            {
                "name": "PCV valve / check valve, crankcase ventilation",
                "oem_part_number": "31430866",
                "source_url": "https://usparts.volvocars.com/p/Volvo__/Check-Valve-Crankcase-Ventilation/65443721/31430866.html",
                "notes": (
                    "RESOLVED 2026-09-01 (previously NOT_FOUND). Genuine Volvo part, "
                    "listed directly on usparts.volvocars.com as 'Check Valve. Crankcase "
                    "Ventilation' -- exactly matches this class's real-world function. "
                    "Independently corroborated identically (same part number, same "
                    "description) across 8+ separate retailers (Tasca, FCP Euro, "
                    "MySwedishParts, VolvoPartsCounter, EuroParts4Less, OEMPartsOnline, "
                    "VolvoDealerParts), all citing '2015-2026 Volvo' fitment -- this is a "
                    "part shared across Volvo's Drive-E engine family rather than one "
                    "specific to a single model/year, which is why fitment isn't narrower "
                    "than that. Distinct from the oil-trap/diaphragm-kit sub-components "
                    "found in the earlier search pass (32140004, 31316184, 31430236, "
                    "31430923, 31670210), which are related but different parts of the "
                    "same crankcase-ventilation system, not the valve itself."
                ),
            },
        ],
    },
    "FuelPump": {
        "sim_class": "xc90_sim.fuel_system.fuel_pump.FuelPump",
        "real_parts": [
            {
                "name": "In-tank electric lift pump",
                "oem_part_number": "32140068",
                "source_url": "https://usparts.volvocars.com",
                "notes": (
                    "Genuine Volvo part described as fitting 2016-2025 XC90, variant code "
                    "G608, steel fuel tank only -- matches this car's configuration. "
                    "(Exact per-product usparts.volvocars.com URL not individually "
                    "captured; found via direct search of usparts.volvocars.com listings.)"
                ),
            },
            {
                "name": "Camshaft-driven high-pressure GDI fuel pump",
                "oem_part_number": "31392104",
                "source_url": "https://www.amazon.com/YABXINHE-Pressure-Compatible-Volvo-31392104/dp/B0D5VVTP4T",
                "notes": (
                    "Lower-confidence than most entries here: this number is cited "
                    "consistently as the genuine-Volvo cross-reference number across "
                    "several aftermarket listings explicitly for 'Volvo ... XC90 T5 T6 "
                    "2.0L L4 Turbo/Supercharged', but was not independently confirmed on "
                    "a first-party Volvo parts site. Recorded because multiple independent "
                    "aftermarket sources agree on it, but flagged for extra scrutiny before "
                    "treating as certain."
                ),
            },
        ],
    },
    "FuelInjector": {
        "sim_class": "xc90_sim.fuel_system.fuel_injector.FuelInjector",
        "real_parts": [
            {
                "name": "Direct (GDI) fuel injector",
                "oem_part_number": "31465787",
                "source_url": "https://www.ipdusa.com/products/56934/1522/2016-Volvo-XC90-T6-Direct-Fuel-Injector-VEA-4-cyl-T6-T8-engines-P3-P5-S60-V60-XC60-XC90-S90-V90-Genuine-Volvo-31465787",
                "notes": (
                    "Genuine Volvo part explicitly listed for the 2016 XC90 T6 (VEA 4-cyl "
                    "T6 & T8 engines). Alt/related numbers 31336653, 31478609, and a "
                    "separate retaining spring clip 31321008 commonly replaced alongside it."
                ),
            },
        ],
    },
    "FuelTank": {
        "sim_class": "xc90_sim.fuel_system.fuel_tank.FuelTank",
        "real_parts": [
            {
                "name": "Fuel tank",
                "oem_part_number": "32325555",
                "source_url": "https://www.volvopartscounter.com/oem-parts/volvo-fuel-tank-32325555",
                "notes": (
                    "Genuine Volvo part for 2016-2025 XC90, explicitly 'compatible with T5 "
                    "and T6 models without plug-in hybrid' -- correctly excludes the T8 "
                    "PHEV's different tank, matching this gas-only T6. A different number, "
                    "31273972 ('80L Fuel Tank'), also turned up for 'XC90' generically but "
                    "its exact year/trim fitment wasn't confirmed, so it's noted here only "
                    "as a secondary, less-certain candidate."
                ),
            },
        ],
    },
    "ExhaustSystem": {
        "sim_class": "xc90_sim.exhaust.exhaust_system.ExhaustSystem",
        "real_parts": [
            {
                "name": "Catalytic converter",
                "oem_part_number": "36010429",
                "source_url": "https://www.volvopartscounter.com/oem-parts/volvo-catalytic-converter-36010429",
                "notes": (
                    "Genuine Volvo part described as fitting 2016-2022 XC90, AWD, "
                    "non-hybrid, variant code GH17 -- matches this car's AWD/non-PHEV "
                    "configuration well. Other candidate codes (36012613, 36013619, "
                    "36012663) exist for other variant codes/years on the same platform; "
                    "the exact match depends on the VIN's specific variant code, which "
                    "wasn't independently cross-checked beyond the 'AWD non-hybrid' "
                    "description, so treat with moderate (not absolute) confidence."
                ),
            },
            {
                "name": "Muffler / rear silencer",
                "oem_part_number": "32252882",
                "source_url": "https://parts.volvocarsofsantamonica.com/p/Volvo__XC90/Muffler-Exhaust-System-Rear/97588821/32252882.html",
                "notes": (
                    "Genuine Volvo part for XC90 2016-2021, not tagged R-Design (unlike "
                    "sibling numbers 30733075/30733164, which are R-Design-specific and "
                    "were rejected as wrong trim), so this is the more plausible fit for "
                    "the base Momentum trim -- but the exact trim tag wasn't independently "
                    "confirmed."
                ),
            },
        ],
    },
    "OxygenSensor": {
        "sim_class": "xc90_sim.exhaust.oxygen_sensor.OxygenSensor",
        "real_parts": [
            {
                "name": "Upstream (pre-catalyst) oxygen/lambda sensor",
                "oem_part_number": "32253664",
                "source_url": "https://www.ipdusa.com/products/23404/Upstream-Oxygen-Sensor-T6-T8-Engines-P5-S90-V90-XC90-to-2017-Genuine-Volvo-32253664",
                "notes": (
                    "Genuine Volvo part explicitly for 'T6 & T8 Engines, P5 XC90/S90/V90, "
                    "to 2017' (variant CC01) -- matches this 2016 model. Note a later "
                    "revision (32253663 / alt 31439480) applies to 2018+ cars instead. "
                    "Alt number for this one: 31380995."
                ),
            },
            {
                "name": "Downstream (post-catalyst) oxygen/lambda sensor",
                "oem_part_number": "31422307",
                "source_url": "https://www.ipdusa.com/products/23397/Downstream-Oxygen-Sensor-P5-XC90-S90-V90-to-2017-Denso-2348010-Volvo-31422307-31480395",
                "notes": "Genuine Volvo part, 'P5 XC90/S90/V90, to 2017' -- matches this 2016 model. Alt number 31480395.",
            },
        ],
    },
    "EGRValve": {
        "sim_class": "xc90_sim.exhaust.egr_valve.EGRValve",
        "real_parts": [
            {
                "name": "EGR valve",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": "https://d2pautoparts.com/products/volvo-egr-valve-d2-d3-d4-oem-36010130",
                "notes": (
                    "CONFIRMED 2026-09-01 (previously flagged as an open question, now "
                    "resolved): the candidate numbers 31439464/36010130 are explicitly "
                    "for the D4204T DIESEL engine family (D2/D3/D4/D5, D4204T4/T14/T23/T2/TX "
                    "variants) across S60/S90/V40/V60/V90/XC40/XC60/XC90 -- confirmed via "
                    "two independent sources (autoparts-24.com's XC90 II listing and "
                    "d2pautoparts.com's D2/D3/D4 listing), neither of which mentions the "
                    "gasoline B4204T9. This gasoline twincharged engine genuinely has NO "
                    "discrete external EGR valve -- Volvo's cataloged EGR valve parts on "
                    "this platform generation are diesel-only. 'NOT_APPLICABLE' rather than "
                    "'NOT_FOUND' because this isn't a failed lookup: the real part doesn't "
                    "exist for this engine. The sim's EGRValve class still models a real "
                    "physical effect (this engine very likely uses INTERNAL EGR via "
                    "camshaft valve-overlap instead, a real, well-documented gasoline-engine "
                    "technique), it just doesn't correspond to one discrete orderable part "
                    "on this specific engine -- see xc90_sim/exhaust/egr_valve.py."
                ),
            },
        ],
    },
    "Turbocharger": {
        "sim_class": "xc90_sim.exhaust.turbocharger.Turbocharger",
        "real_parts": [
            {
                "name": "Turbocharger assembly (exhaust-driven half of the twincharger system; "
                        "the belt-driven supercharger is a separate, un-simulated real part)",
                "oem_part_number": "36012658",
                "source_url": "https://www.fcpeuro.com/products/volvo-turbocharger-genuine-volvo-36012658",
                "notes": (
                    "Genuine Volvo part, BorgWarner-manufactured, described as fitting "
                    "2016-2021 XC90 T6 & T8 (2.0L twincharged VEA engine). Alt number "
                    "31411706."
                ),
            },
        ],
    },
    "CoolingSystem": {
        "sim_class": "xc90_sim.cooling.cooling_system.CoolingSystem",
        "real_parts": [
            {
                "name": "Radiator",
                "oem_part_number": "32224828",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Radiator-Radiator-and-ConnectionsRadiator/73145682/32224828.html",
                "notes": (
                    "RESOLVED 2026-09-01 (previously NOT_FOUND -- the earlier search pass "
                    "only found first-generation-XC90 radiator numbers and correctly "
                    "rejected them, but didn't find the correct second-generation one). "
                    "Genuine Volvo part, listed directly on usparts.volvocars.com for "
                    "'Volvo XC90' with a product family explicitly tagged 'P5 XC90' (P5 is "
                    "Volvo's internal SPA-platform code -- exactly this car's platform, "
                    "confirming this is NOT the first-generation part). Independently "
                    "corroborated across 7+ retailers (Volvo Parts Counter, ipd, Go-Parts, "
                    "eBay, RM European) all citing the same number for '2016-2023/2025/2026 "
                    "XC90' T5/T6/T8, AWD and FWD. Supersedes/cross-references 31338288 and "
                    "the older 8013699. The old, wrong-generation numbers "
                    "(31293550/31305171/36000086/36000464/36002408/8602864/8602866/"
                    "8603427/8603428) remain correctly excluded."
                ),
            },
            {
                "name": "Thermostat (electronically controlled housing assembly)",
                "oem_part_number": "31338532",
                "source_url": "https://www.ipdusa.com/products/20844/Thermostat-Assembly-XC90-T6-Genuine-Volvo-31338532-139397",
                "notes": (
                    "Listed as a genuine Volvo 'Thermostat Assembly - XC90 T6' part, but "
                    "the exact model-year fitment wasn't independently confirmed in the "
                    "source snippet (only 'XC90 T6' generically). A separately-found "
                    "listing explicitly ties the 2016 XC90 T6's VEA 2.0 thermostat "
                    "assembly to part 31686560, but that one is labeled an aftermarket "
                    "(not genuine Volvo) part number -- flagging both here since neither "
                    "was fully cross-confirmed as the one true genuine number for this "
                    "exact model year."
                ),
            },
            {
                "name": "Coolant (water) pump -- electric, Drive-E 2.0",
                "oem_part_number": "32382249",
                "source_url": "https://www.ipdusa.com/products/22029/1522/2016-Volvo-XC90-T8-Electric-Water-Pump-Drive-E-20-Genuine-Volvo-32382249",
                "notes": (
                    "Genuine Volvo electric coolant pump for the Drive-E 2.0 engine; "
                    "confirmed listed identically for the 2016 XC90 T8, 2016 XC60 T6, and "
                    "2022 XC90 T6 (same physical engine architecture across these), which "
                    "gives good confidence it's also correct for this 2016 XC90 T6 even "
                    "though a listing tagged exactly 'XC90 T6 2016' wasn't the one that "
                    "came back first. NOT the separate 'Drive Motor Inverter Cooler Water "
                    "Pump' (31338399), which is an unrelated hybrid-drivetrain part and was "
                    "rejected."
                ),
            },
            {
                "name": "Cooling fan (electric radiator fan assembly)",
                "oem_part_number": "31657772",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Engine-Cooling-Fan/71854649/31657772.html",
                "notes": (
                    "Genuine Volvo part, single fan with brushless motor, explicitly for "
                    "the 2.0L Turbo/Supercharged engine in the 2016-2022 XC90. Alt numbers "
                    "31439756 and 32339486."
                ),
            },
        ],
    },
}
