"""Initial schema migration with all 28 tables.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-21 10:00:00
"""

from alembic import op
# pyrefly: ignore [missing-import]
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # 2. Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_roles_name', 'roles', ['name'])

    # 3. Permissions
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_permissions_name', 'permissions', ['name'])

    # 4. User Roles
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    )

    # 5. Role Permissions
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', sa.String(36), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )

    # 6. Data Owners
    op.create_table(
        'data_owners',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 7. Data Stewards
    op.create_table(
        'data_stewards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Datasets
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('dataset_name', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(100), nullable=False),
        sa.Column('source_system', sa.String(100), nullable=False),
        sa.Column('location', sa.String(500), nullable=False),
        sa.Column('format', sa.String(50), nullable=False, server_default='parquet'),
        sa.Column('size_bytes', sa.Integer(), server_default='0'),
        sa.Column('row_count', sa.Integer(), server_default='0'),
        sa.Column('refresh_frequency', sa.String(50), server_default='DAILY'),
        sa.Column('classification', sa.String(50), server_default='INTERNAL'),
        sa.Column('quality_score', sa.Float(), server_default='100.0'),
        sa.Column('certification_status', sa.String(50), server_default='UNCERTIFIED'),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('data_owners.id'), nullable=True),
        sa.Column('steward_id', sa.String(36), sa.ForeignKey('data_stewards.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_datasets_dataset_name', 'datasets', ['dataset_name'])
    op.create_index('ix_datasets_domain', 'datasets', ['domain'])

    # 9. Dataset Columns
    op.create_table(
        'dataset_columns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('data_type', sa.String(100), nullable=False),
        sa.Column('is_nullable', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('is_primary_key', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('is_foreign_key', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('classification', sa.String(50), server_default='INTERNAL'),
        sa.Column('is_masked', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_dataset_columns_dataset_id', 'dataset_columns', ['dataset_id'])

    # 10. Dataset Profiles
    op.create_table(
        'dataset_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('column_count', sa.Integer(), nullable=False),
        sa.Column('null_counts', sa.JSON(), nullable=True),
        sa.Column('null_percentages', sa.JSON(), nullable=True),
        sa.Column('unique_counts', sa.JSON(), nullable=True),
        sa.Column('uniqueness_percentages', sa.JSON(), nullable=True),
        sa.Column('column_statistics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Quality Rules
    op.create_table(
        'quality_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('rule_id', sa.String(100), unique=True, nullable=False),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('rule_expression', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), server_default='MEDIUM'),
        sa.Column('category', sa.String(50), server_default='TECHNICAL'),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_quality_rules_rule_id', 'quality_rules', ['rule_id'])

    # 12. Quality Results
    op.create_table(
        'quality_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('rule_id', sa.String(36), sa.ForeignKey('quality_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('total_records', sa.Integer(), server_default='0'),
        sa.Column('failed_records', sa.Integer(), server_default='0'),
        sa.Column('pass_rate', sa.Float(), server_default='100.0'),
        sa.Column('execution_time_ms', sa.Float(), server_default='0.0'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. Quality Issues
    op.create_table(
        'quality_issues',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('issue_id', sa.String(100), unique=True, nullable=False),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=True),
        sa.Column('rule_id', sa.String(36), sa.ForeignKey('quality_rules.id', ondelete='CASCADE'), nullable=True),
        sa.Column('severity', sa.String(20), server_default='MEDIUM'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), server_default='OPEN'),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('assigned_to', sa.String(255), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_quality_issues_issue_id', 'quality_issues', ['issue_id'])

    # 14. Remediation Actions
    op.create_table(
        'remediation_actions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('issue_id', sa.String(36), sa.ForeignKey('quality_issues.id', ondelete='CASCADE'), nullable=True),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=True),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('affected_rows', sa.Integer(), server_default='0'),
        sa.Column('executed_by', sa.String(255), server_default='AUTOMATED_ENGINE'),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Metadata Entries
    op.create_table(
        'metadata',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 16. Governance Policies
    op.create_table(
        'governance_policies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('policy_code', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), server_default='HIGH'),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 17. Policy Violations
    op.create_table(
        'policy_violations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('policy_id', sa.String(36), sa.ForeignKey('governance_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), server_default='OPEN'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 18. Compliance Frameworks
    op.create_table(
        'compliance_frameworks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('framework_code', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 19. Compliance Controls
    op.create_table(
        'compliance_controls',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('framework_id', sa.String(36), sa.ForeignKey('compliance_frameworks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('control_code', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('status', sa.String(30), server_default='PASS'),
        sa.Column('evidence_summary', sa.Text(), nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 20. Lineage Nodes
    op.create_table(
        'lineage_nodes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('node_key', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('domain', sa.String(100), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 21. Lineage Edges
    op.create_table(
        'lineage_edges',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_node_id', sa.String(36), sa.ForeignKey('lineage_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_node_id', sa.String(36), sa.ForeignKey('lineage_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transformation_type', sa.String(100), server_default='DIRECT_TRANSFORM'),
        sa.Column('pipeline_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 22. Glossary Terms
    op.create_table(
        'glossary_terms',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('term', sa.String(255), unique=True, nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('business_domain', sa.String(100), nullable=False),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('status', sa.String(30), server_default='APPROVED'),
        sa.Column('related_datasets', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 23. Schema Versions
    op.create_table(
        'schema_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('schema_hash', sa.String(64), nullable=False),
        sa.Column('columns_spec', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 24. Schema Drift Events
    op.create_table(
        'schema_drift_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('drift_type', sa.String(50), nullable=False),
        sa.Column('previous_value', sa.String(255), nullable=True),
        sa.Column('current_value', sa.String(255), nullable=True),
        sa.Column('severity', sa.String(20), server_default='HIGH'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 25. Data Contracts
    op.create_table(
        'data_contracts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_name', sa.String(255), unique=True, nullable=False),
        sa.Column('dataset_id', sa.String(36), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(20), server_default='1.0.0'),
        sa.Column('yaml_spec', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 26. Data Contract Violations
    op.create_table(
        'data_contract_violations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_id', sa.String(36), sa.ForeignKey('data_contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('violation_type', sa.String(50), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 27. Alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('alert_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), server_default='MEDIUM'),
        sa.Column('dataset_name', sa.String(255), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), server_default='UNACKNOWLEDGED'),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 28. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_id', sa.String(64), nullable=True),
        sa.Column('result', sa.String(50), server_default='SUCCESS'),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    tables = [
        'audit_logs', 'alerts', 'data_contract_violations', 'data_contracts',
        'schema_drift_events', 'schema_versions', 'glossary_terms',
        'lineage_edges', 'lineage_nodes', 'compliance_controls',
        'compliance_frameworks', 'policy_violations', 'governance_policies',
        'metadata', 'remediation_actions', 'quality_issues', 'quality_results',
        'quality_rules', 'dataset_profiles', 'dataset_columns', 'datasets',
        'data_stewards', 'data_owners', 'role_permissions', 'user_roles',
        'permissions', 'roles', 'users'
    ]
    for table in tables:
        op.drop_table(table)
