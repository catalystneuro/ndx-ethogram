"""pytest tests for the EthogramEvents neurodata type."""

import numpy as np
import pytest
from pynwb import NWBHDF5IO, validate
from pynwb.epoch import TimeIntervals
from pynwb.testing.mock.file import mock_NWBFile

from ndx_ethogram import Ethogram, EthogramBouts, EthogramEvents


def make_catalogue():
    """A manual coding scheme with a state that has a modifier slot, a plain state and a point behavior."""
    catalogue = Ethogram(name="coding_scheme", description="BORIS coding scheme")
    catalogue.add_row(
        behavior="walking",
        definition="The subject moves forward on all four paws.",
        behavior_type="state",
        modifiers=["walking_speed"],
        modifier_values=[["slow", "fast"]],
        excludes=["standing"],
    )
    catalogue.add_row(
        behavior="standing",
        definition="The subject stays still on all four paws.",
        behavior_type="state",
        modifiers=[],
        modifier_values=[],
        excludes=["walking"],
    )
    catalogue.add_row(
        behavior="jump",
        definition="All four paws leave the floor.",
        behavior_type="point",
        modifiers=[],
        modifier_values=[],
        excludes=[],
    )
    return catalogue


def make_events(catalogue):
    """A closed state that changed its modifier mid-way, a point behavior and a state that never closed."""
    events = EthogramEvents(
        name="scoring",
        description="BORIS observation of one session",
        labeling_method="manual",
        ethogram=catalogue,
        source_software="BORIS 8.27",
        annotator="lab annotator 1",
    )
    events.add_column(name="walking_speed", description="The 'walking_speed' modifier answered at onset.", index=True)
    events.add_column(
        name="stop_walking_speed", description="The 'walking_speed' modifier answered at offset.", index=True
    )
    events.add_row(
        timestamp=1.0,
        duration=2.0,
        label="walking",
        subject="mouse_1",
        annotation="",
        walking_speed=["slow"],
        stop_walking_speed=["fast"],
    )
    events.add_row(
        timestamp=1.5,
        duration=np.nan,
        label="jump",
        subject="mouse_1",
        annotation="jumped over the wall",
        walking_speed=[],
        stop_walking_speed=[],
    )
    events.add_row(
        timestamp=4.0,
        duration=np.nan,
        label="standing",
        subject="",
        annotation="",
        walking_speed=[],
        stop_walking_speed=[],
    )
    return events


def write_nwb(nwbfile, path):
    with NWBHDF5IO(path, mode="w") as io:
        io.write(nwbfile)


def test_ethogram_is_required():
    with pytest.raises(TypeError, match="missing argument 'ethogram'"):
        EthogramEvents(name="scoring", description="no catalogue", labeling_method="manual")


def test_roundtrip(tmp_path):
    """Points, closed states and unclosed states round-trip, with their comments, subjects and modifiers."""
    nwbfile = mock_NWBFile()
    catalogue = make_catalogue()
    events = make_events(catalogue)
    behavior_module = nwbfile.create_processing_module("behavior", "behavior")
    behavior_module.add(catalogue)
    nwbfile.add_events_table(events)
    path = str(tmp_path / "events.nwb")

    write_nwb(nwbfile, path)
    assert validate(path=path) == []
    with NWBHDF5IO(path, mode="r") as io:
        read_events = io.read().events["scoring"]
        assert type(read_events).__name__ == "EthogramEvents"
        assert read_events.labeling_method == "manual"
        assert read_events.source_software == "BORIS 8.27"
        assert read_events.annotator == "lab annotator 1"
        assert read_events.ethogram.name == "coding_scheme"
        assert list(read_events["label"][:]) == ["walking", "jump", "standing"]
        assert list(read_events["timestamp"][:]) == [1.0, 1.5, 4.0]
        durations = read_events["duration"][:]
        assert durations[0] == 2.0
        assert np.isnan(durations[1]) and np.isnan(durations[2])
        assert list(read_events["subject"][:]) == ["mouse_1", "mouse_1", ""]
        assert list(read_events["annotation"][:]) == ["", "jumped over the wall", ""]
        assert list(read_events["walking_speed"][0]) == ["slow"]
        assert list(read_events["stop_walking_speed"][0]) == ["fast"]


def test_nan_duration_is_resolved_by_the_catalogue(tmp_path):
    """A NaN duration is a point behavior or a state that never closed; the catalogue's behavior_type says which."""
    nwbfile = mock_NWBFile()
    catalogue = make_catalogue()
    events = make_events(catalogue)
    behavior_module = nwbfile.create_processing_module("behavior", "behavior")
    behavior_module.add(catalogue)
    nwbfile.add_events_table(events)
    path = str(tmp_path / "events.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r") as io:
        read_events = io.read().events["scoring"]
        read_catalogue = read_events.ethogram
        behavior_type = dict(zip(read_catalogue["behavior"][:], read_catalogue["behavior_type"][:]))
        nan_labels = [
            label for label, duration in zip(read_events["label"][:], read_events["duration"][:]) if np.isnan(duration)
        ]
        assert [behavior_type[label] for label in nan_labels] == ["point", "state"]


def test_observation_intervals_tagged_by_subject_roundtrip(tmp_path):
    """Coverage that differs per subject is tagged with a `subject` column on the linked TimeIntervals."""
    nwbfile = mock_NWBFile()
    catalogue = make_catalogue()
    events = make_events(catalogue)
    coverage = TimeIntervals(name="observed", description="spans each subject was the focal subject")
    coverage.add_column(name="subject", description="The subject observed in the span.")
    coverage.add_row(start_time=0.0, stop_time=5.0, subject="mouse_1")
    coverage.add_row(start_time=5.0, stop_time=10.0, subject="mouse_2")
    events.observation_intervals = coverage
    behavior_module = nwbfile.create_processing_module("behavior", "behavior")
    behavior_module.add(catalogue)
    behavior_module.add(coverage)
    nwbfile.add_events_table(events)
    path = str(tmp_path / "events.nwb")

    write_nwb(nwbfile, path)
    assert validate(path=path) == []
    with NWBHDF5IO(path, mode="r") as io:
        read_coverage = io.read().events["scoring"].observation_intervals
        assert list(read_coverage["subject"][:]) == ["mouse_1", "mouse_2"]


def test_bouts_derived_from_events_roundtrip(tmp_path):
    """The closed states of a scoring, written as bouts, link back to the record through `source_events`."""
    nwbfile = mock_NWBFile()
    catalogue = make_catalogue()
    events = make_events(catalogue)
    bouts = EthogramBouts(
        name="scoring_bouts",
        description="Closed state occurrences of the scoring",
        labeling_method="manual",
        ethogram=catalogue,
        source_events=events,
        bout_concurrency="concurrent",
    )
    bouts.add_row(start_time=1.0, stop_time=3.0, label="walking")
    behavior_module = nwbfile.create_processing_module("behavior", "behavior")
    behavior_module.add(catalogue)
    nwbfile.add_events_table(events)
    behavior_module.add(bouts)
    path = str(tmp_path / "events.nwb")

    write_nwb(nwbfile, path)
    assert validate(path=path) == []
    with NWBHDF5IO(path, mode="r") as io:
        read_bouts = io.read().processing["behavior"]["scoring_bouts"]
        assert read_bouts.source_events.name == "scoring"
        assert read_bouts.bout_concurrency == "concurrent"
