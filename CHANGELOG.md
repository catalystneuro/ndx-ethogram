# Changelog for ndx-ethogram

## 0.2.0 (2026-11-20)

- New `EthogramEvents` type, a subclass of the core `EventsTable`, for the record of a
  scoring: one row per scored occurrence (point behaviors, closed states, and states
  that never closed), with a required `label`, an optional `subject`, comments in the
  inherited `annotation` column, a required `ethogram` link, and the provenance
  attributes and `source_video` and `observation_intervals` links of `EthogramBouts`.
- `EthogramBouts` gains a `source_events` link to the `EthogramEvents` it was derived
  from, and a `bout_concurrency` attribute (`partition`, `disjoint`, or `concurrent`)
  that replaces the catalogue's `exclusive`.
- `Ethogram` gains optional `modifiers`, `modifier_values`, and `excludes` columns. Its
  `exclusive` attribute is deprecated and will be removed in 0.3.0, so that released
  neuroconv versions, which set it, keep working with 0.2.0.
- Requires `pynwb>=4.2.0`, the first release with the core `EventsTable`.

## 0.1.0 (2026-06-24)

- `EthogramBouts` carries a single required text `label` column (a behavior name where
  one exists, the tool's own cluster/motif id rendered as text such as "7" otherwise).
  The earlier two-column design (a required integer `label_id` plus an optional text
  `label`) was dropped: unsupervised cluster ids are arbitrary and run-specific rather
  than a stable identity, and named producers supply names, not integers, so a parallel
  integer code earned nothing the string did not already carry. See the design note
  "One text `label`, no integer `label_id`".
