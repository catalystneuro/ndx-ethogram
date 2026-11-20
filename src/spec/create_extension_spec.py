# -*- coding: utf-8 -*-
from pathlib import Path

from pynwb.spec import (
    NWBNamespaceBuilder,
    export_spec,
    NWBGroupSpec,
    NWBDatasetSpec,
    NWBAttributeSpec,
    NWBLinkSpec,
)


def main():
    ns_builder = NWBNamespaceBuilder(
        name="""ndx-ethogram""",
        version="""0.2.0""",
        doc=(
            "NWB extension for ethograms: a tool-agnostic behavior timeline (EthogramBouts, labeled time "
            "intervals, one row per bout, a TimeIntervals subclass), the record of a manual scoring "
            "(EthogramEvents, one row per scored occurrence, an EventsTable subclass), and the behavior "
            "catalogue / coding scheme both draw labels from (Ethogram, a DynamicTable). Produced from "
            "pose-estimation post-processing tools (VAME, keypoint-MoSeq, B-SOiD, DeepEthogram, SimBA) and "
            "manual coders (BORIS, CalMS21, CRIM13)."
        ),
        author=[
            "Heberto Mayorquin",
        ],
        contact=[
            "h.mayorquin@gmail.com",
        ],
    )
    ns_builder.include_namespace("core")
    # parent + link targets from core / hdmf-common
    ns_builder.include_type("TimeIntervals", namespace="core")
    ns_builder.include_type("EventsTable", namespace="core")  # parent of EthogramEvents
    ns_builder.include_type("ImageSeries", namespace="core")
    ns_builder.include_type("NWBDataInterface", namespace="core")
    ns_builder.include_type("VectorData", namespace="hdmf-common")
    ns_builder.include_type("VectorIndex", namespace="hdmf-common")  # ragged catalogue columns
    ns_builder.include_type("DynamicTable", namespace="hdmf-common")  # parent of the Ethogram catalogue
    # typed pose link target
    ns_builder.include_namespace("ndx-pose")
    ns_builder.include_type("PoseEstimation", namespace="ndx-pose")

    OBSERVATION_INTERVALS_DOC = (
        "Spans over which the labels were assessed (partial-annotation inputs only). Within them, absence "
        "of {row} means the behavior was absent; outside, unobserved. Omitted means assessed throughout "
        "(full coverage). A plain core TimeIntervals; not invalid_times. When coverage differs by subject "
        "or by behavior (focal sampling, a behavior scored in part of the session), each row of the linked "
        "TimeIntervals is tagged with a `subject` or a `label` column; a row without the column covers every "
        "subject and every behavior."
    )

    ethogram_events = NWBGroupSpec(
        neurodata_type_def="EthogramEvents",
        neurodata_type_inc="EventsTable",
        doc=(
            "The record of a behavioral scoring: one row per scored occurrence, drawn from an Ethogram "
            "catalogue. Holds point behaviors, closed state occurrences and state occurrences that never "
            "closed. Each row has the inherited `timestamp` (the onset) and `duration`: the length of a "
            "closed state occurrence, NaN for a point behavior or a state that never closed. The linked "
            "catalogue's `behavior_type` tells the two NaN cases apart. A coder's free-text comment on an "
            "occurrence goes in the inherited `annotation` column. One table holds every behavior of one "
            "coding scheme, since all its rows share the same columns. Modifiers, the answers a coder "
            "records with an occurrence, go in one ragged text column per modifier slot, named by the "
            "producer; the catalogue's `modifiers` column says which of them a behavior writes into. When "
            "an occurrence closes with different answers or a different comment than it opened with, the "
            "closing ones go in a column of the same name prefixed `stop_` (for example `stop_annotation`), "
            "written only when some occurrence in the table changed."
        ),
        attributes=[
            NWBAttributeSpec(
                name="labeling_method",
                dtype="text",
                doc=(
                    "How the occurrences were produced: 'manual' (a human scored the video), 'automated' "
                    "(an algorithm), or 'curated' (human-reviewed model output)."
                ),
            ),
            NWBAttributeSpec(
                name="source_software",
                dtype="text",
                required=False,
                doc="Producing tool and version, e.g. 'BORIS 8.27'.",
            ),
            NWBAttributeSpec(
                name="annotator",
                dtype="text",
                required=False,
                doc="The human or lab who scored the occurrences.",
            ),
            NWBAttributeSpec(
                name="parameters",
                dtype="text",
                required=False,
                doc="Optional JSON-encoded provenance: settings of the producing tool.",
            ),
        ],
        datasets=[
            NWBDatasetSpec(
                name="label",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc="The behavior of each occurrence (required); matches a row of the catalogue's `behavior` column.",
            ),
            NWBDatasetSpec(
                name="subject",
                neurodata_type_inc="VectorData",
                dtype="text",
                quantity="?",
                doc=(
                    "Who the occurrence is attributed to, for scorings of several subjects. An empty string "
                    "means the coder attributed the occurrence to no subject."
                ),
            ),
        ],
        links=[
            NWBLinkSpec(
                name="ethogram",
                target_type="Ethogram",
                doc=(
                    "The behavior catalogue (coding scheme) the occurrences draw their labels from (required). "
                    "Its `behavior_type` column must be filled, since it is what tells a point behavior from a "
                    "state that never closed."
                ),
            ),
            NWBLinkSpec(
                name="source_video",
                target_type="ImageSeries",
                quantity="?",
                doc="The behavioral video the occurrences were scored on.",
            ),
            NWBLinkSpec(
                name="observation_intervals",
                target_type="TimeIntervals",
                quantity="?",
                doc=OBSERVATION_INTERVALS_DOC.format(row="an occurrence"),
            ),
        ],
    )

    behavioral_bouts = NWBGroupSpec(
        neurodata_type_def="EthogramBouts",
        neurodata_type_inc="TimeIntervals",
        doc=(
            "A curated, tool-agnostic ethogram stored as labeled behavioral bouts: one row per bout "
            "(a continuous interval of a single behavior), inheriting start_time and stop_time from "
            "TimeIntervals. A downstream-oriented, lossy-by-design product of behavioral "
            "segmentation/classification tools (VAME motifs, keypoint-MoSeq syllables, B-SOiD clusters, "
            "DeepEthogram/SimBA behaviors); the tool's faithful native output lives in its own extension "
            "and is referenced via the generic `source` link. Overlapping behaviors are overlapping rows. "
            "Holds only durative (state) behaviors; instantaneous point behaviors belong in an EthogramEvents. "
            "A table with a `source_events` link is a view of the closed state occurrences of that "
            "EthogramEvents record, so a reader counts one table or the other, not both."
        ),
        attributes=[
            NWBAttributeSpec(
                name="labeling_method",
                dtype="text",
                doc=(
                    "How the labels were produced: 'manual' (a human scored the video), 'automated' "
                    "(an algorithm), or 'curated' (human-reviewed model output). Required so annotation "
                    "and prediction tables are never indistinguishable."
                ),
            ),
            NWBAttributeSpec(
                name="source_software",
                dtype="text",
                required=False,
                doc="Producing tool and version for 'automated'/'curated' output, e.g. 'VAME 1.1'.",
            ),
            NWBAttributeSpec(
                name="annotator",
                dtype="text",
                required=False,
                doc="The human or lab who produced 'manual'/'curated' labels.",
            ),
            NWBAttributeSpec(
                name="parameters",
                dtype="text",
                required=False,
                doc="Optional JSON-encoded provenance: key hyperparameters (n_cluster, time_window, kappa, ...).",
            ),
            NWBAttributeSpec(
                name="bout_concurrency",
                dtype="text",
                required=False,
                doc=(
                    "How bouts of one subject relate in time. 'partition': one bout at every observed "
                    "instant, so the bouts tile the observed time (VAME motifs, keypoint-MoSeq syllables, "
                    "B-SOiD groups, CalMS21). 'disjoint': never more than one bout at once, gaps allowed. "
                    "'concurrent': bouts may overlap (DeepEthogram, SimBA, most manual coding schemes). "
                    "Absent means unknown. Holds per subject: bouts of different subjects may always overlap."
                ),
            ),
        ],
        datasets=[
            NWBDatasetSpec(
                name="label",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc=(
                    "Behavior/motif/syllable/cluster identity for each bout (required). A single "
                    "text column: a human-readable name for named producers (DeepEthogram, SimBA, "
                    "CalMS21, CRIM13 behaviors); for integer-only unsupervised producers (VAME, "
                    "keypoint-MoSeq, B-SOiD) it is the tool's own cluster id rendered as text "
                    "(e.g. '7'). Text rather than a separate integer code because unsupervised "
                    "cluster ids are arbitrary and run-specific, not a stable canonical identity, "
                    "so a parallel integer key earns nothing the string does not already carry."
                ),
            ),
        ],
        links=[
            NWBLinkSpec(
                name="source",
                target_type="NWBDataInterface",
                quantity="?",
                doc=(
                    "The producing faithful object these bouts were derived from (e.g. a VAMEProject or "
                    "MotifSeries). Generic target keeps ndx-ethogram tool-agnostic (no dependency "
                    "on any tool-faithful extension)."
                ),
            ),
            NWBLinkSpec(
                name="source_pose",
                target_type="PoseEstimation",
                quantity="?",
                doc="The upstream ndx-pose PoseEstimation these bouts were derived from (pose-based tools).",
            ),
            NWBLinkSpec(
                name="source_video",
                target_type="ImageSeries",
                quantity="?",
                doc="The behavioral video the bouts align to.",
            ),
            NWBLinkSpec(
                name="observation_intervals",
                target_type="TimeIntervals",
                quantity="?",
                doc=OBSERVATION_INTERVALS_DOC.format(row="a bout"),
            ),
            NWBLinkSpec(
                name="source_events",
                target_type="EthogramEvents",
                quantity="?",
                doc=(
                    "The EthogramEvents record these bouts were derived from, for a manual scoring whose "
                    "closed state occurrences are also written as bouts. The bouts are then a view of that "
                    "record: count one table or the other, not both."
                ),
            ),
            NWBLinkSpec(
                name="ethogram",
                target_type="Ethogram",
                quantity="?",
                doc=(
                    "The behavior catalogue (coding scheme) these bouts draw their labels from; a bout's "
                    "`label` matches a row's `behavior` column. Optional: the text `label` is self-sufficient, "
                    "the catalogue adds the full output space and per-type metadata when present."
                ),
            ),
        ],
    )

    ethogram = NWBGroupSpec(
        neurodata_type_def="Ethogram",
        neurodata_type_inc="DynamicTable",
        doc=(
            "The behavior catalogue / coding scheme (the classical ethogram): one row per behavior TYPE, "
            "including types that did not occur this session (the full output space). A standalone "
            "DynamicTable that EthogramBouts and EthogramEvents reference via their `ethogram` link; a "
            "row's text `label` matches this table's `behavior` column. "
            "Holds per-type, occurrence-invariant metadata the per-bout table cannot: the complete "
            "repertoire, the state/point kind, the tool's native code, and the hierarchy grouping."
        ),
        datasets=[
            NWBDatasetSpec(
                name="behavior",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc=(
                    "Behavior name / id, the join key an EthogramBouts `label` matches (required). A "
                    "human-readable name for named producers; the tool's own cluster/motif/syllable id "
                    "as text (e.g. '7') for integer-only unsupervised producers. (Not named 'name' "
                    "because that collides with the DynamicTable's own name attribute.)"
                ),
            ),
            NWBDatasetSpec(
                name="definition",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc=(
                    "Operational definition of the behavior (required; may be brief, or a placeholder "
                    "for unsupervised cluster ids that have no a-priori meaning). (Not named "
                    "'description' because that collides with the DynamicTable's own description.)"
                ),
            ),
            NWBDatasetSpec(
                name="behavior_type",
                neurodata_type_inc="VectorData",
                dtype="text",
                quantity="?",
                doc=(
                    "'state' (durative) or 'point' (instantaneous). Optional, except when an EthogramEvents "
                    "links this catalogue: a NaN duration there marks either a point behavior or a state "
                    "that never closed, and only this column tells them apart."
                ),
            ),
            NWBDatasetSpec(
                name="native_code",
                neurodata_type_inc="VectorData",
                dtype="int",
                quantity="?",
                doc=(
                    "The producing tool's own integer id for this behavior (a VAME motif number, a "
                    "CalMS21 class id), recorded once here rather than per bout. Optional; absent for "
                    "named producers that supply no native integer."
                ),
            ),
            NWBDatasetSpec(
                name="category",
                neurodata_type_inc="VectorData",
                dtype="text",
                quantity="?",
                doc=(
                    "Hierarchy / grouping for this behavior (a VAME community, a BORIS behavioral "
                    "category). The normalized home of the motif->community mapping. Optional."
                ),
            ),
            NWBDatasetSpec(
                name="modifiers",
                neurodata_type_inc="VectorData",
                dtype="text",
                quantity="?",
                doc=(
                    "The modifier slots of each behavior: for each slot, the name of the EthogramEvents column "
                    "its answers are written to. Ragged, empty for a behavior with no modifiers. Optional."
                ),
            ),
            NWBDatasetSpec(
                name="modifiers_index",
                neurodata_type_inc="VectorIndex",
                quantity="?",
                doc="Index into `modifiers`, one entry per behavior.",
            ),
            NWBDatasetSpec(
                name="modifier_values",
                neurodata_type_inc="VectorData",
                dtype="text",
                quantity="?",
                doc=(
                    "The menu of values each slot in `modifiers` offers, in the same order. Doubly ragged: a "
                    "list of values per slot, a list of slots per behavior. Empty for a slot with no menu, "
                    "such as a free-text or numeric answer. Optional."
                ),
            ),
            NWBDatasetSpec(
                name="modifier_values_index",
                neurodata_type_inc="VectorIndex",
                quantity="?",
                doc="Index into `modifier_values`, one entry per modifier slot.",
            ),
            NWBDatasetSpec(
                name="modifier_values_index_index",
                neurodata_type_inc="VectorIndex",
                quantity="?",
                doc="Index into `modifier_values_index`, one entry per behavior.",
            ),
            NWBDatasetSpec(
                name="excludes",
                neurodata_type_inc="VectorData",
                dtype="text",
                quantity="?",
                doc=(
                    "The behaviors that starting this behavior terminates, as values of this table's "
                    "`behavior` column (a BORIS exclusion matrix; members of an EthoVision mutually exclusive "
                    "group each exclude the others). Ragged, empty for a behavior that terminates none. "
                    "Optional."
                ),
            ),
            NWBDatasetSpec(
                name="excludes_index",
                neurodata_type_inc="VectorIndex",
                quantity="?",
                doc="Index into `excludes`, one entry per behavior.",
            ),
        ],
    )

    new_data_types = [ethogram, ethogram_events, behavioral_bouts]

    output_dir = str((Path(__file__).parent.parent.parent / "spec").absolute())
    export_spec(ns_builder, new_data_types, output_dir)


if __name__ == "__main__":
    main()
