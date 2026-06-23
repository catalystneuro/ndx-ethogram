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
        version="""0.1.0""",
        doc="""NWB extension for ethograms: a tool-agnostic behavior timeline (EthogramBouts, labeled time intervals, one row per bout, a TimeIntervals subclass) plus the behavior catalogue / coding scheme it draws labels from (Ethogram, a DynamicTable). Produced from pose-estimation post-processing tools (VAME, keypoint-MoSeq, B-SOiD, DeepEthogram, SimBA) and manual coders (CalMS21, CRIM13).""",
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
    ns_builder.include_type("ImageSeries", namespace="core")
    ns_builder.include_type("NWBDataInterface", namespace="core")
    ns_builder.include_type("VectorData", namespace="hdmf-common")
    ns_builder.include_type("DynamicTable", namespace="hdmf-common")  # parent of the Ethogram catalogue
    # typed pose link target
    ns_builder.include_namespace("ndx-pose")
    ns_builder.include_type("PoseEstimation", namespace="ndx-pose")

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
            "Holds only durative (state) behaviors; instantaneous point behaviors belong in an EventsTable."
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
                doc=(
                    "Spans over which the labels were assessed (partial-annotation inputs only). Within "
                    "them, absence of a bout means the behavior was absent; outside, unobserved. Omitted "
                    "means assessed throughout (full coverage). A plain core TimeIntervals; not invalid_times."
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
            "DynamicTable that EthogramBouts (and a future point-behavior EthogramEvents) reference via "
            "their optional `ethogram` link; a bout's text `label` matches this table's `name` column. "
            "Holds per-type, occurrence-invariant metadata the per-bout table cannot: the complete "
            "repertoire, the state/point kind, the tool's native code, and the hierarchy grouping."
        ),
        attributes=[
            NWBAttributeSpec(
                name="exclusive",
                dtype="bool",
                required=False,
                doc=(
                    "True if the scheme is a single-label partition (mutually exclusive behaviors, e.g. "
                    "VAME motifs, keypoint-MoSeq syllables, CalMS21); False if independent multi-label "
                    "behaviors can co-occur (DeepEthogram, SimBA). Tells a consumer whether overlapping "
                    "EthogramBouts rows are expected."
                ),
            ),
        ],
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
                    "'state' (durative -> EthogramBouts) or 'point' (instantaneous -> a future "
                    "EthogramEvents). Optional; all current pose-segmentation tools emit only 'state'."
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
        ],
    )

    new_data_types = [ethogram, behavioral_bouts]

    output_dir = str((Path(__file__).parent.parent.parent / "spec").absolute())
    export_spec(ns_builder, new_data_types, output_dir)


if __name__ == "__main__":
    main()
