
## Developer notes

### Data model overview

This library contains Pydantic models which support validating Gene-based GWAS and Copy Number Variant (CNV) GWAS. In the future new types of data might be validated (e.g. SNPs).

```mermaid
classDiagram
    direction TB

    class BaseSumstatModel {
        <<abstract>>

        %% configuration (conceptual)
        +p_value : PValue | None
        +neg_log10_p_value : NegLog10pValue | None

        +z_score : ZScore | None
        +odds_ratio : OddsRatio | None
        +beta : Beta | None
        +hazard_ratio : HazardRatio | None
        +standard_error : StandardError | None

        +confidence_interval_lower : ConfidenceIntervalLower | None
        +confidence_interval_upper : ConfidenceIntervalUpper | None

        +n : SampleSizePerVariant | None

        --
        -_primary_effect_size : Literal["beta","z_score","hazard_ratio","odds_ratio"] | None

        -_allow_zero_pvalues : bool
    }

    class CNVSumstatModel {
        <<final>>

        +MIN_RECORDS : int
        +FIELD_MAP : Mapping[str,int]
        +VALID_FIELD_NAMES : list[str]

        +chromosome : Chromosome
        +base_pair_start : BasePairStart
        +base_pair_end : BasePairEnd
        +statistical_model_type : StatisticalModelTypeField

        --
        -_assembly : GenomeAssembly
    }

    class GeneSumstatModel {
        <<final>>

        +MIN_RECORDS : int
        +FIELD_MAP : Mapping[str,int]
        +VALID_FIELD_NAMES : list[str]

        +ensembl_gene_id : EnsemblGeneID | None
        +hgnc_symbol : HGNCGeneSymbol | None

        +chromosome : Chromosome | None
        +base_pair_start : BasePairStart | None
        +base_pair_end : BasePairEnd | None
    }

    BaseSumstatModel <|-- GeneSumstatModel
    BaseSumstatModel <|-- CNVSumstatModel
```

### Implementing a new data model

If you want to implement a new data model you should:

1. Create a new Python package inside `src/gwascatalog/sumstatlib`
2. Set up annotated types for each field in the new model, importing and reusing types from the `core` package where possible
3. Compose a new data model from the annotated types, inheriting from the abstract `BaseSumstatModel` class
4. Add tests for your new types and model
5. Add your model to `__all__` in the library's root `__init__.py` 

