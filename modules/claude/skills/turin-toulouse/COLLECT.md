# Collect

Turn my request into trip.json, then fill it with every **leg** the sites show.

1. **Pin the trip** in a new trip folder: `direction` (`turin-toulouse` or
   `toulouse-turin`), `date` (the day I want to arrive), `flex_days` (default 1, so the
   evening before counts), `arrive_by` or `leave_after` (local date and time) when I give
   one, `preferences` only for what I state. Ask only when the direction or the date is missing. Done when
   trip.json holds these fields.
2. **Read the memory**: `trips/lessons.md` and the past trip folders for this direction.
   They name the connections to search, which ones sell out, and where to pause. With an
   empty memory, search Turin ↔ Toulouse on Omio and SNCF Connect and follow the hubs
   they route through. Done when you have the list of connections to search, each with
   its site.
3. **Search each connection** in the built-in browser, for each day of the window, by
   train and bus. Done when each connection was searched for each day.
4. **Record every leg** of the window into trip.json, full ones (`"full": true`) and
   unpriced ones (`"price": null`) included: they explain the rejected options. Times are
   local, without offset; price is the cheapest 2nd class fare; a change inside one ticket
   goes in `changes`. A station outside `STATIONS` gets added to `trip.py`, with its
   transfer in `TRANSFERS` and a test. Done when `trip.py validate` prints ✓ and each
   `!` warning is explained.

## Site tricks

- Built-in browser: decline cookies. If clicks miss, set the viewport to 1280×1400 and
  click by `ref`; reset it to desktop when done. Read results with `get_page_text`.
- **SNCF Connect**: start from the Trains tab.
  - It never chains a hub on its own: search each connection separately.
  - Pick the city "Montpellier" to list both of its stations.
  - "Toulouse" autocompletes to a bus stop first: pick "Toulouse Matabiau" (gare).
  - Results start at the chosen hour (06h by default); "Afficher les trajets suivants"
    loads more.
  - "Non réservable" means no online price.
  - The same train can show twice with different fares: keep the cheaper.
- **Omio**: switch off "Trouver un hébergement" before searching (it opens Booking.com).
  Change the date from the strip on the results page.
