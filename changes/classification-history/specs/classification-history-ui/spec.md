## ADDED Requirements

### Requirement: Classification history page
The system SHALL provide a "分类历史" page at route `/classification-history` that displays the current user's classification records in a table format.

#### Scenario: Access history page from navigation
- **WHEN** user clicks "分类历史" menu item in the navigation bar
- **THEN** system navigates to `/classification-history` and displays the classification history page

#### Scenario: Access history page from home
- **WHEN** user clicks "分类历史" feature card on the home page
- **THEN** system navigates to `/classification-history` and displays the classification history page

### Requirement: History table displays full summary text
The summary column in the history table SHALL display the complete summary text without truncation.

#### Scenario: Long summary displayed in full
- **WHEN** a classification record has a summary of 500 characters
- **THEN** the table row displays all 500 characters in the summary column without "..." truncation

### Requirement: Summary keyword highlighting
When the user filters by summary keyword, the matching keywords in the summary column SHALL be visually highlighted. The system SHALL escape HTML in the summary text before highlighting to prevent XSS.

#### Scenario: Keyword highlighted in summary
- **WHEN** user filters with summary keyword "成像" and a record's summary contains "一种基于...成像...的方法"
- **THEN** the summary column displays the full text with "成像" wrapped in `<mark>` tags, rendered with highlighted styling

#### Scenario: HTML in summary text is escaped
- **WHEN** a record's summary contains `<script>alert(1)</script>` and user filters with any keyword
- **THEN** the summary text is displayed as literal text, the script tag is NOT executed

### Requirement: Multi-condition filtering
The history page SHALL provide filter controls for predicted category (dropdown), time range (date picker), source type (dropdown), and summary keyword (text input). Filtering is triggered by clicking the "查询" button.

#### Scenario: Filter with predicted category
- **WHEN** user selects "医用成像器械" from category dropdown and clicks "查询"
- **THEN** table displays only records with pred_label "医用成像器械"

#### Scenario: Reset filters
- **WHEN** user clicks "重置" button
- **THEN** all filter controls are cleared and table displays all records for the current user

### Requirement: Source type display mapping
The source column SHALL display "单条输入" when source is "single" and "批量导入" when source is "batch".

#### Scenario: Single source display
- **WHEN** a record has source="single"
- **THEN** the source column displays "单条输入"

#### Scenario: Batch source display
- **WHEN** a record has source="batch"
- **THEN** the source column displays "批量导入"

### Requirement: Detail dialog with chart
Clicking "详情" in the operation column SHALL open a dialog displaying the full summary text and an ECharts probability distribution chart using the `ChartVisualization` component.

#### Scenario: Open detail dialog
- **WHEN** user clicks "详情" for a record
- **THEN** a dialog opens showing the complete summary text and a bar chart of the top 10 category probabilities from the record's top_categories JSON data

### Requirement: Route authentication guard
The `/classification-history` route SHALL require authentication. Unauthenticated users SHALL be redirected to the login page.

#### Scenario: Unauthenticated access
- **WHEN** unauthenticated user navigates to `/classification-history`
- **THEN** system redirects to `/login` with redirect query parameter
