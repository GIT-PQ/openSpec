## ADDED Requirements

### Requirement: Record list query with filtering
The system SHALL provide a `GET /api/record/list` endpoint that returns classification records for the current user, supporting optional filtering by predLabel, startTime, endTime, source, and summary keyword.

#### Scenario: Query all records without filters
- **WHEN** user requests `GET /api/record/list` with no filter parameters
- **THEN** system returns all classification records belonging to the current user, ordered by create_time descending

#### Scenario: Filter by predicted category
- **WHEN** user requests `GET /api/record/list?predLabel=医用成像器械`
- **THEN** system returns only records where pred_label equals "医用成像器械" and user_id matches the current user

#### Scenario: Filter by time range
- **WHEN** user requests `GET /api/record/list?startTime=2026-04-01&endTime=2026-04-30`
- **THEN** system returns only records where create_time falls within the specified date range (inclusive) and user_id matches the current user

#### Scenario: Filter by source type
- **WHEN** user requests `GET /api/record/list?source=batch`
- **THEN** system returns only records where source equals "batch" and user_id matches the current user

#### Scenario: Filter by summary keyword with fuzzy match
- **WHEN** user requests `GET /api/record/list?summary=成像`
- **THEN** system returns only records where summary text contains "成像" (LIKE '%成像%') and user_id matches the current user

#### Scenario: Combined filters
- **WHEN** user requests `GET /api/record/list?predLabel=医用成像器械&source=single&summary=成像`
- **THEN** system returns only records matching ALL specified filter conditions and user_id matches the current user

### Requirement: User-scoped data access
All record query endpoints SHALL only return records belonging to the current authenticated user. The userId SHALL be extracted from the `Authorization: Bearer token_{userId}_{timestamp}` header as an implicit WHERE condition. The frontend SHALL NOT pass userId as a request parameter.

#### Scenario: User can only see own records
- **WHEN** user A requests `GET /api/record/list`
- **THEN** system returns only records where user_id equals user A's ID, never other users' records

### Requirement: Single record detail with ownership check
The system SHALL provide a `GET /api/record/{id}` endpoint that returns a single record's full details. The system SHALL verify that the record belongs to the current user; if not, the system SHALL return HTTP 404.

#### Scenario: Query own record detail
- **WHEN** user requests `GET /api/record/42` and record 42 belongs to the current user
- **THEN** system returns the full record including summary, pred_label, pred_index, pred_probability, top_categories, source, batch_id, and create_time

#### Scenario: Query another user's record detail
- **WHEN** user requests `GET /api/record/42` and record 42 belongs to a different user
- **THEN** system returns HTTP 404 without revealing the record's existence

### Requirement: LIKE wildcard escaping for security
When the summary filter parameter is used, the system SHALL escape SQL LIKE wildcards (`%` and `_`) in the user input to prevent them from being interpreted as SQL pattern characters.

#### Scenario: Input contains percent sign
- **WHEN** user requests `GET /api/record/list?summary=50%`
- **THEN** system treats `%` as a literal character, not a SQL wildcard, and searches for records containing "50%"

#### Scenario: Input contains underscore
- **WHEN** user requests `GET /api/record/list?summary=test_1`
- **THEN** system treats `_` as a literal character, not a SQL wildcard, and searches for records containing "test_1"

### Requirement: Reuse existing ClassificationRecordMapper
The system SHALL add select query methods to the existing `ClassificationRecordMapper` rather than creating a separate Mapper for the same table.

#### Scenario: Single mapper for classification_record
- **WHEN** record query methods are implemented
- **THEN** both insert (from step 1) and select methods reside in `ClassificationRecordMapper` and its XML mapping file
