# Analyze

1. **Combine**: `trip.py combine trip.json > itineraries.json`. Each itinerary carries its
   `issues`: `night`, `early-start`, `short-connection`, `over-budget`, `price-unknown`.
   It keeps the best two of each **shape**, the route pattern (each ride's stations and
   operator, whatever the times), best first. Full legs stay out. When it finds nothing,
   the gap usually points to a leg Collect missed: go back for it. Relaxing a preference is
   my call. Done when itineraries.json exists.
2. **Choose** three to five options into selection.json, shaped like
   `tests/selection.json`, the best itinerary of the shapes worth showing:
   - one `recommended`: no issues, the best pauses and margins for my day, judged with
     `trips/lessons.md`; the sort order is only a first hint;
   - `variant`s that trade something real: earlier arrival, lower price;
   - a `fallback` for when the recommended's scarcest leg sells out;
   - `over-budget` only when it buys something I'd value.

   `label` overrides the tag's badge when the tag alone misleads. Rejected rows cover the
   other shapes and the full legs from trip.json, grouped when they fail the same way
   (night buses to Lyon), each with its arrival and the preference it breaks. Done when
   every shape in itineraries.json, and every full leg, is an option or in a rejected row.
