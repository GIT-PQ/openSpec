## ADDED Requirements

### Requirement: Reusable chart component
The system SHALL provide a `ChartVisualization` Vue component that renders an ECharts horizontal bar chart showing the top 10 category probabilities. The component SHALL accept a `categories` prop (array of objects with `name` and `probability` fields).

#### Scenario: Render chart from categories data
- **WHEN** the component receives `categories` prop with 22 category objects
- **THEN** it renders a horizontal bar chart showing the top 10 categories sorted by probability descending, with bars colored by probability thresholds (>=0.5 green, >=0.3 orange, >=0.1 red, <0.1 default)

#### Scenario: Chart responds to window resize
- **WHEN** the browser window is resized
- **THEN** the chart automatically adjusts its dimensions to fit the container

### Requirement: Replace inline chart code in PatentClassification
The `PatentClassification.vue` component SHALL use the `ChartVisualization` component instead of its current inline ECharts code (initChart, updateChart, renderChart methods). After refactoring, the single classification feature SHALL behave identically.

#### Scenario: Classification result rendering unchanged
- **WHEN** user classifies a patent summary after the refactoring
- **THEN** the result chart displays identically to before the refactoring (same colors, same layout, same top 10, same tooltip format)
