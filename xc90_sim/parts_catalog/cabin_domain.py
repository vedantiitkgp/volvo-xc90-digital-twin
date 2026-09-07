"""
Real Volvo OEM parts researched for the cabin electronics domain. See
xc90_sim/parts_catalog/README.md (if present) or STATUS.md for the overall
catalog's scope and honesty rules: a part number here is either here is either a real, source-verified number, exactly the string
"NOT_FOUND" (search didn't confirm one), or exactly the string
"NOT_APPLICABLE" (the real part doesn't exist for this component) --
never a plausible-looking guess.

Researched against: 2016 Volvo XC90 T6 Momentum AWD, VIN YV4A22PKXG1092057,
second-generation (SPA-platform) XC90.

General platform note (relevant to several entries below): this generation
of XC90 uses ONE integrated windshield-mounted camera+radar module (Volvo's
"collision avoidance sensor" / forward sensing unit, mounted at the top of
the windshield near the rearview mirror) to feed City Safety, Adaptive
Cruise Control/Pilot Assist AND Lane Keeping Aid simultaneously -- it is NOT
two separate physical units for ACC vs. lane-keeping. This is reflected
below: ForwardRadar and LaneCamera cite the SAME OEM part number. A second,
much older-generation part number pattern (31660981, "FSM", CH 102260-) that
turned up in early searches was checked and ruled out -- verified via
usparts.volvocars.com to fit only the previous-generation P3 platform
(XC60/XC70/S60/S80, 2013-2017), NOT the SPA-platform XC90 -- so it is
deliberately excluded here despite looking superficially plausible.

Several sub-entries below carry a fitment-confidence caveat in their notes
even though the part number itself is a real, verifiable Volvo part number
(not fabricated) -- this happens where a search turned up a genuine catalog
listing for the XC90/shared-SPA-platform part but could not conclusively
confirm the exact model-year range from the available source snippet. Those
are flagged explicitly rather than silently presented as certain.
"""

PARTS = {
    "BlindSpotMonitor": {
        "sim_class": "xc90_sim.cabin.blind_spot_monitor.BlindSpotMonitor",
        "real_parts": [
            {
                "name": "Blind Spot Information System (BLIS) radar sensor, left rear",
                "oem_part_number": "31665692",
                "source_url": "https://usparts.volvocars.com/p/Volvo__/Blind-Spot-Detection-System-Warning-Sensor-Left/71860446/31665692.html",
                "notes": (
                    "Genuine Volvo part (variant code LW02). Corroborated by an eBay OEM "
                    "listing citing this same part family as fitting XC90 2016-2019, which "
                    "covers this car's model year."
                ),
            },
            {
                "name": "Blind Spot Information System (BLIS) radar sensor, right rear",
                "oem_part_number": "31665693",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Blind-Spot-Detection-System-Warning-Sensor-Right/71855968/31665693.html",
                "notes": (
                    "Genuine Volvo part, paired with 31665692 above. eBay OEM listing "
                    "('VOLVO XC90 BLIND SPOT RADAR SENSOR RIGHT REAR 2016 2017 2018 2019') "
                    "explicitly confirms 2016-2019 XC90 fitment."
                ),
            },
        ],
    },
    "ForwardRadar": {
        "sim_class": "xc90_sim.cabin.adaptive_cruise.ForwardRadar",
        "real_parts": [
            {
                "name": "Forward-facing camera + radar module (windshield-mounted, shared with lane camera)",
                "oem_part_number": "31471458",
                "source_url": "https://volvo-shop.com/front-radar-sensor-camera-unit-volvo-xc60-xc90-2016-31471458",
                "notes": (
                    "Genuine-parts retailer listing titled 'FRONT RADAR SENSOR CAMERA UNIT "
                    "VOLVO XC60 XC90 2016' -- explicitly names this exact model year. This "
                    "is the SAME physical unit cited under LaneCamera below; see the "
                    "module-level docstring on the shared-module architecture. Requires "
                    "professional calibration after replacement on the real car."
                ),
            },
        ],
    },
    "AdaptiveCruiseController": {
        "sim_class": "xc90_sim.cabin.adaptive_cruise.AdaptiveCruiseController",
        "real_parts": [
            {
                "name": "Adaptive Cruise Control follow-distance logic (no discrete part)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "This class is the follow-gap/target-speed control LAW layered on top "
                    "of ForwardRadar's sensor data and CruiseController's speed-tracking -- "
                    "a software algorithm, not a separate orderable hardware part. The real "
                    "hardware it depends on (the radar/camera module) is captured under "
                    "ForwardRadar above."
                ),
            },
        ],
    },
    "Airbag": {
        "sim_class": "xc90_sim.cabin.airbags.Airbag",
        "real_parts": [
            {
                "name": "Driver frontal airbag module (steering wheel)",
                "oem_part_number": "39834784",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Airbag-Module-Drivers-Side-Restraint-System-SRS-Supplemental-Charcoal/65394647/39834784.html",
                "notes": "Genuine Volvo part, listed as fitting XC90 2016-2026 (charcoal trim color code).",
            },
            {
                "name": "Passenger frontal airbag module (dashboard)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Search turned up only the shared Air Bag Control Module and an eBay "
                    "listing title ('2016-2023 Volvo XC90 RH Passenger Dash Airbag Air Bag "
                    "OEM') without a captured, confirmable part number -- did not verify "
                    "confidently enough to record a number."
                ),
            },
            {
                "name": "Side (thorax) airbag, driver seat / left",
                "oem_part_number": "31418256",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Airbag-module/54748700/31418256.html",
                "notes": "Genuine Volvo 'Seat Air Bag (Left)' part for the XC90.",
            },
            {
                "name": "Side (thorax) airbag, passenger seat / right",
                "oem_part_number": "31436486",
                "source_url": "https://www.ebay.com/itm/197616021568",
                "notes": (
                    "eBay OEM listing '2016-2025 VOLVO XC90 FRONT RIGHT SIDE SEAT AIRBAG "
                    "AIR BAG OEM' -- explicit 2016 fitment. Note: usparts.volvocars.com also "
                    "lists right seat airbags under 32403042 and 31690365 for XC90, but "
                    "fitment-year confirmation for those two was inconclusive from search "
                    "snippets alone (32403042's numbering pattern looks like a later "
                    "facelift part); 31436486 is used here as the more confidently-dated "
                    "match for this specific 2016 car."
                ),
            },
            {
                "name": "Curtain airbag, left",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Only found: an eBay listing title referencing a 2016 XC90 curtain "
                    "airbag without a captured part number, and a usparts.volvocars.com "
                    "'Curtain Air Bag' listing (part 9208895) that is explicitly for the "
                    "2022 XC90 facelift, not this 2016 car. Also ruled out 31271166 (FCP "
                    "Euro / ProxyParts) -- that part is confirmed for the first-generation "
                    "'XC90 I' (2002-2014), a different platform entirely, not this SPA-"
                    "platform 2016 car."
                ),
            },
            {
                "name": "Curtain airbag, right",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": "Same search outcome as curtain airbag left -- no confidently-dated 2016 SPA-platform part number found.",
            },
        ],
    },
    "AirbagSystem": {
        "sim_class": "xc90_sim.cabin.airbags.AirbagSystem",
        "real_parts": [
            {
                "name": "SRS (airbag) control module / crash sensor unit",
                "oem_part_number": "32315584",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Air-Bag-Control-Module/102570443/32315584.html",
                "notes": "Genuine Volvo part, listed directly on a '2016 Volvo XC90' catalog page (alternate/superseded number 31681216).",
            },
        ],
    },
    "LaneCamera": {
        "sim_class": "xc90_sim.cabin.lane_keeping_assist.LaneCamera",
        "real_parts": [
            {
                "name": "Forward camera + radar module (windshield-mounted, shared with forward radar)",
                "oem_part_number": "31471458",
                "source_url": "https://volvo-shop.com/front-radar-sensor-camera-unit-volvo-xc60-xc90-2016-31471458",
                "notes": (
                    "Confirmed to be the SAME physical unit as ForwardRadar's part above -- "
                    "this generation of XC90 uses one shared, windshield-mounted camera+"
                    "radar module (mounted near the rearview mirror) for City Safety, "
                    "Pilot Assist/ACC, and Lane Keeping Aid together. See module docstring."
                ),
            },
        ],
    },
    "LaneKeepingAssist": {
        "sim_class": "xc90_sim.cabin.lane_keeping_assist.LaneKeepingAssist",
        "real_parts": [
            {
                "name": "Lane-keeping corrective steering logic (no discrete part)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "This class is the bounded proportional correction LAW plus driver-"
                    "override logic -- pure software running on top of the shared camera/"
                    "radar module's data (see LaneCamera) and the real EPS steering rack. "
                    "No discrete part corresponds to this class itself."
                ),
            },
        ],
    },
    "HVAC": {
        "sim_class": "xc90_sim.cabin.hvac.HVAC",
        "real_parts": [
            {
                "name": "HVAC / climate control module (control unit, CCM)",
                "oem_part_number": "31472269",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Climate-Control-Module-Control-Unit/71853103/31472269.html",
                "notes": "Genuine Volvo part on a '2016 Volvo XC90' catalog page, listed as fitting XC90 2016-2027 (alternate number 31455683).",
            },
            {
                "name": "HVAC blower (fan) motor",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "The blower motor part numbers found (31320393, 30733954) are "
                    "explicitly listed as fitting the earlier first-generation XC90 "
                    "(2003-2014/2015), a different platform -- not a valid match for this "
                    "2016 SPA-platform car. A confirmed 2016+ front blower motor part "
                    "number was not found in reasonable search effort."
                ),
            },
        ],
    },
    "Infotainment": {
        "sim_class": "xc90_sim.cabin.infotainment.Infotainment",
        "real_parts": [
            {
                "name": "Sensus infotainment head unit (IHU) with GPS navigation",
                "oem_part_number": "36003119",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Radio-Control-Unit-with-GPS-Navigation-Infotainment-Head-Unit-IHU-HW-314832224--31667536--31466207--31667538-HW-31483224--31667536--31466207--31667758/71855120/36003119.html",
                "notes": (
                    "Genuine Volvo part, listed as fitting XC90 2016-2022. A separate "
                    "exchange/remanufactured-unit listing (36011500) is also on a '2016 "
                    "Volvo XC90' specific catalog page and may be the correct number "
                    "depending on radio/nav hardware variant -- both are real, verified "
                    "Volvo part numbers for this generation's Sensus IHU, but the exact "
                    "one for this specific car's build would need VIN-level confirmation."
                ),
            },
        ],
    },
    "CruiseController": {
        "sim_class": "xc90_sim.cabin.controls.CruiseController",
        "real_parts": [
            {
                "name": "Proportional throttle/brake cruise controller (no discrete part)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "Pure software speed-tracking controller (proportional throttle/brake "
                    "law), matching this project's own docstring framing -- explicitly "
                    "self-contained and separate from the real driver-facing switches "
                    "(see SteeringWheelControls) and pedal hardware (see PedalInputs)."
                ),
            },
        ],
    },
    "SteeringWheelControls": {
        "sim_class": "xc90_sim.cabin.controls.SteeringWheelControls",
        "real_parts": [
            {
                "name": "Steering wheel switch, audio/cruise control cluster",
                "oem_part_number": "32266343",
                "source_url": "https://usparts.volvocars.com/p/Volvo__/Switch-Steering-Wheel-Crystal-Look-Audio-Cruise-Control/97589812/32266343.html",
                "notes": (
                    "Genuine Volvo part ('Crystal Look' trim variant), cross-referenced "
                    "elsewhere as fitting Volvo SPA-platform cars 2016-2025 including XC90. "
                    "A closely related part number, 32266342, was found cited by ipdusa.com "
                    "specifically for a '2016 Volvo XC90 T6' (this exact car's engine/trim "
                    "family) with 'Matte Black' steering wheel buttons -- steering wheel "
                    "switch part numbers are color/finish-variant-dependent, so the exact "
                    "number for this specific car's actual wheel trim could differ from "
                    "either number listed here without a VIN-level check."
                ),
            },
        ],
    },
    "PedalInputs": {
        "sim_class": "xc90_sim.cabin.controls.PedalInputs",
        "real_parts": [
            {
                "name": "Accelerator pedal position sensor assembly",
                "oem_part_number": "31445944",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Accelerator-Pedal-Sensor/65181492/31445944.html",
                "notes": (
                    "Genuine Volvo part, listed for XC90 (also cross-listed for XC60, a "
                    "shared SPA-platform part). Explicit 2016-specific fitment confirmation "
                    "was not visible in the available source snippet -- flagged as a "
                    "fitment-confidence caveat rather than certain. A different part number, "
                    "31329056, was explicitly ruled out: it is confirmed to fit only the "
                    "earlier P2-platform XC90 (2003-2015), not this SPA-platform 2016 car."
                ),
            },
            {
                "name": "Brake pedal assembly",
                "oem_part_number": "31201400",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Pedal-arrangement-Brake-Control-Brake-Pedal/42899675/31201400.html",
                "notes": (
                    "Genuine Volvo 'Pedal arrangement, Brake Control, Brake Pedal' part "
                    "listed on the XC90 catalog. Explicit 2016-specific model-year fitment "
                    "was not visible in the available source snippet -- fitment-confidence "
                    "caveat, not a fabricated number."
                ),
            },
        ],
    },
    "Seat": {
        "sim_class": "xc90_sim.cabin.seats.Seat",
        "real_parts": [
            {
                "name": "Complete seat assembly (driver / front passenger / row2 L+R / row3 L+R)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "Volvo does not catalog a 'complete seat' as one single orderable part "
                    "number -- seats are sold as many separate sub-components (frame, "
                    "cushion pad, seat back panel, trim cover, motors, etc.), each with its "
                    "own part number and its own trim-color/upholstery-code variants. A "
                    "single per-position 'seat assembly' PN genuinely does not exist to "
                    "find, for any of the 6 seating positions -- this is an honest '0 "
                    "discrete parts at this granularity' answer, not a research gap. Two "
                    "confirmed real sub-components are listed below instead."
                ),
            },
            {
                "name": "Front seat heater pad (driver / front passenger)",
                "oem_part_number": "31413712",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Seat-Heater-Pad-Seat-heater-pad/65426824/31413712.html",
                "notes": "Genuine Volvo part, listed as fitting XC90 2016-2022.",
            },
            {
                "name": "Rear seat heater pad (row 2)",
                "oem_part_number": "32136000",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Seat-Heater-Pad/75709238/32136000.html",
                "notes": (
                    "Genuine Volvo part, listed as fitting XC90 2016-2022 (alternate "
                    "number 32206448). Could not confirm from search whether this is "
                    "specifically row 2 vs. a shared row2/row3 part number -- this car's "
                    "specs (xc90_sim.specs.cabin.REAR_SEATS_HEATED) determine which real "
                    "rear rows actually have heating; row-level PN granularity beyond that "
                    "was not confirmable."
                ),
            },
        ],
    },
    "Seating": {
        "sim_class": "xc90_sim.cabin.seats.Seating",
        "real_parts": [
            {
                "name": "Seating layout composition (no discrete part)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "This class is a pure software container/composition of the 6 "
                    "individual Seat objects (2-3-2 layout) plus the seatbelt-reminder "
                    "logic -- it does not itself correspond to any single real part. See "
                    "Seat above for the real seat sub-components."
                ),
            },
        ],
    },
    "ParkAssistPilot": {
        "sim_class": "xc90_sim.cabin.park_assist_pilot.ParkAssistPilot",
        "real_parts": [
            {
                "name": "Park Assist Pilot semi-autonomous steering module",
                "oem_part_number": "31399352",
                "source_url": "https://www.volvodealeraccessories.com/sku/31399352.html",
                "notes": (
                    "Real Volvo part number found for 'Volvo Parking Assistance Pilot' -- "
                    "sourced from Volvo's own dealer-accessories catalog description "
                    "matching this class's real-world behavior (semi-automatic parallel "
                    "parking; car steers while driver handles gears/throttle/brake). Note: "
                    "this is listed on an accessories/retrofit-kit storefront, so it may "
                    "represent a retrofit kit part number rather than the OEM factory-build "
                    "module number for a car ordered with this option from new -- flagged "
                    "as a caveat, not certain to be identical either way. The shared EPS "
                    "(electric power steering) rack this feature also depends on was not "
                    "separately researched/confirmed here."
                ),
            },
        ],
    },
    "ParkingAssist": {
        "sim_class": "xc90_sim.cabin.parking_assist.ParkingAssist",
        "real_parts": [
            {
                "name": "Ultrasonic parking aid sensor, front bumper",
                "oem_part_number": "31471005",
                "source_url": "https://usparts.volvocars.com/p/Volvo__/Parking-Aid-Sensor/65209286/31471005.html",
                "notes": (
                    "Genuine Volvo 'Parking Aid Sensor' (alternate number 31381691), "
                    "listed as fitting S90/V90/V90 Cross Country/XC60/XC90 -- a shared "
                    "SPA-platform part. Explicit 2016-specific fitment year and front-vs-"
                    "rear position were not both clearly confirmed from the available "
                    "source snippet -- fitment-confidence caveat."
                ),
            },
            {
                "name": "Ultrasonic parking aid sensor, rear bumper",
                "oem_part_number": "32292457",
                "source_url": "https://usparts.volvocars.com/p/Volvo__/Parking-Aid-Sensor/102570608/32292457.html",
                "notes": (
                    "Genuine Volvo 'Parking Aid Sensor', listed as fitting S60/S90/V60/V60 "
                    "Cross Country/V90/V90 Cross Country/XC60/XC90 -- another shared SPA-"
                    "platform part. Same fitment-confidence caveat as the front sensor "
                    "above; could not confirm this is specifically the rear (vs. front) "
                    "variant from the source snippet alone."
                ),
            },
        ],
    },
    "OilLifeMonitor": {
        "sim_class": "xc90_sim.cabin.maintenance.OilLifeMonitor",
        "real_parts": [
            {
                "name": "Oil life monitor (no discrete part)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "Confirmed pure software: a mileage-based countdown reset via a "
                    "service-menu action, not a continuous oil-quality sensor and not a "
                    "discrete orderable part -- matches this project's own docstring "
                    "framing exactly. Zero discrete orderable parts is the correct, honest "
                    "answer here."
                ),
            },
        ],
    },
    "TPMS": {
        "sim_class": "xc90_sim.cabin.tpms.TPMS",
        "real_parts": [
            {
                "name": "TPMS sensor, front left wheel",
                "oem_part_number": "31362304",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Tire-Pressure-Monitoring-System-TPMS-Sensor/65434887/31362304.html",
                "notes": "Genuine Volvo part on a '2016 Volvo XC90' specific catalog page. TPMS sensors are identical/interchangeable across all 4 wheel positions on this car, so the same part number applies to all 4 corners below.",
            },
            {
                "name": "TPMS sensor, front right wheel",
                "oem_part_number": "31362304",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Tire-Pressure-Monitoring-System-TPMS-Sensor/65434887/31362304.html",
                "notes": "Same part as front-left -- one universal TPMS sensor part number is used at every wheel position.",
            },
            {
                "name": "TPMS sensor, rear left wheel",
                "oem_part_number": "31362304",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Tire-Pressure-Monitoring-System-TPMS-Sensor/65434887/31362304.html",
                "notes": "Same part as front-left -- one universal TPMS sensor part number is used at every wheel position.",
            },
            {
                "name": "TPMS sensor, rear right wheel",
                "oem_part_number": "31362304",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Tire-Pressure-Monitoring-System-TPMS-Sensor/65434887/31362304.html",
                "notes": (
                    "Same part as front-left -- one universal TPMS sensor part number is "
                    "used at every wheel position. Note: an alternate 315 MHz-variant "
                    "sensor (31200923) also turned up for the 2016 XC90 -- North American-"
                    "market cars use 315 MHz TPMS while other markets use 433 MHz, so "
                    "31200923 rather than 31362304 could be the correct number depending "
                    "on which frequency variant this specific US-market car actually uses; "
                    "not resolved further here."
                ),
            },
        ],
    },
    "Storage": {
        "sim_class": "xc90_sim.cabin.storage.Storage",
        "real_parts": [
            {
                "name": "Glove box assembly",
                "oem_part_number": "30722840",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Glove-Box-Glove-CompartmentGlove-Box/42840188/30722840.html",
                "notes": (
                    "Genuine Volvo 'Glove compartment' part listed on the XC90 catalog. "
                    "Explicit 2016-specific model-year fitment was not visible in the "
                    "available source snippet -- fitment-confidence caveat, not a "
                    "fabricated number."
                ),
            },
            {
                "name": "Center console assembly",
                "oem_part_number": "39819462",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Center-Console-Interior-code-GX0X--GX6X--GV1Z--GX0X--GX6X--GX0X--GX6X/148060813/39819462.html",
                "notes": (
                    "Genuine Volvo part on a '2016 Volvo XC90' specific catalog page, tied "
                    "to specific interior trim codes (GX0X/GX6X/GV1Z) -- the exact code for "
                    "this specific car's actual interior trim was not separately confirmed, "
                    "so this may need adjustment if this car's interior code differs."
                ),
            },
        ],
    },
}
