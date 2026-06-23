# ndx-ethogram Extension for NWB

An NWB extension for storing a curated, tool-agnostic ethogram as labeled behavioral
bouts: one row per bout, where a bout is a continuous interval of a single behavior.
`EthogramBouts` is a `TimeIntervals` subclass, so each row inherits `start_time` and
`stop_time` and adds a single text `label`.

It is the downstream-oriented, lossy-by-design product of behavioral
segmentation and classification tools. Named producers (DeepEthogram, SimBA, CalMS21,
CRIM13) give the label a human-readable behavior name; integer-only unsupervised
producers (VAME, keypoint-MoSeq, B-SOiD) give it the tool's own cluster id as text
(e.g. `"7"`). Overlapping behaviors are simply overlapping rows. A tool's faithful
native output (per-frame motif or syllable stream) lives in its own extension and is
referenced through the generic `source` link, so this extension depends on no
tool-specific extension.

## Installation

```bash
pip install ndx-ethogram
```

Or from a clone of this repository:

```bash
pip install -e .
```

## Usage

```python
from datetime import datetime, timezone

from pynwb import NWBFile, NWBHDF5IO
from ndx_ethogram import EthogramBouts

nwbfile = NWBFile(
    session_description="social behavior session",
    identifier="session-001",
    session_start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
)

# One EthogramBouts table. `labeling_method` is required: "manual" (a human scored
# the video), "automated" (an algorithm), or "curated" (human-reviewed model output).
bouts = EthogramBouts(
    name="behavior_bouts",
    description="DeepEthogram behavior bouts",
    labeling_method="manual",
    source_software="DeepEthogram 0.1.4",   # optional
    annotator="lab annotator 1",            # optional
)

# One row per bout. `label` is the only added column (single required text column).
bouts.add_row(start_time=1.0, stop_time=2.5, label="grooming")
bouts.add_row(start_time=2.0, stop_time=3.0, label="rearing")   # overlap is allowed

behavior = nwbfile.create_processing_module("behavior", "behavioral bouts")
behavior.add(bouts)

with NWBHDF5IO("example.nwb", "w") as io:
    io.write(nwbfile)
```

### Optional links

A `EthogramBouts` table can point at the objects it was derived from or aligns to,
each optional:

- `source_pose` -> the upstream ndx-pose `PoseEstimation` (pose-based tools).
- `source_video` -> the behavioral video `ImageSeries` the bouts align to.
- `source` -> the producing faithful object (e.g. a per-frame motif/syllable
  `TimeSeries` or a tool-specific container); a generic `NWBDataInterface` target so
  this extension stays tool-agnostic.
- `observation_intervals` -> a core `TimeIntervals` marking the spans over which the
  labels were assessed, for partial-coverage inputs. Within them, absence of a bout
  means the behavior was absent; outside, it was unobserved. Omit when assessed
  throughout.

```python
bouts.source_pose = pose_estimation     # an ndx_pose.PoseEstimation
bouts.source_video = behavior_video     # a pynwb.image.ImageSeries
```

## Attributes and columns at a glance

| Field | Kind | Required | Meaning |
|---|---|---|---|
| `start_time`, `stop_time` | column (float, s) | yes (inherited) | the bout span |
| `label` | column (text) | yes | the bout's behavior / motif / cluster identity |
| `labeling_method` | attribute | yes | `manual`, `automated`, or `curated` |
| `source_software` | attribute | no | producing tool and version |
| `annotator` | attribute | no | human or lab who produced manual/curated labels |
| `parameters` | attribute | no | JSON-encoded key hyperparameters |
| `source` | link | no | the faithful producing object |
| `source_pose` | link | no | upstream `PoseEstimation` |
| `source_video` | link | no | the behavioral video `ImageSeries` |
| `observation_intervals` | link | no | spans over which labels were assessed |

Only durative (state) behaviors belong here; instantaneous point behaviors belong in
an `EventsTable`.

---
This extension was created using [ndx-template](https://github.com/nwb-extensions/ndx-template).
