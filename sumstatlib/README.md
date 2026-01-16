
## Developer notes

### Data model overview

This library contains Pydantic models which support validating Gene-based GWAS and Copy Number Variant (CNV) GWAS. In the future new types of data might be validated (e.g. SNPs).

If you want to implement a new data model you should:

1. Create a new Python package inside `src/gwascatalog/sumstatlib`
2. Set up annotated types for each field in the new model, importing and reusing types from the `core` package where possible
3. Compose a new data model from the annotated types, inheriting from the abstract `BaseSumstatModel` class
4. Add tests for your new types and model
5. Add your model to `__all__` in the library's root `__init__.py` 

```mermaid
classDiagram
    direction TB

    class GeneSumstatModel {
        <<final>>
        +ensembl_gene_id : EnsemblGeneID | None
        +hgnc_symbol : HGNCGeneSymbol | None

        +base_pair_start : BasePairStart | None
        +base_pair_end : BasePairEnd | None

        +z_score : ZScore | None
        +odds_ratio : OddsRatio | None
        +beta : Beta | None

        +confidence_interval_lower : ConfidenceIntervalLower | None
        +confidence_interval_upper : ConfidenceIntervalUpper | None
    }

    class CNVSumstatModel {
        <<final>>
        +chromosome : Chromosome
        +base_pair_start : BasePairStart
        +base_pair_end : BasePairEnd
        +effect_direction : EffectDirectionField
        +effect_allele : CNVEffectAllele
        +model_type : ModelTypeField
        +n : SampleSizePerVariant | None

        -_assembly : GenomeAssembly
    }

    class BaseSumstatModel {
        <<abstract>>
        +p_value : PValue | None
        +neg_log10_p_value : NegLog10pValue | None

        +validate_semantics() void
        +validate_pvalues(info: ValidationInfo) Self
        +is_neg_log_10_p_value : bool
    }

    BaseSumstatModel <|-- GeneSumstatModel
    BaseSumstatModel <|-- CNVSumstatModel
```
