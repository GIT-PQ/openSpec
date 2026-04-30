## ADDED Requirements

### Requirement: Classification record database table
The system SHALL create a `classification_record` table in the `zl` MySQL database with the following columns: `id` (bigint, PK, AUTO_INCREMENT), `user_id` (int, NOT NULL, INDEX), `summary` (text, NOT NULL), `pred_label` (varchar 100, NOT NULL), `pred_index` (int, NOT NULL), `pred_probability` (double, NOT NULL), `top_categories` (json, NULL), `source` (varchar 20, NOT NULL, DEFAULT 'single'), `batch_id` (varchar 50, NULL, INDEX), `create_time` (datetime, NOT NULL, DEFAULT CURRENT_TIMESTAMP).

#### Scenario: Table created with correct schema
- **WHEN** the database migration is executed
- **THEN** the `classification_record` table exists with all specified columns, types, constraints, and indexes

### Requirement: Automatic persistence on successful classification
The system SHALL automatically insert a record into the `classification_record` table after each successful single-patent classification (Python `/predict` returns code 200).

#### Scenario: Successful classification creates a record
- **WHEN** a user submits a patent summary and the Python service returns a successful prediction
- **THEN** a new record is inserted into `classification_record` with: `user_id` extracted from the request token, `summary` from the input, `pred_label`, `pred_index`, `pred_probability` from the prediction result, `top_categories` containing all 22 category probabilities as JSON, `source` set to 'single', `batch_id` set to null, and `create_time` auto-populated

#### Scenario: Failed classification does not create a record
- **WHEN** the Python service returns a non-200 code or throws an exception
- **THEN** no record is inserted into `classification_record`

### Requirement: User identity from Authorization header
The system SHALL extract the user ID from the `Authorization: Bearer token_{userId}_{timestamp}` request header when processing classification requests. If the token is missing or invalid, the classification SHALL still proceed with `user_id` set to 0 (anonymous).

#### Scenario: Valid token extracts user ID
- **WHEN** a classification request includes a valid `Authorization: Bearer token_5_1682678400000` header
- **THEN** the persisted record has `user_id` = 5

#### Scenario: Missing or invalid token defaults to anonymous
- **WHEN** a classification request has no `Authorization` header or the token format is invalid
- **THEN** the classification proceeds normally, and the persisted record has `user_id` = 0

### Requirement: Persistence failure tolerance
The system SHALL NOT allow classification record persistence failures to affect the user-facing classification result. If the database insert fails, the system SHALL log the error and still return the classification result to the user.

#### Scenario: Database insert fails during classification
- **WHEN** a classification succeeds but the database insert throws an exception
- **THEN** the user receives the normal classification response (code 200 with prediction data), and an error is logged

### Requirement: Full 22-category probability storage
The `top_categories` JSON field SHALL store all 22 category probability entries returned by the Python service, sorted by probability descending, each containing `name`, `probability`, and `index` fields.

#### Scenario: All categories stored in top_categories
- **WHEN** the Python service returns 22 categories in its response
- **THEN** the `top_categories` JSON field contains all 22 entries with `name`, `probability`, and `index` fields, sorted by probability descending

### Requirement: No changes to Python service and frontend
The Python service and frontend code SHALL NOT be modified. The persistence is implemented entirely within the Java backend layer.

#### Scenario: Python service unchanged
- **WHEN** the classification record persistence feature is deployed
- **THEN** the Python `/predict` endpoint request and response format remain identical

#### Scenario: Frontend unchanged
- **WHEN** the classification record persistence feature is deployed
- **THEN** the frontend classification flow and API call remain identical; the `Authorization` header is already sent by the existing request interceptor