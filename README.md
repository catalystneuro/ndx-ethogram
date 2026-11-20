# ndx-ethogram Extension for NWB

An NWB extension for storing a curated, tool-agnostic behavior catalogue, its
labeled behavioral bouts, and the record of a manual scoring. It defines three
neurodata types:

- [`Ethogram`](#ethogram), the behavior catalogue or coding scheme, with one row per
  behavior type.
- [`EthogramBouts`](#ethogrambouts), the behavioral timeline, with one row per
  continuous occurrence of a state behavior.
- [`EthogramEvents`](#ethogramevents), the record of a scoring, with one row per
  scored occurrence: point behaviors, closed states, and states that never closed.

Together, these types provide a downstream-oriented, tool-agnostic representation of
behavioral annotations. Named producers (DeepEthogram, SimBA, CalMS21, CRIM13) use
human-readable behavior labels; integer-only unsupervised producers (VAME,
keypoint-MoSeq, B-SOiD) use the tool's cluster identifier as text (for example,
`"7"`).

## Installation

```bash
pip install ndx-ethogram
```

Or from a clone of this repository:

```bash
pip install -e .
```

## Ethogram

`Ethogram` is a `DynamicTable` containing the complete behavior catalogue or coding
scheme. It has one row per behavior type, including behaviors that were defined but
did not occur during the session. This is where occurrence-invariant information
belongs: the operational definition, whether a behavior is a state or point event,
the producing tool's native code, and any category or hierarchy.

An `EthogramBouts` table can link to an `Ethogram` through its optional `ethogram`
link, and an `EthogramEvents` table must. Each row's `label` then matches a value in
the catalogue's `behavior` column.

| Field | Kind | Required | Meaning |
|---|---|---|---|
| `behavior` | column (text) | yes | behavior name or identifier; the join key for `EthogramBouts.label` |
| `definition` | column (text) | yes | operational definition of the behavior |
| `behavior_type` | column (text) | no, except when an `EthogramEvents` links the catalogue | `state` for durative behaviors or `point` for instantaneous behaviors |
| `native_code` | column (integer) | no | producing tool's native integer identifier |
| `category` | column (text) | no | hierarchy or grouping for the behavior |
| `modifiers` | ragged column (text) | no | the behavior's modifier slots, each named after the `EthogramEvents` column its answers go to |
| `modifier_values` | doubly ragged column (text) | no | the menu of values each slot offers, empty for a free answer |
| `excludes` | ragged column (text) | no | behaviors that starting this one terminates |
| `exclusive` | attribute (boolean) | no | deprecated, removed in 0.3.0; use `bout_concurrency` on `EthogramBouts` |

## EthogramBouts

`EthogramBouts` is a `TimeIntervals` subclass containing the observed occurrences of
durative behaviors. Each row inherits `start_time` and `stop_time` and adds a required
text `label`. Overlapping behaviors are represented by overlapping rows.

This table is a downstream-oriented, lossy-by-design representation. A producing
tool's faithful native output, such as a per-frame motif or syllable sequence, belongs
in its own extension and can be referenced through the generic `source` link.

| Field | Kind | Required | Meaning |
|---|---|---|---|
| `start_time`, `stop_time` | column (float, s) | yes (inherited) | bout interval |
| `label` | column (text) | yes | behavior, motif, syllable, or cluster identity |
| `labeling_method` | attribute | yes | `manual`, `automated`, or `curated` |
| `source_software` | attribute | no | producing tool and version |
| `annotator` | attribute | no | human or lab responsible for manual or curated labels |
| `parameters` | attribute | no | JSON-encoded key hyperparameters |
| `bout_concurrency` | attribute | no | `partition`, `disjoint`, or `concurrent`; absent means unknown |
| `ethogram` | link | no | behavior catalogue from which the labels are drawn |
| `source` | link | no | faithful object from which the bouts were derived |
| `source_events` | link | no | `EthogramEvents` record the bouts were derived from |
| `source_pose` | link | no | upstream `PoseEstimation` |
| `source_video` | link | no | behavioral `ImageSeries` |
| `observation_intervals` | link | no | spans over which behaviors were assessed |

`bout_concurrency` records how the bouts of one subject relate in time:
`partition` means one bout at every observed instant, so the bouts tile the observed
time (VAME, keypoint-MoSeq, B-SOiD); `disjoint` means never more than one bout at
once, with gaps allowed; `concurrent` means bouts may overlap (DeepEthogram, SimBA,
most manual coding schemes). Bouts of different subjects may always overlap.

Only durative state behaviors belong in `EthogramBouts`; instantaneous point
behaviors belong in an `EthogramEvents`. A manual scorer can write the closed state
occurrences of its `EthogramEvents` as bouts too, so that tools reading bouts see
them, and link the record through `source_events`. Such a table is a view of the
record: count one table or the other, not both.

## EthogramEvents

`EthogramEvents` is an `EventsTable` subclass containing the record of a scoring, one
row per scored occurrence. Each row has the inherited `timestamp` (the onset) and
`duration`: the length of a closed state, `NaN` for a point behavior or for a state
that never closed. The linked catalogue's `behavior_type` tells the two `NaN` cases
apart, which is why the `ethogram` link is required here. A coder's free-text
comment goes in the inherited `annotation` column.

| Field | Kind | Required | Meaning |
|---|---|---|---|
| `timestamp` | column (float, s) | yes (inherited) | onset of the occurrence |
| `duration` | column (float, s) | no (inherited) | length of a closed state; `NaN` for a point or an unclosed state |
| `annotation` | column (text) | no (inherited) | the coder's comment |
| `label` | column (text) | yes | behavior of the occurrence |
| `subject` | column (text) | no | subject the occurrence is attributed to; empty for none |
| `labeling_method` | attribute | yes | `manual`, `automated`, or `curated` |
| `source_software` | attribute | no | producing tool and version |
| `annotator` | attribute | no | human or lab who scored the occurrences |
| `parameters` | attribute | no | JSON-encoded settings of the producing tool |
| `ethogram` | link | yes | behavior catalogue from which the labels are drawn |
| `source_video` | link | no | behavioral `ImageSeries` that was scored |
| `observation_intervals` | link | no | spans over which behaviors were assessed |

Modifiers, the answers a coder records with an occurrence, go in one ragged text
column per modifier slot, named by the producer; the catalogue's `modifiers` column
says which of them a behavior writes into. When an occurrence closes with different
answers or a different comment than it opened with, the closing ones go in a column
of the same name prefixed `stop_` (for example `stop_annotation`), written only when
some occurrence in the table changed.

## Usage

```python
from datetime import datetime, timezone

from pynwb import NWBFile, NWBHDF5IO
from ndx_ethogram import Ethogram, EthogramBouts

nwbfile = NWBFile(
    session_description="social behavior session",
    identifier="session-001",
    session_start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
)

# The complete coding scheme, including behaviors that may not occur in this session.
ethogram = Ethogram(
    name="behavior_catalogue",
    description="Behaviors scored in the social-interaction assay",
)
ethogram.add_row(
    behavior="grooming",
    definition="The subject cleans its own fur with its paws or mouth.",
    behavior_type="state",
)
ethogram.add_row(
    behavior="rearing",
    definition="The subject raises both forepaws from the floor.",
    behavior_type="state",
)

# `labeling_method` is "manual", "automated", or "curated".
bouts = EthogramBouts(
    name="behavior_bouts",
    description="Manually scored social-interaction behavior",
    labeling_method="manual",
    annotator="lab annotator 1",  # optional
    bout_concurrency="concurrent",  # optional
)
bouts.add_row(start_time=1.0, stop_time=2.5, label="grooming")
bouts.add_row(start_time=2.0, stop_time=3.0, label="rearing")   # overlap is allowed
bouts.ethogram = ethogram

behavior = nwbfile.create_processing_module("behavior", "behavioral bouts")
behavior.add(ethogram)
behavior.add(bouts)

with NWBHDF5IO("example.nwb", "w") as io:
    io.write(nwbfile)
```

### Optional source links

An `EthogramBouts` table can point at the objects it was derived from or aligns to,
each optional:

- `source_pose` -> the upstream ndx-pose `PoseEstimation` (pose-based tools).
- `source_video` -> the behavioral video `ImageSeries` the bouts align to.
- `source` -> the producing faithful object (e.g. a per-frame motif/syllable
  `TimeSeries` or a tool-specific container); a generic `NWBDataInterface` target so
  this extension stays tool-agnostic.
- `observation_intervals` -> a core `TimeIntervals` marking the spans over which the
  labels were assessed, for partial-coverage inputs. Within them, absence of a bout
  means the behavior was absent; outside, it was unobserved. Omit when assessed
  throughout. When coverage differs by subject or by behavior, tag the rows of the
  linked `TimeIntervals` with a `subject` or `label` column.

```python
bouts.source_pose = pose_estimation     # an ndx_pose.PoseEstimation
bouts.source_video = behavior_video     # a pynwb.image.ImageSeries
```

---
This extension was created using [ndx-template](https://github.com/nwb-extensions/ndx-template).
