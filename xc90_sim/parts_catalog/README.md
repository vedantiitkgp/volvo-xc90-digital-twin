# Parts catalog

Real Volvo OEM part numbers for this specific 2016 XC90 T6 Momentum AWD
(VIN YV4A22PKXG1092057), mapped to the simulated component classes in the
rest of `xc90_sim/`. This is a separate, additive layer — it doesn't feed
any physics, and nothing in `xc90_sim/sim/` imports it. It exists so the
simulation's components can be tied to real, orderable parts wherever one
genuinely exists, alongside (not instead of) the physics itself.

## The one rule that matters

**A part number here is either real and source-verified, or it's one of
two explicit sentinel strings.** Never a plausible-looking guess. This
project's entire discipline (real fact or flagged ASSUMPTION, everywhere
else in the sim) applies especially hard here: an invented part number
that looks real is actively harmful — someone could try to order it.

- **`"NOT_FOUND"`** — a real search, tried a few different ways, that
  didn't turn up a confirmed match for this exact car/generation. Still a
  normal, expected outcome, not a failure — correct for a pure software/
  logic class with no discrete hardware of its own (e.g. `TractionControl`,
  `OilLifeMonitor`, `CruiseController`), or a part that likely has a real
  number but couldn't be confidently pinned down.
- **`"NOT_APPLICABLE"`** — the real part doesn't exist for this component
  at all, confirmed rather than merely unsearched. E.g. `EGRValve`: this
  gasoline engine's cataloged "EGR valve" part numbers were confirmed to
  be for a different (diesel) engine family — this engine has no discrete
  external EGR valve, full stop, because it likely uses internal EGR via
  camshaft valve overlap instead, a real mechanism with no separate part.
- a real part that Volvo's catalog doesn't assign its own number to
  separately (e.g. a tire is a Pirelli product, not a Volvo part number;
  some relays are integrated into a CEM/fuse box rather than sold
  individually) is also `NOT_APPLICABLE`.

## Schema

Each domain file exports a module-level `PARTS` dict:

```python
PARTS = {
    "ClassName": {
        "sim_class": "xc90_sim.<package>.ClassName",
        "real_parts": [
            {
                "name": "Human-readable real part name",
                "oem_part_number": "12345678",  # or exactly "NOT_FOUND"
                "source_url": "https://...",     # or None if NOT_FOUND
                "notes": "caveats, confidence, why NOT_FOUND, etc.",
            },
            # a class can have multiple real_parts entries -- e.g. a
            # lumped sim class covering several real parts (CoolingSystem
            # -> radiator + thermostat + water pump + fan), or a class
            # with genuinely more than one physical instance (Battery ->
            # main + support; WheelBearing -> front + rear)
        ],
    },
}
```

`xc90_sim/parts_catalog/__init__.py` merges every domain file's `PARTS`
into one `PARTS_CATALOG` dict and exposes `lookup()`, `verified_part_number()`,
and `summary()`.

## Resolved questions

- **EGR valve** (resolved 2026-09-01, was previously an open question):
  confirmed this twincharged *gasoline* engine has no discrete external
  EGR valve — the candidate part numbers (31439464/36010130) are
  confirmed via two independent sources to be for the D4204T *diesel*
  engine family (D2/D3/D4/D5), not the gasoline B4204T9. Recorded as
  `NOT_APPLICABLE`, not `NOT_FOUND` — the real part genuinely doesn't
  exist here. The sim's `EGRValve` class still models a real effect (this
  engine very likely uses internal EGR via camshaft valve overlap
  instead, a real gasoline-engine technique), it just doesn't correspond
  to one discrete orderable part on this specific engine — see
  `xc90_sim/exhaust/egr_valve.py`.

## Known open questions (read before trusting a specific number)

- Several verified numbers carry a **generation/chassis-break caveat** in
  their `notes` — Volvo ran mid-cycle part changes within the same model
  years, and some search results were for the *first-generation* (2003–
  2014/2015, P2-platform) XC90 rather than this second-generation (SPA-
  platform) 2016 car; those were excluded, but a few remaining entries
  are a best-confidence match rather than a VIN-confirmed one.
- A handful of entries (front struts/springs, some trim-specific seat and
  wheel parts) are real Volvo part numbers, but Volvo splits these by an
  equipment/trim variant code that isn't exposed without a VIN-specific
  dealer lookup — flagged in `notes` rather than silently picked.

## Updating

If a `NOT_FOUND` gets a real answer later, or a flagged caveat gets
resolved, edit the relevant domain file directly (`engine_domain.py`,
`electrical_drivetrain_domain.py`, `transmission_chassis_domain.py`,
`body_dsc_domain.py`, `cabin_domain.py`) — there's no generated/derived
state to keep in sync beyond `__init__.py`'s merge, which just unions the
five dicts.
