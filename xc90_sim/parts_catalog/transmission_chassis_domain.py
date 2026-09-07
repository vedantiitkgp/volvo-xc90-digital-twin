"""
Real Volvo OEM parts researched for the transmission/chassis/suspension/
steering domain. See xc90_sim/parts_catalog/README.md (if present) or
STATUS.md for the overall catalog's scope and honesty rules: a part number
here is either a real, source-verified number, exactly the string
"NOT_FOUND" (search didn't confirm one), or exactly the string
"NOT_APPLICABLE" (the real part doesn't exist for this component) --
never a plausible-looking guess.

Scope: 2016 Volvo XC90 T6 Momentum AWD, VIN YV4A22PKXG1092057, Aisin
TG-81SC (marketed AWF8F45) 8-speed automatic.

A recurring, honestly-reported limitation across this file: Volvo's OEM
catalog frequently splits a single conceptual part into multiple
variant-code-specific part numbers (wheel/brake package, active-chassis
vs. standard suspension, region code, etc.). Where a real, catalog-listed
number was found but this specific VIN's exact variant code could not be
independently confirmed from public sources, that is stated explicitly in
`notes` rather than silently picking one option and presenting it as
certain. That is a real-but-unconfirmed-variant caveat, not a fabrication
-- the number itself is real and does apply to *some* 2016 XC90 T6 build.
"""

PARTS = {
    "GearSelector": {
        "sim_class": "xc90_sim.transmission.gear_selector.GearSelector",
        "real_parts": [
            {
                "name": "Gear shift lever knob (PRND selector, passenger compartment)",
                "oem_part_number": "31437262",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Gear-Shift-Lever-Knob-Gear-Selector-Passenger-Compartment/65432141/31437262.html",
                "notes": (
                    "Genuine Volvo part, Volvo's own parts catalog lists this fitting "
                    "2016-2021 XC90. The 2016 XC90 T6 uses a conventional column/console "
                    "floor shift lever (confirmed via SwedeSpeed forum discussion: T6/T5 "
                    "have a traditional shift-through-gate lever; the joystick-style "
                    "shift-by-wire selector is exclusive to T8 hybrid models), so this is "
                    "a genuine mechanical part, not software-only. A second variant-code "
                    "knob (31492640, usparts, fits 2016-2022) also exists -- Volvo splits "
                    "this by trim/interior variant code, and this project could not "
                    "confirm which variant code this specific VIN carries."
                ),
            },
            {
                "name": "Complete gear selector/shifter mechanism assembly (housing, gate, PNP switch linkage -- beyond just the knob)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Still NOT_FOUND as one single 'assembly' part -- see below, though: "
                    "Volvo does sell the real sub-components separately rather than as one "
                    "assembly, which is itself the resolved answer to why no single number "
                    "exists (not a research gap)."
                ),
            },
            {
                "name": "Automatic transmission shift lever (the lever mechanism itself, distinct from the knob above)",
                "oem_part_number": "32324873",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Automatic-Transmission-Shift-Lever/133966147/32324873.html",
                "notes": (
                    "RESOLVED 2026-09-01 (partial -- adds a real sub-component previously "
                    "missing, doesn't replace the still-NOT_FOUND 'one complete assembly' "
                    "entry above). Genuine Volvo part, listed on usparts.volvocars.com for "
                    "'Volvo XC90' as the Automatic Transmission Shift Lever -- confirms "
                    "Volvo sells the lever mechanism and the knob (31437262, above) as "
                    "separate orderable parts, consistent with why one single 'assembly' "
                    "part number doesn't exist."
                ),
            },
            {
                "name": "Automatic transmission shifter cable (connects the lever to the transmission)",
                "oem_part_number": "31492811",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Automatic-Transmission-Shifter-Cable-GEAR-SHIFT-CABLE/71863878/31492811.html",
                "notes": (
                    "RESOLVED 2026-09-01. Genuine Volvo part, listed for XC90 2016-2023. "
                    "Two other genuine numbers (31492813, 30759240) also turned up for "
                    "this same function -- likely variant-code/supersession differences "
                    "not disambiguated here, same caveat pattern as several other entries "
                    "in this file."
                ),
            },
        ],
    },
    "TorqueConverter": {
        "sim_class": "xc90_sim.transmission.torque_converter.TorqueConverter",
        "real_parts": [
            {
                "name": "TG-81SC torque converter",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Several genuine Volvo 'XC90 torque converter' part numbers exist "
                    "(8251105, 31325001, 8647487, 30651139, 30713945) but every one that "
                    "could be attributed to a specific drivetrain is explicitly tied to "
                    "the FIRST-generation XC90's older transmissions (8251105 is stated "
                    "as fitting the '4T65EV-GT, 6CYL, TURBO' transmission; 31325001 is "
                    "tied to the 3.2L NA I6) -- none were confirmed as the converter "
                    "inside this car's Aisin TG-81SC 8-speed. Tried 3 query variants; no "
                    "TG-81SC-specific converter part number was found."
                ),
            },
        ],
    },
    "Transmission": {
        "sim_class": "xc90_sim.transmission.transmission.Transmission",
        "real_parts": [
            {
                "name": "Aisin TG-81SC 8-speed automatic transmission assembly",
                "oem_part_number": "1285130",
                "source_url": "https://www.ebay.com/itm/175251707545",
                "notes": (
                    "Cited on an eBay OEM-used-parts listing titled '16-20 Volvo XC90 "
                    "V90CC XC60 Automatic Transmission Assembly TG-81SC AWD 1285130' -- "
                    "plausible (used-parts resellers typically photograph and transcribe "
                    "the part tag off the actual removed unit) but NOT independently "
                    "corroborated on usparts.volvocars.com or a second retailer, so "
                    "confidence is moderate, not high. usparts.volvocars.com does list "
                    "a related sub-component, the transmission's 'Final gear: TG-81SC "
                    "AWD' page, confirming Volvo's own catalog uses the TG-81SC "
                    "designation for this car's transmission family, but that page does "
                    "not itself give a whole-assembly part number."
                ),
            },
        ],
    },
    "TransmissionFluid": {
        "sim_class": "xc90_sim.transmission.transmission_fluid.TransmissionFluid",
        "real_parts": [
            {
                "name": "Genuine Volvo ATF for the 8-speed automatic (Aisin AW, JWS3324 spec)",
                "oem_part_number": "31256775",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Transmission-oil/42923364/31256775.html",
                "notes": (
                    "Listed on usparts.volvocars.com as 'Transmission oil. Automatic, "
                    "CH, CN' for the XC90. Corroborated by a SwedeSpeed forum thread "
                    "specifically titled 'Volvo OEM 8-speed Transmission Fluid Change "
                    "Kit for XC90, XC60, V60, S60, S90, V90, XC40, XC70' and by the "
                    "fluid spec (JWS3324) matching the Aisin AWF8F45/TG-81SC 8-speed "
                    "family, not the older 6-speed TF-80SC (which uses the different "
                    "T-IV/JWS3309 spec, Volvo part 1161540/1161621 -- a different fluid "
                    "for a different, older transmission, correctly NOT used here). The "
                    "'CH, CN' region/variant qualifier on the listing was not resolved "
                    "against this VIN's exact build code, a minor residual caveat."
                ),
            },
        ],
    },
    "TireModel": {
        "sim_class": "xc90_sim.chassis.tire_model.TireModel",
        "real_parts": [
            {
                "name": "OE-fitment 235/55R19 touring tire (Pirelli Scorpion Verde, VOL-sidewall-marked)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": "https://www.pirelli.com/tyres/en-ww/car/catalogue/product/scorpion-verde/235_55-r19/105v-xl-volvo",
                "notes": (
                    "Pirelli's own catalog lists a 'Scorpion Verde 235/55R19 105V XL "
                    "VOLVO' product -- a real, Volvo-specific OE-homologated tire in "
                    "exactly this car's tire size (confirming one of the three "
                    "candidates specs/chassis.py already narrowed this VIN's tire to). "
                    "oem_part_number is NOT_FOUND deliberately: tires aren't sold under "
                    "a Volvo part number the way mechanical components are -- the real, "
                    "verifiable identity here is the tire manufacturer + model + size/ "
                    "load-index string above, not a numeric Volvo PN. specs/chassis.py "
                    "already documents that this project could not confirm which of the "
                    "three real OE-marked tire models (Pirelli Scorpion Verde, Michelin "
                    "Latitude Tour HP N0, Continental CrossContact LX Sport) is actually "
                    "mounted on this specific VIN -- this entry doesn't resolve that "
                    "ambiguity, it just independently confirms the Pirelli option is a "
                    "genuine, real OE product in this exact size, not an invented one."
                ),
            },
        ],
    },
    "Brakes": {
        "sim_class": "xc90_sim.chassis.brakes.Brakes",
        "real_parts": [
            {
                "name": "Front brake caliper, right (18/19-inch wheel package)",
                "oem_part_number": "36003280",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Disc-Brake-Caliper-18--19--Right--Front/97592602/36003280.html",
                "notes": (
                    "Genuine Volvo part, explicitly listed as '(18, 19, Right, Front)', "
                    "matching this car's confirmed 19-inch wheels. Also cross-listed for "
                    "the Volvo V90 (same SPA platform generation as the second-gen XC90), "
                    "corroborating it as a real, current-generation part rather than a "
                    "mislabeled first-generation (2003-2014) listing. Left-front caliper "
                    "part number (presumably a mirrored PN) was not separately confirmed."
                ),
            },
            {
                "name": "Rear brake caliper, left",
                "oem_part_number": "36003032",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Disc-Brake-Caliper/71853762/36003032.html",
                "notes": (
                    "Genuine Volvo part on usparts.volvocars.com's 2016 XC90 page. "
                    "Rear-left designation confirmed via PartsGeek's listing (ATE "
                    "36003032, Rear Left, 2016-2025 XC90 fitment); the Volvo-side "
                    "listing title alone did not spell out front/rear, so that specific "
                    "detail relies on the retailer cross-reference, not Volvo's title "
                    "text directly."
                ),
            },
            {
                "name": "Rear brake caliper, right",
                "oem_part_number": "36003033",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Disc-Brake-Caliper/71863304/36003033.html",
                "notes": "Same sourcing/caveat as the rear-left caliper above (PartsGeek: ATE 36003033, Rear Right, 2016-2025 XC90).",
            },
            {
                "name": "Front brake pad set (for 336mm front rotors -- matches this project's already-confirmed front rotor, part 30657301)",
                "oem_part_number": "32373170",
                "source_url": "https://www.ipdusa.com/products/13066/Front-Brake-Pad-Set-XC90-with-336mm-Rotors-Genuine-Volvo-32373170-30769125",
                "notes": (
                    "ipd (Genuine Volvo parts distributor) explicitly ties this pad set "
                    "to '336mm Rotors', the same rotor size this project already "
                    "verified (specs/chassis.py, part 30657301) for this car's front "
                    "brakes, which is good corroborating evidence this pad set is the "
                    "right one. Cross-referenced part 30769125. A second genuine Volvo "
                    "PN for the same 336mm-rotor pad set (32373161 / 31262705 / "
                    "31687101) also exists on ipd -- likely an earlier/later "
                    "superseded part number for the same physical pad, not "
                    "independently resolved which one this exact VIN's parts history "
                    "would show."
                ),
            },
            {
                "name": "Rear brake pad set (for 320mm rear rotors -- matches this project's already-confirmed rear rotor, parts 31471816/31400778)",
                "oem_part_number": "31471265",
                "source_url": "https://www.ipdusa.com/products/23106/Rear-Brake-Pads-320mm-and-some-340mm-rotors-P5-S60-V60-S90-V90-XC60-XC90-ATE-607326-Volvo-32287447",
                "notes": (
                    "Search results describe two genuine Volvo rear pad part numbers "
                    "keyed to brake variant code: 31471265 [variant RC01] or 32233035 "
                    "[variant RC02], both for 320mm-rotor-equipped XC90s -- this "
                    "project could not confirm which variant code (RC01 vs RC02) "
                    "applies to this specific VIN, so 31471265 is reported as the more "
                    "commonly-cited option, not a certain match. Both are real, "
                    "catalog-listed Volvo numbers, not a guess."
                ),
            },
        ],
    },
    "BrakeBooster": {
        "sim_class": "xc90_sim.chassis.brake_booster.BrakeBooster",
        "real_parts": [
            {
                "name": "Power brake booster",
                "oem_part_number": "31400307",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Power-Brake-Booster-Master-Cylinder--Power-Brake-Booster/65381098/31400307.html",
                "notes": (
                    "Genuine Volvo part, listed on usparts.volvocars.com fitting XC90 "
                    "2016-2023. Independently corroborated by Volvo Parts Counter's "
                    "listing, which states this part is specifically compatible with "
                    "the XC90 T6. A second candidate (31423490, usparts, 2016-2019 "
                    "fitment) also exists; 31400307's broader/more specific T6 "
                    "corroboration made it the primary pick here."
                ),
            },
        ],
    },
    "VacuumPump": {
        "sim_class": "xc90_sim.chassis.vacuum_pump.VacuumPump",
        "real_parts": [
            {
                "name": "Electric brake-booster vacuum pump",
                "oem_part_number": "31401152",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2013_XC90/Power-Brake-Booster-Vacuum-Pump/49477873/31401152.html",
                "notes": (
                    "RE-VERIFIED (already present in specs/chassis.py, not "
                    "re-researched from scratch as instructed). Confirmed genuine on "
                    "usparts.volvocars.com, listed as 'Power Brake Booster Vacuum "
                    "Pump' fitting XC90 (and S60/S80/V60/V70/XC60/XC70); a specific "
                    "2013 XC90 product page and a separate OEM-parts-online listing "
                    "citing 2010-2016 fitment both corroborate this covers the model "
                    "years spanning this car's 2016 build. This project found no "
                    "evidence the existing 31401152 value is wrong -- it checks out."
                ),
            },
        ],
    },
    "Wheel": {
        "sim_class": "xc90_sim.chassis.wheel.Wheel",
        "real_parts": [
            {
                "name": "19x8-inch alloy road wheel (6-spoke design)",
                "oem_part_number": "31414513",
                "source_url": "https://www.oemrimshop.com/products/volvo-xc90-oem-wheel-2016-2023-19x8-inch-31414513-314145137-6-spoke-factory-alloy-original-rim",
                "notes": (
                    "Real Volvo OEM wheel, 19x8in, 5x108 bolt pattern, +42.5mm offset, "
                    "fitting 2016-2023 XC90, matching this car's 235/55R19 tire size "
                    "per specs/chassis.py. Volvo offered multiple distinct 19-inch "
                    "wheel designs across XC90 trims/years (this 6-spoke design, plus a "
                    "10-spoke 'Turbine Silver' design, part 31362276, and other "
                    "variant-coded numbers like 31423021) -- this project could not "
                    "confirm via VIN decode which specific wheel design this VIN's "
                    "Momentum trim actually carries, so this is reported as A real "
                    "19-inch OEM wheel for this car, not confirmed as THE exact design "
                    "on this VIN."
                ),
            },
            {
                "name": "19-inch, 10-spoke 'Turbine Silver' alloy wheel (alternate design)",
                "oem_part_number": "31362276",
                "source_url": "https://volvo.oempartsonline.com/oem-parts/volvo-19-inch-10-spoke-turbine-silver-alloy-wheel-31362276",
                "notes": "Real, catalog-listed alternate 19-inch wheel design, 2016-2024 XC90 fitment. Same design-ambiguity caveat as above.",
            },
        ],
    },
    "VehicleBody": {
        "sim_class": "xc90_sim.chassis.vehicle_body.VehicleBody",
        "real_parts": [
            {
                "name": "N/A -- pure rigid-body physics abstraction",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "Not a failed search -- this class models the vehicle's mass, yaw "
                    "inertia, and 3-DOF planar dynamics as a simulation abstraction. "
                    "There is no single real 'vehicle body' part; the physical body "
                    "shell is a structural weldment/assembly Volvo does not sell as one "
                    "orderable part (body shop replacement is done via individual "
                    "stamped panels, which this class does not model). Reported "
                    "honestly as not applicable rather than forcing a part number onto "
                    "a physics abstraction."
                ),
            },
        ],
    },
    "Corner": {
        "sim_class": "xc90_sim.suspension.corner.Corner / xc90_sim.suspension.ride_model.RideModel",
        "real_parts": [
            {
                "name": "Front strut / shock absorber (MacPherson strut, per specs/suspension.py's confirmed front layout)",
                "oem_part_number": "32269059",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Suspension-Strut-Front-SHOCK-ABSORBER/75712616/32269059.html",
                "notes": (
                    "Genuine Volvo part, listed specifically on a '2016 Volvo XC90' "
                    "product page (usparts.volvocars.com), which is better year "
                    "specificity than most of the alternates found. Other real, "
                    "catalog-listed front strut PNs also exist for this car keyed to "
                    "different equipment variant codes (31681639 [variant 7C06], "
                    "31681640 [variant CI02/RA03/RI01], 31658458) -- likely "
                    "distinguishing standard vs. Four-C adaptive damping, but this "
                    "project could not confirm which variant code this specific "
                    "Momentum-trim VIN carries. specs/suspension.py already confirms "
                    "this car does NOT have Four-C (non-adjustable-damping suspension), "
                    "which narrows it but doesn't uniquely resolve the exact PN."
                ),
            },
            {
                "name": "Rear shock absorber",
                "oem_part_number": "32346010",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Suspension-Shock-Absorber-Rear/42913961/30635776.html",
                "notes": (
                    "Search results describe 32346010 as the genuine Volvo rear shock "
                    "'for models without active chassis, FWD or AWD without auto "
                    "level' -- consistent with this car's standard (non-Four-C, "
                    "non-active-chassis) rear suspension per specs/suspension.py, "
                    "though 'without auto level' specifically (vs. this car's actual "
                    "self-leveling equipment, if any) was not independently confirmed. "
                    "Other real variant-coded PNs (32346058, 32346059) exist for "
                    "active-chassis/auto-level AWD configurations, which this project "
                    "believes do not apply here but could not rule out with full "
                    "confidence. An older PN, 30635776, also shows up for the XC90 "
                    "rear shock generally but without year/variant specificity."
                ),
            },
            {
                "name": "Front coil spring",
                "oem_part_number": "31434858",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Spring-Suspension--Coil-Spring-and-Torsion-Spring-Front-FRONT-SPRING/71859142/31434858.html",
                "notes": (
                    "Genuine Volvo part, generic 'XC90' fitment listing (year/variant "
                    "not itemized in the catalog snippet retrieved). Other real "
                    "front-spring PNs also exist for this car (31451301, 32425859 "
                    "[2016-2027 fitment]) -- likely load-rating/equipment variants; "
                    "exact match to this VIN's specific build not confirmed."
                ),
            },
            {
                "name": "Rear transverse composite (fiber-reinforced) leaf spring",
                "oem_part_number": "32283083",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Leaf-Spring-Rear/97591042/32283083.html",
                "notes": (
                    "Genuine Volvo part, explicitly listed with variant codes 7806 and "
                    "780P, fitting XC90 2016-2024 -- reasonably specific. Corroborates "
                    "specs/suspension.py's already-researched finding (Volvo press "
                    "material + trade coverage) that the standard (non-Four-C) rear "
                    "suspension on this car uses a composite leaf spring, not a coil "
                    "spring. Other genuine variant-coded PNs (32283084 [7802/7807], "
                    "32370043 [7805], 32370039 [7803/7804]) also exist for this car -- "
                    "this project could not confirm which of the 7802/7803/7804/7805/ "
                    "7806/780P/7807 variant codes this specific VIN carries."
                ),
            },
        ],
    },
    "FrontControlArm": {
        "sim_class": "xc90_sim.suspension.linkage_geometry (front double-wishbone lower control arms; no dedicated class)",
        "real_parts": [
            {
                "name": "Front lower control arm, left",
                "oem_part_number": "32381882",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Suspension-Control-Arm-Left--Front--Lower/120878946/32381882.html",
                "notes": "Genuine Volvo part, explicitly '(Left, Front, Lower)'. Supersession number 32381879 also noted by the retailer listing (superseded/replaced part, same physical component).",
            },
            {
                "name": "Front lower control arm, right",
                "oem_part_number": "32370923",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Control-Arm-Wheel-Suspension-CN-Right--Front--Lower/120879718/32370923.html",
                "notes": "Genuine Volvo part, listed specifically on a 2016 XC90 product page, '(Right, Front, Lower)'.",
            },
        ],
    },
    "RearControlArm": {
        "sim_class": "xc90_sim.suspension.linkage_geometry (rear 'Integral Axle' multi-link arms; no dedicated class)",
        "real_parts": [
            {
                "name": "Rear trailing arm (multi-link 'Integral Axle' rear suspension)",
                "oem_part_number": "31360588",
                "source_url": "https://www.tascaparts.com/oem-parts/volvo-trailing-arm-31360588",
                "notes": (
                    "Genuine Volvo part ('Trailing Arm', includes bushings), listed "
                    "fitting 2016-2026 Volvo AWD models without Polestar -- matches "
                    "this car's AWD (non-Polestar) configuration. This is only ONE of "
                    "the several distinct links that make up the real multi-link "
                    "'Integral Axle' rear suspension (Volvo's own material describes "
                    "multiple lateral/toe links per corner, not just a trailing arm) -- "
                    "individual toe-link and upper-link part numbers for this specific "
                    "car were searched for but not found with confidence and are "
                    "reported as NOT_FOUND below rather than guessed."
                ),
            },
            {
                "name": "Rear multi-link toe link / upper link (additional links beyond the trailing arm)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "The real 'Integral Axle' rear suspension has more discrete links "
                    "than just the trailing arm found above, but this project could not "
                    "find confidently-attributed, VIN-relevant part numbers for the "
                    "remaining individual links (toe link, upper link) in the time "
                    "available across 3 query variants -- left NOT_FOUND rather than "
                    "assumed to share a part family with the trailing arm."
                ),
            },
        ],
    },
    "SteeringSystem": {
        "sim_class": "xc90_sim.steering.geometry.SteeringSystem",
        "real_parts": [
            {
                "name": "Electric power steering rack and pinion assembly",
                "oem_part_number": "36010518",
                "source_url": "https://usparts.volvocars.com/p/Volvo__/Rack-and-Pinion/102574570/36010518.html",
                "notes": (
                    "Genuine Volvo part, variant code FV01, listed fitting S90, V60 "
                    "Cross Country, V90, V90 Cross Country, XC60, and XC90 (the shared "
                    "SPA-platform electric-rack part family) across 2016-2022. A "
                    "second genuine Volvo rack PN, 36050014 ('Rack and Pinion. STEERING "
                    "GEAR, EXC'), also turned up for the XC90 specifically -- this "
                    "project could not confirm from public sources which of the two "
                    "variant codes (FV01 vs. the EXC-tagged one) matches this "
                    "specific VIN's steering ratio/assist calibration, so both are "
                    "reported here as real candidates rather than picking one with "
                    "false confidence."
                ),
            },
            {
                "name": "Electric power steering rack and pinion assembly (alternate variant)",
                "oem_part_number": "36050014",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Rack-and-Pinion/42834397/36050014.html",
                "notes": "Genuine Volvo part specifically listed for the XC90; see caveat on the primary entry above regarding unresolved variant-code ambiguity between this and 36010518.",
            },
        ],
    },
}
