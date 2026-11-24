#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Deterministic steps of the /turin-toulouse skill.

`validate` checks the legs collected in trip.json. `combine` chains them into
itineraries between Turin and Toulouse and measures each one against my
preferences. `render` turns the chosen itineraries into the comparison page, and
`ics` turns the booked one into calendar events. Searching the booking sites and
choosing what to recommend stay with the model.
"""

import argparse
import hashlib
import html
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Italy and France share the same clock, summer time included.
ZONE = ZoneInfo("Europe/Paris")

# Each known station and its city: a trip starts and ends at any station of its two cities.
STATIONS = {
    # Plain "Turin" is a bus stop not yet pinned down: take the exact one from the ticket.
    "Turin": "turin",
    "Turin Porta Susa": "turin",
    "Turin Porta Nuova": "turin",
    "Turin Stura": "turin",
    "Turin Lingotto": "turin",
    "Lyon Part-Dieu": "lyon",
    "Lyon Perrache": "lyon",
    "Lyon Gerland": "lyon",
    "Montpellier Saint-Roch": "montpellier",
    "Montpellier Sud-de-France": "montpellier",
    "Narbonne": "narbonne",
    "Nîmes": "nimes",
    "Marseille Saint-Charles": "marseille",
    "Toulouse Matabiau": "toulouse",
}

DIRECTIONS = {"turin-toulouse": ("turin", "toulouse"), "toulouse-turin": ("toulouse", "turin")}

# Minutes to cross a city between two stations, either way, walk to the platform included.
# How I cross is my call on the day.
TRANSFERS = [
    ("Lyon Gerland", "Lyon Part-Dieu", 30),
    ("Lyon Perrache", "Lyon Part-Dieu", 30),
    ("Montpellier Sud-de-France", "Montpellier Saint-Roch", 30),
]

# Each mode's calendar emoji and its fill on the page.
MODES = {
    "high-speed-train": ("🚄", "train"),
    "train": ("🚆", "train"),
    "bus": ("🚌", "bus"),
}

PREFERENCES = {
    # Below this, a connection is physically impossible and the chain is dropped.
    "min_connection_minutes": 5,
    # Below these, a margin stresses me and is flagged as short.
    "required_margin_minutes": {
        # A change inside one ticket.
        "change": 30,
        # Between two tickets.
        "connection": 30,
        # After a bus: Fréjus delays run long, and the next ticket is not protected.
        "after-bus": 90,
    },
    # A wait at least this long is a pause to read or eat.
    "pause_minutes": 60,
    # Departing before this time of day means a bad night.
    "earliest_departure": "06:30",
    "avoid_night": True,
    "budget": 150,
    "max_legs": 4,
    "max_duration_hours": 30,
}

NIGHT_START = time(23, 0)
NIGHT_END = time(5, 0)

# Each tag and its default badge on the page.
TAGS = {
    "recommended": "Recommended",
    "variant": "Variant",
    "fallback": "Fallback",
    "over-budget": "Over budget",
}

# Each issue as the page names it.
ISSUES = {
    "night": "Night travel",
    "early-start": "Early start",
    "short-connection": "Short connection",
    "over-budget": "Over budget",
    "price-unknown": "Price unknown",
}


def fail(message):
    sys.exit(f"✗ {message}")


def local(text):
    moment = datetime.fromisoformat(text)
    return moment.replace(tzinfo=ZONE) if moment.tzinfo is None else moment.astimezone(ZONE)


def load(path):
    with open(path) as file:
        return json.load(file)


# Collected data.


@dataclass(frozen=True)
class Leg:
    origin: str
    destination: str
    depart: datetime
    arrive: datetime
    mode: str
    operator: str
    number: str | None
    price: float | None
    full: bool
    changes: list
    reference: str | None


@dataclass(frozen=True)
class Transfer:
    origin: str
    destination: str
    minutes: int


def transfers_from(station):
    for origin, destination, minutes in TRANSFERS:
        if origin == station:
            yield Transfer(origin, destination, minutes)
        elif destination == station:
            yield Transfer(destination, origin, minutes)


class Trip:
    def __init__(self, data):
        start_city, end_city = DIRECTIONS[data["direction"]]
        self.origins = {station for station, city in STATIONS.items() if city == start_city}
        self.destinations = {station for station, city in STATIONS.items() if city == end_city}
        self.date = date.fromisoformat(data["date"])
        overrides = data.get("preferences", {})
        self.preferences = {
            **PREFERENCES, **overrides,
            "required_margin_minutes": {
                **PREFERENCES["required_margin_minutes"], **overrides.get("required_margin_minutes", {}),
            },
        }
        flex = timedelta(days=data.get("flex_days", 1))
        leave_after, arrive_by = data.get("leave_after"), data.get("arrive_by")
        self.window_start = (
            local(leave_after) if leave_after else datetime.combine(self.date - flex, time.min, ZONE)
        )
        self.window_end = (
            local(arrive_by) if arrive_by else datetime.combine(self.date + flex, time.max, ZONE)
        )
        self.legs = [
            Leg(
                origin=leg["from"],
                destination=leg["to"],
                depart=local(leg["depart"]),
                arrive=local(leg["arrive"]),
                mode=leg["mode"],
                operator=leg.get("operator", ""),
                number=leg.get("number"),
                price=leg.get("price"),
                full=leg.get("full", False),
                changes=leg.get("changes", []),
                reference=leg.get("reference"),
            )
            for leg in data.get("legs", [])
        ]


def is_iso(text):
    try:
        datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return False
    return True


def validate(data):
    """Return (errors, warnings) about trip.json."""
    errors, warnings = [], []
    if data.get("direction") not in DIRECTIONS:
        errors.append(f"direction must be one of {sorted(DIRECTIONS)}")
    if "date" not in data:
        errors.append("date is missing")
    for index, leg in enumerate(data.get("legs", [])):
        for key in ("from", "to", "depart", "arrive", "mode"):
            if key not in leg:
                errors.append(f"legs[{index}].{key} is missing")
        for key in ("from", "to"):
            if key in leg and leg[key] not in STATIONS:
                errors.append(f"legs[{index}].{key} {leg[key]!r} is not a known station")
        if "mode" in leg and leg["mode"] not in MODES:
            errors.append(f"legs[{index}].mode {leg['mode']!r} is not one of {sorted(MODES)}")
        for key in ("depart", "arrive"):
            if key in leg and not is_iso(leg[key]):
                errors.append(f"legs[{index}].{key} {leg[key]!r} is not an ISO time")
        for change in leg.get("changes", []):
            if not isinstance(change.get("at"), str) or not isinstance(change.get("minutes"), int):
                errors.append(f"legs[{index}].changes needs an `at` station and integer `minutes`: {change!r}")
    for key in ("date", "arrive_by", "leave_after"):
        if key in data and not is_iso(data[key]):
            errors.append(f"{key} {data[key]!r} is not an ISO date or time")
    if errors:
        return errors, warnings
    trip = Trip(data)
    for index, leg in enumerate(trip.legs):
        label = f"legs[{index}] {leg.origin} → {leg.destination} {leg.depart:%d/%m %H:%M}"
        if leg.arrive <= leg.depart:
            errors.append(f"{label}: arrives before it departs")
        elif leg.depart < trip.window_start or leg.arrive > trip.window_end:
            warnings.append(f"{label}: outside the date window")
    return errors, warnings


# Itineraries.


def minutes_between(start, end):
    return int((end - start).total_seconds() // 60)


def overlaps_night(start, end):
    day = start.date() - timedelta(days=1)
    while day <= end.date():
        night_start = datetime.combine(day, NIGHT_START, ZONE)
        night_end = datetime.combine(day + timedelta(days=1), NIGHT_END, ZONE)
        if start < night_end and end > night_start:
            return True
        day += timedelta(days=1)
    return False


def chains(trip):
    """Yield every leg sequence from an origin to a destination inside the window, with the transfers between.

    Full legs stay out: trip.json keeps them to explain the rejected options.
    """
    preferences = trip.preferences
    longest = timedelta(hours=preferences["max_duration_hours"])
    legs_by_origin = {}
    for leg in trip.legs:
        if not leg.full and leg.arrive <= trip.window_end:
            legs_by_origin.setdefault(leg.origin, []).append(leg)

    def extend(path, transfers, visited):
        last = path[-1]
        if last.destination in trip.destinations:
            yield path, transfers
            return
        if len(path) >= preferences["max_legs"]:
            return
        options = [(last.destination, None)] + [
            (transfer.destination, transfer) for transfer in transfers_from(last.destination)
        ]
        for station, transfer in options:
            ready = last.arrive + timedelta(
                minutes=(transfer.minutes if transfer else 0) + preferences["min_connection_minutes"]
            )
            for leg in legs_by_origin.get(station, []):
                if leg.depart < ready or leg.destination in visited or leg.arrive - path[0].depart > longest:
                    continue
                yield from extend(path + [leg], transfers + [transfer], visited | {leg.destination})

    for origin in sorted(trip.origins):
        for leg in legs_by_origin.get(origin, []):
            if leg.depart >= trip.window_start:
                yield from extend([leg], [], {leg.origin, leg.destination})


def build_itinerary(trip, legs, transfers):
    preferences = trip.preferences
    required = preferences["required_margin_minutes"]
    # Every margin with its kind, to judge it against the margin it requires.
    steps, margins = [], []
    for index, leg in enumerate(legs):
        if index > 0:
            previous, transfer = legs[index - 1], transfers[index - 1]
            # Crossing the city to the next station comes out of the margin.
            ready = previous.arrive + timedelta(minutes=transfer.minutes if transfer else 0)
            margin = minutes_between(ready, leg.depart)
            margins.append((margin, "after-bus" if previous.mode == "bus" else "connection"))
            if margin > 0:
                steps.append({
                    "kind": "pause" if margin >= preferences["pause_minutes"] else "wait",
                    "at": leg.origin, "minutes": margin,
                    "start": ready.isoformat(), "end": leg.depart.isoformat(),
                })
        margins.extend((change["minutes"], "change") for change in leg.changes)
        steps.append({
            "kind": "leg", "mode": leg.mode, "operator": leg.operator, "number": leg.number,
            "from": leg.origin, "to": leg.destination,
            "start": leg.depart.isoformat(), "end": leg.arrive.isoformat(),
            "price": leg.price, "reference": leg.reference, "changes": leg.changes,
        })

    prices = [leg.price for leg in legs]
    total = None if None in prices else round(sum(prices), 2)
    departure, arrival = legs[0].depart, legs[-1].arrive
    issues = []
    if total is None:
        issues.append("price-unknown")
    elif preferences["budget"] is not None and total > preferences["budget"]:
        issues.append("over-budget")
    if preferences["avoid_night"] and overlaps_night(departure, arrival):
        issues.append("night")
    if NIGHT_END <= departure.time() < time.fromisoformat(preferences["earliest_departure"]):
        issues.append("early-start")
    if any(minutes < required[kind] for minutes, kind in margins):
        issues.append("short-connection")

    key = "|".join(f"{leg.origin}@{leg.depart.isoformat()}" for leg in legs)
    return {
        "id": hashlib.sha1(key.encode()).hexdigest()[:8],
        "departure": departure.isoformat(),
        "arrival": arrival.isoformat(),
        "day_offset": (arrival.date() - trip.date).days,
        "total_price": total,
        "pause_minutes": sum(step["minutes"] for step in steps if step["kind"] == "pause"),
        "shortest_margin_minutes": min((minutes for minutes, _ in margins), default=None),
        "issues": issues,
        "steps": steps,
    }


def shape(itinerary):
    """The route pattern: each ride's stations and operator, whatever the times."""
    return tuple((step["from"], step["to"], step["operator"]) for step in itinerary["steps"] if step["kind"] == "leg")


def combine(data, per_shape):
    trip = Trip(data)
    itineraries = [build_itinerary(trip, legs, transfers) for legs, transfers in chains(trip)]
    itineraries.sort(key=lambda itinerary: (
        len(itinerary["issues"]), abs(itinerary["day_offset"]),
        itinerary["arrival"], math.inf if itinerary["total_price"] is None else itinerary["total_price"],
    ))
    # Keep the best few of each shape: the time variants of one route add little, and an
    # overall cap let dozens of night buses push whole routes out.
    kept = Counter()
    best = []
    for itinerary in itineraries:
        if kept[shape(itinerary)] < per_shape:
            kept[shape(itinerary)] += 1
            best.append(itinerary)
    return {"direction": data["direction"], "date": data["date"], "itineraries": best}


def by_id(itineraries):
    return {itinerary["id"]: itinerary for itinerary in itineraries["itineraries"]}


# Report.


def duration(minutes):
    hours, rest = divmod(minutes, 60)
    if not hours:
        return f"{rest} min"
    return f"{hours}h{rest:02d}" if rest else f"{hours}h"


def euros(amount):
    if amount is None:
        return "price unknown"
    return f"€{amount:.0f}" if amount == int(amount) else f"€{amount:.2f}"


def change_text(change):
    return f"Change at {change['at']}: {change['minutes']} min"


def render(itineraries, selection, template):
    if "direction" not in itineraries:
        fail("itineraries.json predates the direction field: run combine again")
    known = by_id(itineraries)
    for choice in selection["options"]:
        if choice["id"] not in known:
            fail(f"selection option {choice['id']} is not in the itineraries")
        if choice["tag"] not in TAGS:
            fail(f"selection tag {choice['tag']!r} is not one of {sorted(TAGS)}")
    chosen = [known[choice["id"]] for choice in selection["options"]]
    if not chosen:
        fail("selection has no options")
    # One time axis for the whole page, in local wall-clock minutes from the midnight before the
    # earliest departure, so its clocks read right across a summer-time change.
    midnight = min(datetime.fromisoformat(itinerary["departure"]) for itinerary in chosen).replace(
        hour=0, minute=0, tzinfo=None,
    )
    options = []
    for choice, itinerary in zip(selection["options"], chosen):
        issues = set(itinerary["issues"])
        # Only the rides: pauses show as the gaps between them, and crossing a city is mine to plan.
        legs, previous_end = [], None
        for step in itinerary["steps"]:
            if step["kind"] != "leg":
                continue
            departs, arrives = datetime.fromisoformat(step["start"]), datetime.fromisoformat(step["end"])
            legs.append({
                "class": MODES[step["mode"]][1],
                "what": " ".join(part for part in (step["operator"], step["number"]) if part),
                "detail": ", ".join(change_text(change) for change in step["changes"]),
                "price": euros(step["price"]), "origin": step["from"], "destination": step["to"],
                "start": minutes_between(midnight, departs.replace(tzinfo=None)),
                "end": minutes_between(midnight, arrives.replace(tzinfo=None)),
                "duration": duration(minutes_between(departs, arrives)),
                # The time since the previous ride, crossing the city included.
                "pause": duration(minutes_between(previous_end, departs)) if previous_end else "",
            })
            previous_end = arrives
        options.append({
            "name": choice["name"], "tag": choice["tag"], "label": choice.get("label", TAGS[choice["tag"]]),
            "notes": choice.get("notes", []),
            "issues": [ISSUES[issue] for issue in itinerary["issues"]],
            "total": duration(minutes_between(
                datetime.fromisoformat(itinerary["departure"]), datetime.fromisoformat(itinerary["arrival"]),
            )),
            "price": euros(itinerary["total_price"]),
            "price_warning": bool(issues & {"over-budget", "price-unknown"}),
            # The raw price, for sorting the options on the page.
            "price_value": itinerary["total_price"],
            "legs": legs,
        })
    origin, destination = DIRECTIONS[itineraries["direction"]]
    title = f"From {origin.capitalize()} to {destination.capitalize()}"
    page = {"rejected": [], **selection, "title": title, "options": options}
    payload = json.dumps(page, ensure_ascii=False).replace("</", "<\\/")
    return template.replace("__TITLE__", html.escape(title)).replace("__DATA__", payload)


def escape_ics(text):
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """Fold a content line at 75 octets, as RFC 5545 requires."""
    encoded, parts, limit = line.encode(), [], 75
    while len(encoded) > limit:
        cut = limit
        while (encoded[cut] & 0xC0) == 0x80:
            cut -= 1
        parts.append(encoded[:cut].decode())
        encoded = encoded[cut:]
        # Continuation lines start with a space, which counts.
        limit = 74
    parts.append(encoded.decode())
    return "\r\n ".join(parts)


def utc(moment):
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def ics(itinerary, now):
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//dotfiles//turin-toulouse//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
    ]
    for index, step in enumerate(itinerary["steps"]):
        if step["kind"] != "leg":
            continue
        details = [step["operator"], step["number"]]
        details += [change_text(change) for change in step["changes"]]
        if step["reference"]:
            details.append(f"Reference {step['reference']}")
        description = "\n".join(detail for detail in details if detail)
        summary = f"{MODES[step['mode']][0]} {step['from']} — {step['to']}"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{itinerary['id']}-{index}@turin-toulouse",
            f"DTSTAMP:{utc(now)}",
            f"DTSTART:{utc(datetime.fromisoformat(step['start']))}",
            f"DTEND:{utc(datetime.fromisoformat(step['end']))}",
            f"SUMMARY:{escape_ics(summary)}",
            f"LOCATION:{escape_ics(step['from'])}",
        ]
        if description:
            lines.append(f"DESCRIPTION:{escape_ics(description)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "".join(fold(line) + "\r\n" for line in lines)


# Command line.


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("validate", help="check trip.json")
    command.add_argument("trip")
    command = commands.add_parser("combine", help="print itineraries.json")
    command.add_argument("trip")
    command.add_argument("--per-shape", type=int, default=2, help="itineraries kept for each route pattern")
    command = commands.add_parser("render", help="print the comparison page")
    command.add_argument("itineraries")
    command.add_argument("selection")
    command = commands.add_parser("ics", help="print one itinerary as calendar events")
    command.add_argument("itineraries")
    command.add_argument("id")
    arguments = parser.parse_args()

    if arguments.command == "validate":
        data = load(arguments.trip)
        errors, warnings = validate(data)
        for warning in warnings:
            print(f"! {warning}")
        for error in errors:
            print(f"✗ {error}")
        if errors:
            sys.exit(1)
        print(f"✓ {len(data.get('legs', []))} legs")
    elif arguments.command == "combine":
        data = load(arguments.trip)
        errors, _ = validate(data)
        if errors:
            fail(f"trip.json is invalid, run validate: {errors[0]}")
        if arguments.per_shape < 1:
            fail("--per-shape must be at least 1")
        result = combine(data, arguments.per_shape)
        if not result["itineraries"]:
            fail("no itinerary reaches the destination in the date window")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif arguments.command == "render":
        template = (Path(__file__).parent / "page.html").read_text()
        print(render(load(arguments.itineraries), load(arguments.selection), template))
    elif arguments.command == "ics":
        itineraries = by_id(load(arguments.itineraries))
        if arguments.id not in itineraries:
            fail(f"itinerary {arguments.id} is not in {arguments.itineraries}")
        sys.stdout.write(ics(itineraries[arguments.id], datetime.now(UTC)))


if __name__ == "__main__":
    main()
