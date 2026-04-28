## ADDED Requirements

### Requirement: Batch ID column in classification history table
The classification history table SHALL display a "批次ID" column showing the complete batchId value (36-character UUID) for each record.

#### Scenario: Batch classification record shows batch ID
- **WHEN** a record with source='batch' is displayed in the table
- **THEN** the batchId column shows the complete 36-character UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")

#### Scenario: Single classification record shows placeholder
- **WHEN** a record with source='single' (no batchId) is displayed in the table
- **THEN** the batchId column shows "-" to indicate no batch association

#### Scenario: Column width accommodates full UUID
- **WHEN** the table renders
- **THEN** the batchId column has sufficient width (approximately 280px) to display the full UUID without truncation

### Requirement: Batch ID filter input in classification history page
The classification history page SHALL provide a batchId filter input field in the filter area, allowing users to filter records by exact batchId match.

#### Scenario: User filters by batch ID
- **WHEN** user enters a batchId value (e.g., "550e8400-e29b-41d4-a716-446655440000") in the batchId input field and clicks "查询"
- **THEN** the table displays only records where batchId equals the entered value

#### Scenario: Batch ID filter combined with other filters
- **WHEN** user enters batchId along with other filter conditions (predLabel, source, etc.) and clicks "查询"
- **THEN** the table displays records matching ALL specified conditions including the exact batchId match

#### Scenario: Empty batchId filter returns all records
- **WHEN** user leaves the batchId input field empty and clicks "查询"
- **THEN** the batchId filter is ignored and records are filtered by other specified conditions only

#### Scenario: Reset clears batchId filter
- **WHEN** user clicks "重置" button
- **THEN** the batchId input field is cleared along with all other filter fields