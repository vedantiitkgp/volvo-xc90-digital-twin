"""
Real Volvo OEM parts researched for the electrical/drivetrain domain. See
xc90_sim/parts_catalog/README.md (if present) or STATUS.md for the overall
catalog's scope and honesty rules: a part number here is either here is either a real, source-verified number, exactly the string
"NOT_FOUND" (search didn't confirm one), or exactly the string
"NOT_APPLICABLE" (the real part doesn't exist for this component) --
never a plausible-looking guess.

Researched against: 2016 Volvo XC90 T6 Momentum AWD, VIN YV4A22PKXG1092057,
Drive-E B4204T9 2.0L twincharged engine (Volvo's "2.0L 4-cylinder Turbo"
family designation on parts catalogs covers T5/T6/T8 alike), Haldex Gen 5
AWD, second-generation (SPA-platform) XC90.

General platform note (relevant to several entries below): the SPA-platform
XC90 (2015+) does not use discrete plug-in relays in the traditional P2-era
sense for most circuits -- relay functions for many circuits are integrated
into the Central Electronic Module (CEM) and the engine-compartment
relay/fuse box, not sold as individually named, separately orderable relay
parts. This is a real, sourced finding (see RelayBox entries), not a gap in
research.
"""

PARTS = {
    "AccessoryBelt": {
        "sim_class": "xc90_sim.electrical.AccessoryBelt",
        "real_parts": [
            {
                "name": "Serpentine (accessory drive) belt",
                "oem_part_number": "31430015",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Serpentine-Belt/62793135/31430015.html",
                "notes": (
                    "Genuine Volvo part, cross-referenced to 31316095. Listed as fitting "
                    "Volvo S60/S90/V60/V90/XC40/XC60/XC70/XC90 2014-2022, which covers this "
                    "car's 2.0L Drive-E engine family (T5/T6/T8 share the same accessory "
                    "belt path since this car has no belt-driven power steering pump -- "
                    "belt drives only the alternator and, via clutch, the AC compressor). "
                    "Not confirmed as T6-exclusive vs. shared across T5/T6/T8, but that is "
                    "expected -- Volvo's catalog does not split this part by trim."
                ),
            },
        ],
    },
    "AutoStopStart": {
        "sim_class": "xc90_sim.electrical.AutoStopStart",
        "real_parts": [
            {
                "name": "Engine Auto Start/Stop (no discrete part)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "Confirmed: this is a software feature implemented in the engine/"
                    "central control software (start-stop logic runs in the ECM/CEM), "
                    "not a discrete orderable part -- matches this project's own docstring "
                    "framing. There IS a physical dash Start/Stop disable button on this "
                    "car, but the sim class models only the stop/resume decision logic, "
                    "not that button, so no real part number applies to what's actually "
                    "modeled here. Zero discrete orderable parts is the correct, honest "
                    "answer for this class."
                ),
            },
        ],
    },
    "Alternator": {
        "sim_class": "xc90_sim.electrical.Alternator",
        "real_parts": [
            {
                "name": "Alternator assembly",
                "oem_part_number": "36011427",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90-20l-4-cylinder-Turbo/Alternator-Alternator--ExchangeAlternator/71858033/36011427.html",
                "notes": (
                    "Genuine Volvo part, explicitly listed for '2016 Volvo XC90 2.0L "
                    "4-cylinder Turbo' -- the engine family that includes this car's "
                    "B4204T9. A second number, 36012474 (exchange/core-charge variant, "
                    "listed under 'Variant, Code'), also turned up for the 2016 XC90; "
                    "not confident which output rating it represents relative to "
                    "36011427 (Volvo sometimes offers a higher-output alternator for "
                    "higher-electrical-load option packages), so 36011427 is given as "
                    "the primary match and 36012474 flagged here rather than asserted."
                ),
            },
        ],
    },
    "FuseBox": {
        "sim_class": "xc90_sim.electrical.FuseBox / Fuse",
        "real_parts": [
            {
                "name": "Primary fuse/relay box, engine compartment",
                "oem_part_number": "31409364",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Relay-Fuse-Box-StartStop-Primary-Fuse-Box-Engine-Compartment/65251323/31409364.html",
                "notes": "Genuine Volvo part, explicitly listed for the 2016 XC90.",
            },
            {
                "name": "Central Electronic Module (CEM) / relay and fuse box, passenger compartment",
                "oem_part_number": "31394157",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Electronics-Box-Central-Electronic-Module-CEM-Control-Units-Relay-and-Fuse-Box-Passenger-Compartment-CEM/42858018/31394157.html",
                "notes": (
                    "Genuine Volvo part for XC90's CEM (combined control unit + relay + "
                    "fuse box). Listing did not show an explicit '2016' year tag in "
                    "search results (unlike 31409364 above), so fitment to this exact "
                    "model year is a reasonable-confidence but not fully pinned match."
                ),
            },
            {
                "name": "Fuse: headlights circuit (15A, per specs.FUSE_RATING_HEADLIGHTS_A)",
                "oem_part_number": "31346548",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2019_XC90/Fuse-Blue/65252908/31346548.html",
                "notes": (
                    "Genuine Volvo 'Multi-Purpose Fuse (Blue), Micro 15A' -- confirmed "
                    "fitting XC90 2016-2025 (per volvopartscounter.com listing of the "
                    "same part number). This is a generic multi-position 15A fuse, not a "
                    "uniquely-named 'headlight fuse' SKU -- Volvo sells fuses by "
                    "amperage/type, not by circuit name, so the same part number occupies "
                    "whichever 15A slot a given circuit uses."
                ),
            },
            {
                "name": "Fuse: horn circuit (15A)",
                "oem_part_number": "31346548",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2019_XC90/Fuse-Blue/65252908/31346548.html",
                "notes": "Same generic 15A Micro fuse part as headlights above -- see that entry's note.",
            },
            {
                "name": "Fuse: infotainment circuit (15A)",
                "oem_part_number": "31346548",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2019_XC90/Fuse-Blue/65252908/31346548.html",
                "notes": "Same generic 15A Micro fuse part as headlights above -- see that entry's note.",
            },
            {
                "name": "Fuse: wipers circuit (25A)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": "Searched for a genuine Volvo 25A micro/mcase fuse part number distinctly; did not find one I could confirm.",
            },
            {
                "name": "Fuse: fuel pump circuit (20A)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": "Searched for a genuine Volvo 20A fuse part number distinctly; did not find one I could confirm.",
            },
            {
                "name": "Fuse: cooling fan circuit (40A)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Searched for a genuine Volvo 40A fuse part number for this platform; "
                    "found only an 8697089 'Fuse... Maxi... 40A' listing that appears to be "
                    "P2-era XC90 (2003-2014) naming/numbering, not confirmed for this "
                    "2016 SPA-platform car, so not used."
                ),
            },
            {
                "name": "Fuse: dome light circuit (10A)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": "Searched for a genuine Volvo 10A fuse part number distinctly; did not find one I could confirm.",
            },
            {
                "name": "Fuse: ECU main circuit (10A)",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": "Same as dome light above -- not found distinctly for this rating.",
            },
        ],
    },
    "Battery": {
        "sim_class": "xc90_sim.electrical.Battery",
        "real_parts": [
            {
                "name": "Main starter battery (AGM)",
                "oem_part_number": "31419211",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Vehicle-Battery/65286237/31419211.html",
                "notes": (
                    "Genuine Volvo part, explicitly listed for the 2016 XC90 (cross-"
                    "referenced to alternate number 31652065, also explicitly listed for "
                    "2016 XC90; Volvo's catalog carries multiple market/variant-coded "
                    "battery part numbers for the same model year, e.g. variant code "
                    "'CS03' seen in one listing -- 31419211 given as primary since it was "
                    "the first-listed genuine part for this exact model/year)."
                ),
            },
            {
                "name": "Support/auxiliary battery (buffers electronics during Auto Start/Stop engine-off)",
                "oem_part_number": "32238082",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Battery/97587808/32238082.html",
                "notes": (
                    "VERIFIED against the prior session's lead: 32238082 is confirmed via "
                    "usparts.volvocars.com as a genuine Volvo 'Battery... Support' part "
                    "explicitly listed for the 2016 XC90, and independently corroborated "
                    "by SKANDIX/FCP Euro/Superstart listings as a 12V 10Ah 170A AGM "
                    "auxiliary/support battery for start-stop XC90s -- this is a real, "
                    "well-corroborated match, sized close to this project's own "
                    "SUPPORT_BATTERY_CAPACITY_AH = 14.0 assumption. The other lead, "
                    "30659531, checked out as a genuine Volvo auxiliary/support battery "
                    "part number too (FCP Euro), but its listed fitment ('S60, S80, S90, "
                    "V60, V90, XC40, XC60, XC70, XC90' with no year breakdown) could not "
                    "be confirmed as covering the 2016 XC90 specifically -- it may be the "
                    "newer-model-years number the task description flagged it as. Using "
                    "32238082 as the number for this car; 30659531 not used due to "
                    "unconfirmed year fitment."
                ),
            },
        ],
    },
    "RelayBox": {
        "sim_class": "xc90_sim.electrical.RelayBox / Relay",
        "real_parts": [
            {
                "name": "Fuel pump relay (individually named/orderable)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "Confirmed (see module docstring) that this SPA-platform XC90 does "
                    "not sell most relay functions as discrete plug-in relay parts -- "
                    "they are positions/functions inside the engine-compartment relay/"
                    "fuse box (31409364, see FuseBox entry) and the CEM (31394157). "
                    "Aftermarket-only 'fuel pump relay' part numbers found in search "
                    "(e.g. SMP 859ZD78) were for the older 2003-2008 XC90 and don't apply "
                    "to this 2016 SPA-platform car."
                ),
            },
            {
                "name": "Starter relay (individually named/orderable)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": "Same integration finding as fuel pump relay above -- functions live in the relay/fuse box assembly, not as a separate SKU.",
            },
            {
                "name": "Cooling fan relay (individually named/orderable)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": "Same integration finding as fuel pump relay above.",
            },
            {
                "name": "Horn relay (individually named/orderable)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": "Same integration finding as fuel pump relay above.",
            },
            {
                "name": "Main ECU/ignition-switched relay (individually named/orderable)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": "Same integration finding as fuel pump relay above.",
            },
            {
                "name": "Physical assembly containing these relay functions: engine-compartment relay/fuse box",
                "oem_part_number": "31409364",
                "source_url": "https://usparts.volvocars.com/p/Volvo_2016_XC90/Relay-Fuse-Box-StartStop-Primary-Fuse-Box-Engine-Compartment/65251323/31409364.html",
                "notes": "Same part as the FuseBox entry above -- included here too since this is the real physical part RelayBox most directly maps to on this car.",
            },
        ],
    },
    "HaldexAWD": {
        "sim_class": "xc90_sim.drivetrain.HaldexAWD",
        "real_parts": [
            {
                "name": "AWD coupling unit (Haldex Gen 5 / Active On-demand Coupling, AOC)",
                "oem_part_number": "36010561",
                "source_url": "https://usparts.volvocars.com/p/volvo__/AWD-Coupling-Unit/103337878/36010561.html",
                "notes": (
                    "Genuine Volvo part (viscous/AWD coupling unit), confirmed via "
                    "volvopartscounter.com as fitting '2016-2023 Volvo' XC90, with "
                    "fitment explicitly restricted to AWD, non-hybrid, non-Polestar, "
                    "non-plug-in-hybrid variants -- matches this car exactly (2016 XC90 "
                    "T6 AWD, gasoline, non-hybrid). Corroborates specs/awd.py's research "
                    "that this generation is Haldex Gen 5 / BorgWarner-supplied AOC. Other "
                    "AWD-coupling part numbers found in search (8602807, 36000964, "
                    "36001386) use Volvo's older 'Ch -nnnnnn' chassis-number fitment "
                    "notation characteristic of the first-generation (2003-2014) P2-"
                    "platform XC90 and were NOT used, since they don't apply to this "
                    "second-generation (SPA) car."
                ),
            },
        ],
    },
    "OpenDifferential": {
        "sim_class": "xc90_sim.drivetrain.OpenDifferential",
        "real_parts": [
            {
                "name": "Rear differential (final drive)",
                "oem_part_number": "32324105",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Differential-Rear/102570611/32324105.html",
                "notes": "Genuine Volvo part, confirmed fitting XC90 2016-2022 (cross-referenced to alternate number 32249816).",
            },
            {
                "name": "Front differential (standalone assembly)",
                "oem_part_number": "NOT_APPLICABLE",
                "source_url": None,
                "notes": (
                    "Researched and found this is NOT a separately orderable part on "
                    "this car's architecture: this XC90's front differential is "
                    "integrated inside the transverse-mounted transmission/transaxle "
                    "casing (a real, sourced architectural fact -- 'the AWD in the 2nd "
                    "gen XC90 uses a bevel gear off the transmission in the front and a "
                    "[separate] differential in the rear'). What IS separately sold is a "
                    "bevel gear / power-transfer-unit (PTU, Volvo calls it 'Transfer "
                    "Case') that routes transmission output to the propshaft -- a genuine "
                    "Volvo part number 36002052 turned up for this ('Transfer Case, BEVEL "
                    "GEAR, EXCH', XC90) but its exact model-year fitment was not "
                    "confirmed and it is not itself a differential, so it's noted here "
                    "rather than used as the answer for 'front differential'."
                ),
            },
        ],
    },
    "CVJoint": {
        "sim_class": "xc90_sim.drivetrain.CVJoint",
        "real_parts": [
            {
                "name": "Front CV axle (right) -- includes both CV joints on that half-shaft, sold as one assembly",
                "oem_part_number": "36011808",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/CV-Axle-Right--Front/109273921/36011808.html",
                "notes": (
                    "Genuine Volvo part. Volvo does not sell individual CV joints "
                    "separately from the half-shaft for this car -- the whole CV axle "
                    "(shaft + inner and outer CV joints) is the orderable unit, so this "
                    "maps to (rather than exactly equals) the sim's per-joint model. A "
                    "second right-front number, 36003732 ('AXLE SHAFT, EXCH' variant), "
                    "also turned up; not confident which supersedes which, so 36011808 "
                    "given as primary."
                ),
            },
            {
                "name": "Front CV axle (left)",
                "oem_part_number": "36011804",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/CV-Axle-Left--Front/109273838/36011804.html",
                "notes": (
                    "Genuine Volvo part, found associated with the 2016 XC90 in search "
                    "results (alternate number 36010583 also referenced). Several other "
                    "left-front CV axle numbers also turned up in search (36010569, "
                    "36011818, 36003638) -- Volvo appears to have superseded/revised this "
                    "part multiple times across the XC90's production run, and I could "
                    "not confidently pin down which exact number applies to this "
                    "specific VIN's production date/options. 36011804 given as the "
                    "most-directly-2016-associated match found; treat the exact number "
                    "with some caution."
                ),
            },
        ],
    },
    "WheelBearing": {
        "sim_class": "xc90_sim.drivetrain.WheelBearing",
        "real_parts": [
            {
                "name": "Rear wheel bearing and hub assembly",
                "oem_part_number": "32331434",
                "source_url": "https://usparts.volvocars.com/p/Volvo__XC90/Wheel-Bearing-and-Hub-Rear-HUB-KIT/102573880/32331434.html",
                "notes": (
                    "Genuine Volvo part, one listing explicitly labels it '(Rear)', "
                    "confirmed fitting XC90 2016-2021/2022 across multiple usparts "
                    "listings. A closely related/possibly-superseding number, 32370046, "
                    "also turned up for the same rear position (cross-referenced to "
                    "32331433, a likely left/right pair partner of 32331434) -- both are "
                    "real Volvo parts for this position, exact current vs. superseded "
                    "status not fully disambiguated from search alone."
                ),
            },
            {
                "name": "Front wheel bearing and hub assembly",
                "oem_part_number": "NOT_FOUND",
                "source_url": None,
                "notes": (
                    "Numbers that came up for 'XC90 front wheel bearing' (30639875, "
                    "31406300) are confirmed to be for the first-generation, P2-platform "
                    "XC90 (2003-2015), NOT this second-generation (SPA, 2015+) car -- "
                    "explicitly ruled out rather than guessed-and-used. Could not find a "
                    "clearly-labeled 'front' wheel bearing/hub number for the 2016+ SPA "
                    "XC90 distinct from the rear one above within a reasonable search "
                    "effort (some listings for 32331434/32370046 were ambiguous or "
                    "conflictingly labeled front vs. rear across different resellers), so "
                    "marked NOT_FOUND rather than asserting a guess."
                ),
            },
        ],
    },
    "Propshaft": {
        "sim_class": "xc90_sim.drivetrain.Propshaft",
        "real_parts": [
            {
                "name": "Propshaft / drive shaft (front transfer unit to rear differential)",
                "oem_part_number": "32339130",
                "source_url": "https://www.volvodealerparts.com/oem-parts/volvo-drive-shaft-32339130",
                "notes": (
                    "Genuine Volvo part, listed fitment 'AWD without plug-in hybrid, "
                    "2016-2022 XC90' -- matches this car exactly (2016 XC90 T6 AWD, "
                    "gasoline, non-PHEV)."
                ),
            },
        ],
    },
}
