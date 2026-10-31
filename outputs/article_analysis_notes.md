# Analysis notes for the discovery article

These notes retain the qualifications behind the short article. They are part of its evidence, alongside the complete equity report, case ledger and methodology. The article's opening summaries describe observed map correspondence and supported location discrepancies; they do not establish unequal confirmed operating-station error rates.

## What a nearby listing means

The comparison asks whether a supplied Overture place has a primary or alternate fire_department category within 100 m of an OpenStreetMap fire-station geometry. A nearby compatible category does not independently certify the same entity. An unmatched site can reflect a displaced listing, a missing listing, another category, or an incomplete/stale OSM comparator. Neither the unmatched count nor its rural/urban difference is a count of communities without service.

## The rural gap becomes smaller after adjustment

The region-only model estimates 23.1 percentage points lower correspondence at rural sites, among 1,371 sites with known rurality. Adding population, observed station supply, SVI, wildfire exposure, heat and drought gives a 4.8-point rural shortfall among 1,358 sites with complete model inputs. Its 95% county-clustered interval extends from a 3.6-point rural advantage to a 13.1-point shortfall. Adding map-record features gives a 5.3-point shortfall; including population density gives 2.7 points. Both intervals also include zero. Missing data changes the model sample slightly.

The observed rural/urban gap appears in each completed region, but a clear independent rural effect is not established. Adjustment describes associations and does not identify which community characteristics cause map discrepancies. Matched comparisons have limited overlap, residual imbalance in the initial set, and sparse strict subsets; the complete equity report documents them.

## What the wildfire chart shows

The descriptive exposure chart was added on 27 October 2026 using existing site outcomes and tract ranks. All 12 region-by-exposure groups are disclosed in wildfire_story_exposure_groups.csv, with rural/urban composition in wildfire_story_group_composition.csv. It introduces no new model or inferential test. Exposure groups are defined using the existing within-region ranks of all supplied tracts, not equal-sized groups of station sites.

The raw groups differ substantially in rurality. All lowest-exposure-quarter sites in this sample are urban. In Northern California, 180 of 198 highest-quarter sites are rural. Their 91% versus 38% correspondence rates cannot, by themselves, identify a separate exposure effect. Adjusting with a model does not create directly comparable rural and urban observations where those observations are absent.

## What the adjusted wildfire estimate means

The existing model estimates 14.4 percentage points lower local correspondence for a move from the regional 25th to 75th exposure percentile, after community and map-record adjustments. The article expresses that model association as about 14 fewer matches per 100 sites. The 95% county-clustered interval is 8.6–20.2 points lower. This is an expected difference in correspondence, not 14 independently verified missing stations. The fixed-rank contrast differs from the average difference between the chart's exposure groups.

The model includes 1,358 sites in 120 counties and accounts for region, rurality, population, mapped-site supply, social vulnerability, heat, drought, polygon/point representation, GNIS tags, record age, naming and station numbering. The density sensitivity gives a 12.4-point shortfall. Changing the radius to 50 m gives 15.7 points; 200 m gives 13.1 points. Other record-quality sensitivities retain the negative association. These are exploratory associations rather than multiplicity-adjusted confirmatory findings.

The regional association is clearest in Northern California and Maricopa. Eastern Washington's estimate has a wide interval; Eastern Oklahoma's interval includes zero. A universally established independent exposure effect across every region is not claimed. The evidence does not show a consistent additional social-vulnerability or tribal-overlap penalty across regions.

The exposure variable is a tract landscape Exposure Type average related to proximity to burnable vegetation. It is distinct from annual burn probability, personal or housing-weighted exposure, current fire danger and risk at the precise station site. Regional ranks compare places within their supplied region, not absolute exposure across states. See the USFS definition linked in the equity report.

## What the case checks establish

All 11 unique-name discrepancies above 500 m were reviewed: three supported location errors, five distinct-facility pairings and three unresolved. Broken Arrow Station 3 is a supported urban error. Porum and Westport illustrate local failures within wildfire-exposed, socially vulnerable tract contexts; they are selected examples, not a random sample for estimating group error prevalence.

Porum's county contract address and the Westport department address support their local sites. Overture retains local building geometry while the named department listings are elsewhere. Building retention can share upstream OSM data and does not independently establish snapshot-time operations. The county address layer used for Westport warns of errors and inconsistencies; the department's own address provides additional corroboration. No site visit or operating-station census was performed. Source-specific limitations remain in the case audit.

Tract populations are 2020 census context, not the populations of station catchments. SVI describes tract-level relative social vulnerability, not every resident. Tribal-area intersection is area, not the identity of residents; statistical and legal geographies differ.

## Potential consequences and historical context

The resource-search and meeting-point scenarios are hypothetical. We have no observation of dispatchers using Overture, a crew travelling to either listing, a response delay or anyone being harmed. A 5 km local search can exclude Porum's same-name listing 44.4 km away, but we do not claim that every other fire listing is absent. Westport's position can change within one tract without changing its facility total. Neither example proves a deployed score or real response workflow failed.

The 14 January 2007 outage report was reviewed as historical context but removed from the short article because it does not establish a mapping-related response failure. It predates the 2026 map snapshot and is not evidence of mapping-related harm. Westport's reported 14 volunteers and 190-square-mile area describe its public website when checked on 24 October 2026, not independently established August staffing.

## Scope and reproducibility

The complete comparison covers Eastern Oklahoma, Eastern Washington, Maricopa and surrounding areas, and Northern California. Washington is supplementary to the completed leaderboard regions. Texas's historical extraction is incomplete and contributes no rates. OSM is historical state 2026-08-01; Overture is release 2026-08-19.0. Current case sources were checked on 24 October. No removed reference layers or new leaderboard targets were used.

The [equity report](equity_followup_report.md), [case audit](comprehensive_case_audit.md) and [methodology](methodology.md) retain all estimates, denominators, sensitivity checks, source caveats and reproduction details. Descriptive chart counts reconcile with the 1,372 original sites.
