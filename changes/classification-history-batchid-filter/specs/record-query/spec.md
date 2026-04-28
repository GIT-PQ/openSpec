## ADDED Requirements

### Requirement: Filter by batch ID
The `GET /api/record/list` endpoint SHALL support filtering by batchId parameter for exact match queries.

#### Scenario: Filter by batch ID exact match
- **WHEN** user requests `GET /api/record/list?batchId=550e8400-e29b-41d4-a716-446655440000`
- **THEN** system returns only records where batch_id equals "550e8400-e29b-41d4-a716-446655440000" and user_id matches the current user

#### Scenario: Filter by batch ID combined with other filters
- **WHEN** user requests `GET /api/record/list?batchId=550e8400-e29b-41d4-a716-446655440000&source=batch&predLabel=医用成像器械`
- **THEN** system returns only records matching ALL specified filter conditions including batchId exact match and user_id matches the current user

#### Scenario: Empty batchId parameter ignored
- **WHEN** user requests `GET /api/record/list?batchId=` (empty value)
- **THEN** system ignores the batchId filter and returns records filtered by other specified conditions only