# Report

I buy the tickets myself; every step ends at information.

1. **Publish**: `trip.py render itineraries.json selection.json > page.html`, then publish
   page.html as an artifact. Republishing the same path keeps the link. Done when I have
   the link and a short recap: the recommended option and its total.
2. **Recheck** when I ask before buying: search again the legs of the options shown,
   with COLLECT.md's site tricks, update them in trip.json, then combine. An option whose legs changed gets chosen again
   in selection.json, since its itinerary may be gone; then render and republish. Done
   when every shown leg reflects today's site and you told me what changed.
3. **Calendar** once I say I booked: align trip.json with my tickets (times, the exact
   Turin stop, train numbers, references I give), combine, then
   `trip.py ics itineraries.json <id> > trip.ics` with the booked itinerary's id in the new
   itineraries.json (ids change with times; raise `--per-shape` when it is missing), and
   send the file. Done when trip.ics is sent.
4. **Learn**: update `trips/lessons.md` with what this trip taught that will hold next
   time (a connection worth searching, a sell-out, a schedule pattern, a transfer time),
   dated, one line each, and correct the lines it proved wrong. Add the booked trip to
   its Trips list. Done when lessons.md holds this trip's lessons.
