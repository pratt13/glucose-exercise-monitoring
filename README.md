# README

The purpose of this app is to:

* Represent glucose levels and exercise activities in one place
* Identify patterns, indicators of high/low glucose events
* Use machine learning to suggest food/insulin intake

## Outline

An oversimplified outline of what this app will try to achieve.

```mermaid
flowchart TD
    subgraph G[Glucose Levels]
    L[(Libre)]
    Z[(Zoe)]
    D[(Dexicon)]
    end
    subgraph Exercise
    S[(Strava)]
    SH[(Samsung Health)]
    end
    subgraph App
    V[Data Visualisation]
    F[Forecasting]
    end
    G --> App
    Exercise --> App
    C[(Carb counting\nApp)] --> G
```