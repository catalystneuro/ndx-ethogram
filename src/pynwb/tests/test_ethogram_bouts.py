"""pytest tests for the EthogramBouts neurodata type."""

from pynwb import NWBHDF5IO
from pynwb.epoch import TimeIntervals
from pynwb.testing.mock.file import mock_NWBFile

from ndx_ethogram import EthogramBouts


def make_bouts(name="VAME_motifs", labeling_method="automated", source_software="VAME 1.1"):
    """A small single-label (partition-style) EthogramBouts table."""
    bouts = EthogramBouts(
        name=name,
        description="VAME motif bouts (run-length-encoded MotifSeries)",
        labeling_method=labeling_method,
        source_software=source_software,
    )
    bouts.add_row(start_time=0.0, stop_time=1.5, label="7")
    bouts.add_row(start_time=1.5, stop_time=2.0, label="3")
    bouts.add_row(start_time=2.0, stop_time=3.2, label="7")
    return bouts


def write_nwb(nwbfile, path):
    """Write the file to disk; each test reopens it in a fresh IO to read back."""
    with NWBHDF5IO(path, mode="w") as io:
        io.write(nwbfile)


def test_constructor():
    bouts = make_bouts()
    assert bouts.name == "VAME_motifs"
    assert bouts.labeling_method == "automated"
    assert bouts.source_software == "VAME 1.1"
    assert len(bouts) == 3
    assert list(bouts["label"][:]) == ["7", "3", "7"]


def test_label_is_single_text_column():
    """A single required text `label` carries identity: a name for named producers,
    the tool's own cluster id as text for integer-only producers (no separate int code)."""
    bouts = EthogramBouts(name="bb", description="unsupervised motif ids", labeling_method="automated")
    bouts.add_row(start_time=0.0, stop_time=1.0, label="5")
    assert list(bouts["label"][:]) == ["5"]
    assert "label_id" not in bouts.colnames


def test_roundtrip(tmp_path):
    nwbfile = mock_NWBFile()
    bouts = make_bouts()
    nwbfile.create_processing_module("behavior", "behavior").add(bouts)
    path = str(tmp_path / "bb.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r", load_namespaces=True) as io:
        rb = io.read().processing["behavior"]["VAME_motifs"]
        assert type(rb).__name__ == "EthogramBouts"
        assert rb.labeling_method == "automated"
        assert rb.source_software == "VAME 1.1"
        assert list(rb["label"][:]) == ["7", "3", "7"]


def test_multilabel_overlap_roundtrip(tmp_path):
    """Multi-label tools (DeepEthogram/SimBA) produce overlapping bouts of different behaviors."""
    nwbfile = mock_NWBFile()
    bouts = EthogramBouts(
        name="DeepEthogram",
        description="multi-label behavior bouts (annotation)",
        labeling_method="manual",
        annotator="lab annotator",
    )
    bouts.add_row(start_time=1.0, stop_time=3.0, label="chasing")
    bouts.add_row(start_time=2.5, stop_time=4.0, label="Anogenital")  # overlaps on [2.5, 3.0]
    nwbfile.create_processing_module("behavior", "behavior").add(bouts)
    path = str(tmp_path / "bb.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r", load_namespaces=True) as io:
        rb = io.read().processing["behavior"]["DeepEthogram"]
        assert rb.labeling_method == "manual"
        assert rb.annotator == "lab annotator"
        assert list(rb["label"][:]) == ["chasing", "Anogenital"]
        assert rb["start_time"][1] < rb["stop_time"][0]  # overlap survives


def test_observation_intervals_link_roundtrip(tmp_path):
    """A partial annotation records its assessed coverage via the observation_intervals link."""
    nwbfile = mock_NWBFile()
    coverage = TimeIntervals(name="observed", description="frames a human reviewed")
    coverage.add_row(start_time=0.0, stop_time=10.0)
    coverage.add_row(start_time=20.0, stop_time=30.0)
    bouts = EthogramBouts(
        name="DeepEthogram",
        description="partial annotation",
        labeling_method="manual",
        observation_intervals=coverage,
    )
    bouts.add_row(start_time=1.0, stop_time=2.0, label="chasing")
    beh = nwbfile.create_processing_module("behavior", "behavior")
    beh.add(coverage)
    beh.add(bouts)
    path = str(tmp_path / "bb.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r", load_namespaces=True) as io:
        rb = io.read().processing["behavior"]["DeepEthogram"]
        assert rb.observation_intervals is not None
        assert len(rb.observation_intervals) == 2
        assert rb.observation_intervals["stop_time"][0] == 10.0
