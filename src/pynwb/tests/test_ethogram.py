"""pytest tests for the Ethogram catalogue type and its link from EthogramBouts."""

from pynwb import NWBHDF5IO
from pynwb.testing.mock.file import mock_NWBFile

from ndx_ethogram import Ethogram, EthogramBouts


def make_ethogram(name="ethogram", exclusive=True, with_optional=True):
    """A small behavior catalogue, optionally with native_code + category columns.

    Key columns are `behavior` and `definition` (not `name`/`description`, which are
    reserved DynamicTable attributes).
    """
    eg = Ethogram(name=name, description="behavior catalogue (coding scheme)", exclusive=exclusive)
    rows = [
        ("0", "locomotion"),
        ("1", "grooming"),
        ("2", "rearing"),
    ]
    for index, (behavior, definition) in enumerate(rows):
        row = {"behavior": behavior, "definition": definition}
        if with_optional:
            row["native_code"] = index
            row["category"] = str(index % 2)
        eg.add_row(**row)
    return eg


def write_nwb(nwbfile, path):
    with NWBHDF5IO(path, mode="w") as io:
        io.write(nwbfile)


def test_ethogram_constructor():
    eg = make_ethogram()
    assert eg.name == "ethogram"
    assert eg.exclusive  # single-label partition
    assert len(eg) == 3
    assert list(eg["behavior"][:]) == ["0", "1", "2"]
    assert list(eg["definition"][:]) == ["locomotion", "grooming", "rearing"]
    assert [int(x) for x in eg["native_code"][:]] == [0, 1, 2]
    assert "category" in eg.colnames


def test_ethogram_minimal_columns():
    """behavior + definition are the only required columns; the optional ones may be absent."""
    eg = make_ethogram(with_optional=False)
    assert set(eg.colnames) == {"behavior", "definition"}


def test_ethogram_roundtrip(tmp_path):
    nwbfile = mock_NWBFile()
    eg = make_ethogram(exclusive=False)
    nwbfile.create_processing_module("behavior", "behavior").add(eg)
    path = str(tmp_path / "eg.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r", load_namespaces=True) as io:
        rb = io.read().processing["behavior"]["ethogram"]
        assert type(rb).__name__ == "Ethogram"
        assert not rb.exclusive  # multi-label scheme
        assert list(rb["behavior"][:]) == ["0", "1", "2"]
        assert [int(x) for x in rb["native_code"][:]] == [0, 1, 2]
        assert list(rb["category"][:]) == ["0", "1", "0"]


def test_ethogram_link_roundtrip(tmp_path):
    """EthogramBouts.ethogram links the catalogue; the link resolves on a fresh read."""
    nwbfile = mock_NWBFile()
    eg = make_ethogram()
    bouts = EthogramBouts(name="VAME_motifs", description="motif bouts", labeling_method="automated")
    bouts.add_row(start_time=0.0, stop_time=1.0, label="0")
    bouts.add_row(start_time=1.0, stop_time=2.0, label="2")
    bouts.ethogram = eg
    beh = nwbfile.create_processing_module("behavior", "behavior")
    beh.add(eg)
    beh.add(bouts)
    path = str(tmp_path / "eg.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r", load_namespaces=True) as io:
        rb = io.read().processing["behavior"]["VAME_motifs"]
        assert rb.ethogram is not None
        assert type(rb.ethogram).__name__ == "Ethogram"
        assert list(rb.ethogram["behavior"][:]) == ["0", "1", "2"]


def test_full_output_space_includes_unobserved(tmp_path):
    """The catalogue holds behaviors that never occur in the bouts (the full output space)."""
    nwbfile = mock_NWBFile()
    eg = Ethogram(name="ethogram", description="full scheme", exclusive=True)
    for code, behavior in enumerate(["attack", "investigation", "mount", "other"]):
        eg.add_row(behavior=behavior, definition="", native_code=code)
    bouts = EthogramBouts(name="CalMS21", description="annotation", labeling_method="manual")
    for label in ["investigation", "mount", "other"]:  # only 3 of the 4 occur
        bouts.add_row(start_time=0.0, stop_time=1.0, label=label)
    bouts.ethogram = eg
    beh = nwbfile.create_processing_module("behavior", "behavior")
    beh.add(eg)
    beh.add(bouts)
    path = str(tmp_path / "eg.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r", load_namespaces=True) as io:
        rb = io.read().processing["behavior"]["CalMS21"]
        catalogue = set(rb.ethogram["behavior"][:])
        observed = set(rb["label"][:])
        assert catalogue == {"attack", "investigation", "mount", "other"}
        assert "attack" in catalogue and "attack" not in observed  # unobserved behavior survives


def test_shared_catalogue_roundtrip(tmp_path):
    """Two EthogramBouts may link the same Ethogram object; it is stored once and both resolve."""
    nwbfile = mock_NWBFile()
    eg = make_ethogram()
    motif = EthogramBouts(name="VAME_motifs", description="motif bouts", labeling_method="automated")
    motif.add_row(start_time=0.0, stop_time=1.0, label="0")
    community = EthogramBouts(name="VAME_communities", description="community bouts", labeling_method="automated")
    community.add_row(start_time=0.0, stop_time=2.0, label="1")
    motif.ethogram = eg
    community.ethogram = eg
    beh = nwbfile.create_processing_module("behavior", "behavior")
    beh.add(eg)
    beh.add(motif)
    beh.add(community)
    path = str(tmp_path / "eg.nwb")

    write_nwb(nwbfile, path)
    with NWBHDF5IO(path, mode="r", load_namespaces=True) as io:
        read = io.read().processing["behavior"]
        assert read["VAME_motifs"].ethogram is not None
        assert read["VAME_communities"].ethogram is not None
        # both links resolve to the single stored catalogue
        assert read["VAME_motifs"].ethogram.name == read["VAME_communities"].ethogram.name == "ethogram"
