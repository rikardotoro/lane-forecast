# Demo data source

- **Dataset:** DataCo Smart Supply Chain for Big Data Analysis
- **URL:** https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
- **Licence:** CC0: Public Domain (https://creativecommons.org/publicdomain/zero/1.0/)
- **Retrieved:** 2026-08-12
- **Modifications:** reshaped to this tool's schema (fixed origin `CNSHA`,
  destination `USA` from the largest order country, carrier from shipping mode,
  arrival derived from actual shipping days, carrier ETA from scheduled days),
  filtered to one lane, sampled to 4,000 rows, and the most recent 8% marked
  in-transit by clearing their arrival dates.

This is **order-delivery data, not ocean transit data**. It demonstrates that
the method works on real promised-versus-actual figures. It does not describe
sea lane performance.
