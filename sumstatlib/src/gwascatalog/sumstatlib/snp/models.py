from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from gwascatalog.sumstatlib.core.metadata_types import (
    AdjustedCovariates,
    AnalysisSoftware,
    AncestryCategoryField,
    AncestryMethod,
    ArrayInformation,
    ArrayManufacturerField,
    BackgroundTrait,
    CaseControlStudy,
    CaseCount,
    Cohort,
    CohortRef,
    ControlCount,
    CoordinateSystemField,
    CountryOfRecruitment,
    FounderOrGeneticallyIsolatedPopulationDescriptor,
    GenomeAssemblyField,
    GenotypingTechnologyField,
    Imputation,
    ImputationPanel,
    ImputationSoftware,
    IsNeglog10pValue,
    MAFLowerLimit,
    Md5Sum,
    NumberOfIndividuals,
    Readme,
    ReportedTrait,
    SampleAncestry,
    SampleDescription,
    SexField,
    StageField,
    StatisticalModel,
    StudyDescription,
    StudyTag,
    SummaryStatisticsFile,
    VariantCount,
)
from gwascatalog.sumstatlib.core.sumstat_types import (
    BasePairLocation,
    Beta,
    Chromosome,
    ConfidenceIntervalLower,
    ConfidenceIntervalUpper,
    HazardRatio,
    Info,
    NegLog10pValue,
    OddsRatio,
    PValue,
    SampleSizePerVariant,
    StandardError,
)
from gwascatalog.sumstatlib.snp.sumstat_types import (
    EffectAllele,
    EffectAlleleFrequency,
    OtherAllele,
    RefAlleleField,
    RsID,
    VariantId,
)


class SNPStudyMetadata(BaseModel):
    """A single row in the study tab of submission metadata

    See https://www.ebi.ac.uk/gwas/docs/submission-summary-statistics-plus-metadata
    """

    study_tag: StudyTag
    genotyping_technology: list[GenotypingTechnologyField]
    array_manufacturer: list[ArrayManufacturerField] | None
    array_information: ArrayInformation | None
    analysis_software: AnalysisSoftware | None
    imputation: Imputation
    imputation_panel: ImputationPanel | None
    imputation_software: ImputationSoftware | None
    variant_count: VariantCount
    statistical_model: StatisticalModel | None
    study_description: StudyDescription | None
    adjusted_covariates: list[AdjustedCovariates] | None
    reported_trait: ReportedTrait
    background_trait: BackgroundTrait | None
    summary_statistics_file: SummaryStatisticsFile | Literal["NR"]
    md5_sum: Md5Sum | Literal["NR"]
    readme: Readme | None
    summary_statistics_assembly: GenomeAssemblyField
    neg_log_10_p_values: IsNeglog10pValue | None
    maf_lower_limit: MAFLowerLimit | None
    cohorts: list[Cohort] | None
    cohort_ref: list[CohortRef] | None
    sex: SexField | None
    coordinate_system: CoordinateSystemField


class SNPSampleMetadata(BaseModel):
    """A single row in the sample tab of submission metadata

    See https://www.ebi.ac.uk/gwas/docs/submission-summary-statistics-plus-metadata
    """

    study_tag: StudyTag
    stage: StageField
    number_of_individuals: NumberOfIndividuals
    case_control_study: CaseControlStudy
    number_of_cases: CaseCount | None
    number_of_controls: ControlCount | None
    sample_description: SampleDescription | None
    ancestry_category: list[AncestryCategoryField]
    sample_ancestry: SampleAncestry | None
    founder_or_genetically_isolated_population_descriptor: (
        list[FounderOrGeneticallyIsolatedPopulationDescriptor] | None
    )
    ancestry_method: list[AncestryMethod]
    country_of_recruitment: list[CountryOfRecruitment] | None


class SNPSumStat(BaseModel):
    """A single row in a SNP summary statistics table."""

    chromosome: Chromosome
    base_pair_location: BasePairLocation
    effect_allele: EffectAllele
    other_allele: OtherAllele
    beta: Beta | None
    odds_ratio: OddsRatio | None
    hazard_ratio: HazardRatio | None
    standard_error: StandardError | None
    effect_allele_frequency: EffectAlleleFrequency
    p_value: PValue | None
    neg_log_10_p_value: NegLog10pValue | None
    variant_id: VariantId | None
    rsid: RsID | None
    info: Info | None
    ci_lower: ConfidenceIntervalLower | None
    ci_upper: ConfidenceIntervalUpper | None
    ref_allele: RefAlleleField | None
    n: SampleSizePerVariant | None


class SNPSubmission(BaseModel):
    studies: list[SNPStudyMetadata]
    samples: list[SNPSampleMetadata]
    sumstats: list[SNPSumStat]

    # TODO: add any sumstat validation rules here which depend on metadata
    # e.g. 0 p-values ->  requires analysis_software declared
