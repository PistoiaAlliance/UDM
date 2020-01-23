# UDM XML Schema Change Log

## Changes 5.0.1 to 6.0.0

1. Introduced controlled vocabularies (in separate *.xsd files) for
   * Countries (based on ISO 3166)
   * Units (based on 2019.09 Allotrope version of QUDT)
     * Amount of substance
     * Mass
     * Mass per volume
     * Molar concentration
     * Pressure or stress
     * Temperature
     * Time
     * Volume
   * Analytical methods (based on 2019.09 Allotrope Foundation Taxonomies)

1. New entity: `ANALYTICAL_DATA` and related sub-elements: `EXPERIMENT`,
   `CREATION_DATE`, `SYSTEM`, `SUMMARY`, `DATA`, `DATA_URL`.

   ```xml
<ANALYTICAL_DATA>
  <EXPERIMENT method="nuclear magnetic resonance spectroscopy">
    <CREATION_DATE>2019-01-23</CREATION_DATE>
    <DATA_URL>https://our-lims/record-21312</DATA_URL>
  </EXPERIMENT>
</ANALYTICAL_DATA>
   ```

1. New entity: `ORGANISATION` containing `NAME` (required), `ADDRESS`,
   `COUNTRY`, `URL`, `EMAIL`, `PHONE`, `COMMENT`.

1. New entity: `ORGANISATIONS` to group `ORGANISATION`s.

1. Enhanced `AUTHOR` entity to include `NAME` (required), `EMAIL`, `PHONE`,
   `ORGANISATION`.

1. New entity: `AUTHORS` to group `AUTHOR`s.

1. `RESP_SCIENTIST` and `SCIENTIST` contain the same elements as `AUTHOR`.

1. New entity: `SAMPLE` containing `SAMPLE_ID` (required), `SAMPLE_REF`,
   `SAMPLE_MASS`, `BATCH_ID`, `AMOUNT`, `PURITY`, `BARCODE`, `ANALYTICAL_DATA`.

1. New entity: `SAMPLES` to group `SAMPLE`s.

1. New placeholder entity `EHS` for future use.

1. The `DATE` field of `COPYRIGHT` renamed to `YEAR`,
   e.g. `/UDM/LEGAL/COPYRIGHT/DATE` becomes `/UDM/LEGAL/COPYRIGHT/YEAR`.

1. Type of `/UDM/CITATIONS/CITATION/PATENT_PUB_DATE` changed to `xs:date`.

1. Type of `/UDM/CITATIONS/CITATION/YEAR` changed to `xs:positiveInteger`.

1. `MOLECULE` can be specified inside `REACTANT`, `PRODUCT`, `SOLVENT`,
   `CATALYST` and `REAGENT` in addition or instead of the `MOLECULES` block.

1. Removed the `ID` attribute from `REACTANT`, `PRODUCT`, `SOLVENT`,
   `CATALYST` and `REAGENT`, use `<MOLECULE MOD_ID="..." />` instead.


## TODO Add changes introduced in 5.0.x versions
