# Changelog for ndx-ethogram

## 0.1.0 (unreleased)

- `EthogramBouts` carries a single required text `label` column (a behavior name where
  one exists, the tool's own cluster/motif id rendered as text such as "7" otherwise).
  The earlier two-column design (a required integer `label_id` plus an optional text
  `label`) was dropped: unsupervised cluster ids are arbitrary and run-specific rather
  than a stable identity, and named producers supply names, not integers, so a parallel
  integer code earned nothing the string did not already carry. See the design note
  "One text `label`, no integer `label_id`".
