"""Tests for the deterministic steps of /turin-toulouse.

Run with `uv run --with pytest pytest` from the skill directory.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import trip

TESTS = SKILL / "tests"
TEMPLATE = (SKILL / "scripts" / "page.html").read_text()
NOW = datetime(2030, 1, 11, 18, 0, tzinfo=UTC)


def leg(origin, destination, depart, arrive, mode="high-speed-train", price=10, **extra):
    return {"from": origin, "to": destination, "depart": depart, "arrive": arrive,
            "mode": mode, "operator": "SNCF", "price": price, **extra}


def journey(legs, direction="turin-toulouse", **extra):
    return {"direction": direction, "date": "2030-01-17", "legs": legs, **extra}


def operators(itinerary):
    return [f"{step['operator']} {step['start'][11:16]}" for step in itinerary["steps"] if step["kind"] == "leg"]


def find(itineraries, expected):
    return next(itinerary for itinerary in itineraries["itineraries"] if operators(itinerary) == expected)


@pytest.fixture
def fixture():
    return json.loads((TESTS / "fixture.json").read_text())


@pytest.fixture
def selection():
    return json.loads((TESTS / "selection.json").read_text())


@pytest.fixture
def itineraries(fixture):
    return trip.combine(fixture, per_shape=100)


# Validate.


def test_fixture_is_valid(fixture):
    assert trip.validate(fixture) == ([], [])


def test_unknown_station_is_an_error():
    errors, _ = trip.validate(journey([leg("Lyon Part Dieu", "Toulouse Matabiau", "2030-01-17T06:40", "2030-01-17T10:52")]))
    assert errors == ["legs[0].from 'Lyon Part Dieu' is not a known station"]


def test_leg_arriving_before_departure_is_an_error():
    errors, _ = trip.validate(journey([leg("Lyon Part-Dieu", "Toulouse Matabiau", "2030-01-17T10:52", "2030-01-17T06:40")]))
    assert errors == ["legs[0] Lyon Part-Dieu → Toulouse Matabiau 17/01 10:52: arrives before it departs"]


def test_malformed_time_is_an_error():
    errors, _ = trip.validate(journey([leg("Lyon Part-Dieu", "Toulouse Matabiau", "17/01 06:40", "2030-01-17T10:52")]))
    assert errors == ["legs[0].depart '17/01 06:40' is not an ISO time"]


def test_partial_margin_override_keeps_the_other_margins(fixture):
    fixture["preferences"] = {"required_margin_minutes": {"after-bus": 30}}
    itabus = find(trip.combine(fixture, per_shape=100), ["Itabus 08:00", "TGV INOUI 14:10", "Intercités 19:05"])
    assert itabus["issues"] == []


def test_leg_outside_the_date_window_is_a_warning():
    errors, warnings = trip.validate(journey([leg("Lyon Part-Dieu", "Toulouse Matabiau", "2030-01-20T06:40", "2030-01-20T10:52")]))
    assert errors == []
    assert warnings == ["legs[0] Lyon Part-Dieu → Toulouse Matabiau 20/01 06:40: outside the date window"]


# Combine.


def test_the_best_trip_ranks_first(itineraries):
    best = itineraries["itineraries"][0]
    assert operators(best) == ["Flixbus 07:45", "TGV INOUI 14:10", "Intercités 19:05"]
    assert best["total_price"] == 136
    assert best["arrival"] == "2030-01-17T21:19:00+01:00"
    assert best["day_offset"] == 0
    assert best["pause_minutes"] == 100 + 165
    assert best["shortest_margin_minutes"] == 100
    assert best["issues"] == []
    assert [step["kind"] for step in best["steps"]] == ["leg", "pause", "leg", "pause", "leg"]


def test_full_legs_are_never_used(itineraries):
    used = {name for itinerary in itineraries["itineraries"] for name in operators(itinerary)}
    assert "Intercités 17:05" not in used
    assert all(
        (step["to"], step["start"][11:16]) != ("Toulouse Matabiau", "14:10")
        for itinerary in itineraries["itineraries"] for step in itinerary["steps"] if step["kind"] == "leg"
    )


def test_bus_to_train_needs_a_large_margin(itineraries):
    itabus = find(itineraries, ["Itabus 08:00", "TGV INOUI 14:10", "Intercités 19:05"])
    assert itabus["shortest_margin_minutes"] == 40
    assert itabus["issues"] == ["short-connection"]


def test_short_change_inside_a_leg_is_flagged(itineraries):
    narbonne = find(itineraries, ["Flixbus 07:45", "TGV INOUI 14:10", "TER liO 17:53"])
    assert narbonne["shortest_margin_minutes"] == 10
    assert narbonne["issues"] == ["short-connection"]


def test_night_bus_is_flagged(itineraries):
    assert find(itineraries, ["Flixbus 23:15"])["issues"] == ["night"]


def test_night_spent_waiting_in_a_station_is_flagged():
    data = journey([
        leg("Turin Porta Susa", "Lyon Part-Dieu", "2030-01-16T17:41", "2030-01-16T22:10"),
        leg("Lyon Part-Dieu", "Toulouse Matabiau", "2030-01-17T06:40", "2030-01-17T10:52"),
    ])
    assert trip.combine(data, per_shape=10)["itineraries"][0]["issues"] == ["night"]


def test_train_from_turin_is_over_budget(itineraries):
    train = find(itineraries, ["TGV INOUI 07:36", "TGV INOUI 14:10", "Intercités 19:05"])
    assert train["total_price"] == 205
    assert train["issues"] == ["over-budget"]


def test_unknown_price_is_flagged(itineraries):
    regional = find(itineraries, ["Flixbus 07:45", "TER 14:20", "Intercités 19:05"])
    assert regional["total_price"] is None
    assert regional["issues"] == ["price-unknown"]


def test_connection_must_fit_the_transfer():
    data = journey([
        leg("Turin", "Lyon Gerland", "2030-01-17T07:45", "2030-01-17T12:00", mode="bus"),
        leg("Lyon Part-Dieu", "Toulouse Matabiau", "2030-01-17T12:30", "2030-01-17T16:40"),
        leg("Lyon Part-Dieu", "Toulouse Matabiau", "2030-01-17T12:40", "2030-01-17T16:50"),
    ])
    found = trip.combine(data, per_shape=10)["itineraries"]
    assert [operators(itinerary) for itinerary in found] == [["SNCF 07:45", "SNCF 12:40"]]


def test_transfers_work_in_the_return_direction():
    data = journey([
        leg("Toulouse Matabiau", "Lyon Part-Dieu", "2030-01-19T06:40", "2030-01-19T10:52"),
        leg("Lyon Gerland", "Turin", "2030-01-19T13:00", "2030-01-19T17:15", mode="bus"),
    ], direction="toulouse-turin", date="2030-01-19")
    pause = trip.combine(data, per_shape=10)["itineraries"][0]["steps"][1]
    # The 30 minutes across Lyon come out of the pause.
    assert (pause["at"], pause["start"], pause["minutes"]) == ("Lyon Gerland", "2030-01-19T11:22:00+01:00", 98)


def test_the_cap_keeps_every_shape(fixture):
    everything = trip.combine(fixture, per_shape=100)["itineraries"]
    found = trip.combine(fixture, per_shape=1)["itineraries"]
    assert len(found) < len(everything)
    assert {trip.shape(itinerary) for itinerary in found} == {trip.shape(itinerary) for itinerary in everything}
    # Day itineraries breaking one preference, behind dozens of night buses in the ranking.
    assert {("over-budget",), ("price-unknown",), ("short-connection",)} <= {tuple(itinerary["issues"]) for itinerary in found}


def test_arrive_by_is_a_hard_limit(fixture):
    fixture["arrive_by"] = "2030-01-17T12:00"
    arrivals = {itinerary["arrival"] for itinerary in trip.combine(fixture, per_shape=100)["itineraries"]}
    assert arrivals == {"2030-01-17T10:52:00+01:00", "2030-01-17T11:50:00+01:00"}


def test_preferences_override_the_defaults(fixture):
    fixture["preferences"] = {"avoid_night": False}
    best = trip.combine(fixture, per_shape=100)["itineraries"][0]
    assert best["arrival"] == "2030-01-17T10:52:00+01:00"


@pytest.mark.parametrize("start, end, expected", [
    ("2030-01-17T07:45", "2030-01-17T12:00", False),
    ("2030-01-16T23:15", "2030-01-17T11:50", True),
    ("2030-01-17T04:25", "2030-01-17T08:45", True),
    ("2030-01-17T19:05", "2030-01-17T23:00", False),
])
def test_overlaps_night(start, end, expected):
    assert trip.overlaps_night(trip.local(start), trip.local(end)) is expected


# Render.


def payload(page):
    return json.loads(page.split("const PAGE = ")[1].split(";\n")[0])


def test_render_embeds_the_options(itineraries, selection):
    page = trip.render(itineraries, selection, TEMPLATE)
    assert "<title>From Turin to Toulouse</title>" in page
    day, night = payload(page)["options"]
    assert (day["label"], day["total"], day["price"], day["price_warning"]) == ("Recommended", "13h34", "€136", False)
    bus, train = day["legs"][:2]
    assert (bus["what"], bus["detail"], bus["price"], bus["origin"], bus["destination"]) == ("Flixbus", "", "€18", "Turin", "Lyon Gerland")
    assert (train["duration"], train["pause"]) == ("1h40", "2h10")
    assert (night["label"], night["issues"]) == ("Night", ["Night travel"])


def test_render_escapes_the_closing_script_tag(itineraries, selection):
    selection["options"][0]["name"] = "</script><b>x</b>"
    assert "</script><b>" not in trip.render(itineraries, selection, TEMPLATE)


def test_render_shares_one_time_axis(itineraries, selection):
    day, night = (option["legs"][0]["start"] for option in payload(trip.render(itineraries, selection, TEMPLATE))["options"])
    # Both count from the midnight before the night bus departs.
    assert (day, night) == (24 * 60 + 7 * 60 + 45, 23 * 60 + 30)


def test_render_clocks_follow_the_wall_across_summer_time():
    data = journey([leg("Turin", "Toulouse Matabiau", "2027-03-27T23:30", "2027-03-28T05:00", mode="bus")],
                   date="2027-03-28")
    itineraries = trip.combine(data, per_shape=1)
    selection = {"options": [{"id": itineraries["itineraries"][0]["id"], "name": "Night bus", "tag": "fallback"}]}
    night_bus = payload(trip.render(itineraries, selection, TEMPLATE))["options"][0]
    # The bus leaves at 23:30 and arrives at 05:00 on the clock, after 4h30 on the road.
    assert (night_bus["legs"][0]["start"], night_bus["legs"][0]["end"]) == (23 * 60 + 30, 24 * 60 + 5 * 60)
    assert night_bus["total"] == "4h30"


def test_render_asks_to_recombine_older_itineraries(itineraries, selection):
    del itineraries["direction"]
    with pytest.raises(SystemExit, match="run combine again"):
        trip.render(itineraries, selection, TEMPLATE)


def test_validate_checks_changes(fixture):
    fixture["legs"][0]["changes"] = [{"station": "Narbonne", "minutes": 10}]
    errors, _ = trip.validate(fixture)
    assert errors and "changes" in errors[0]


def test_render_rejects_an_empty_selection(itineraries, selection):
    selection["options"] = []
    with pytest.raises(SystemExit):
        trip.render(itineraries, selection, TEMPLATE)


def test_render_rejects_an_unknown_itinerary(itineraries, selection):
    selection["options"][0]["id"] = "missing"
    with pytest.raises(SystemExit):
        trip.render(itineraries, selection, TEMPLATE)


# Calendar.


def test_ics_exports_the_legs(itineraries):
    calendar = trip.ics(itineraries["itineraries"][0], NOW)
    lines = calendar.split("\r\n")
    assert [line for line in lines if line.startswith("SUMMARY:")] == [
        "SUMMARY:🚌 Turin — Lyon Gerland",
        "SUMMARY:🚄 Lyon Part-Dieu — Montpellier Sud-de-France",
        "SUMMARY:🚆 Montpellier Saint-Roch — Toulouse Matabiau",
    ]
    assert "DTSTART:20300117T131000Z" in lines
    assert "DTSTAMP:20300111T180000Z" in lines
    assert calendar.endswith("END:VCALENDAR\r\n")
    assert "\n" not in calendar.replace("\r\n", "")


@pytest.mark.parametrize("amount, expected", [(136, "€136"), (43.2, "€43.20"), (None, "price unknown")])
def test_euros(amount, expected):
    assert trip.euros(amount) == expected


@pytest.mark.parametrize("minutes, expected", [(45, "45 min"), (120, "2h"), (265, "4h25")])
def test_duration(minutes, expected):
    assert trip.duration(minutes) == expected


def test_ics_escapes_and_folds():
    assert trip.escape_ics("a,b;c\\d\ne") == "a\\,b\\;c\\\\d\\ne"
    folded = trip.fold("DESCRIPTION:" + "é" * 80)
    assert all(len(part.encode()) <= 75 for part in folded.split("\r\n"))
    assert folded.replace("\r\n ", "") == "DESCRIPTION:" + "é" * 80
