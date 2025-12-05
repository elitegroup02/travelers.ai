"""Initial schema

Revision ID: b742eabbe725
Revises:
Create Date: 2025-12-04 11:08:01.339839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = 'b742eabbe725'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('cities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('coordinates', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('wikidata_id', sa.String(length=20), nullable=True),
        sa.Column('google_place_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cities_coordinates', 'cities', ['coordinates'], unique=False, postgresql_using='gist')
    op.create_index('ix_cities_country', 'cities', ['country'], unique=False)

    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('preferred_language', sa.String(length=2), nullable=False),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_table('pois',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('city_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('wikidata_id', sa.String(length=20), nullable=True),
        sa.Column('google_place_id', sa.String(length=255), nullable=True),
        sa.Column('wikipedia_url', sa.String(length=500), nullable=True),
        sa.Column('coordinates', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('year_built_circa', sa.Boolean(), nullable=False),
        sa.Column('architect', sa.String(length=255), nullable=True),
        sa.Column('architectural_style', sa.String(length=255), nullable=True),
        sa.Column('heritage_status', sa.String(length=255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('summary_es', sa.Text(), nullable=True),
        sa.Column('wikipedia_extract', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('image_attribution', sa.Text(), nullable=True),
        sa.Column('poi_type', sa.String(length=50), nullable=True),
        sa.Column('estimated_visit_duration', sa.Integer(), nullable=False),
        sa.Column('data_quality_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('data_source', sa.String(length=50), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pois_city', 'pois', ['city_id'], unique=False)
    op.create_index('ix_pois_coordinates', 'pois', ['coordinates'], unique=False, postgresql_using='gist')
    op.create_index('ix_pois_type', 'pois', ['poi_type'], unique=False)
    op.create_index('ix_pois_wikidata', 'pois', ['wikidata_id'], unique=False)

    op.create_table('trips',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('destination_city_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('share_token', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['destination_city_id'], ['cities.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token')
    )
    op.create_index('ix_trips_share', 'trips', ['share_token'], unique=False)
    op.create_index('ix_trips_user', 'trips', ['user_id'], unique=False)

    op.create_table('itineraries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('trip_id', sa.UUID(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('schedule', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('total_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('total_travel_minutes', sa.Integer(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_itineraries_trip_day', 'itineraries', ['trip_id', 'day_number'], unique=True)

    op.create_table('trip_pois',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('trip_id', sa.UUID(), nullable=False),
        sa.Column('poi_id', sa.UUID(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=True),
        sa.Column('order_in_day', sa.Integer(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('is_must_see', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['poi_id'], ['pois.id'], ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trip_pois_trip', 'trip_pois', ['trip_id'], unique=False)
    op.create_index('ix_trip_pois_unique', 'trip_pois', ['trip_id', 'poi_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_trip_pois_unique', table_name='trip_pois')
    op.drop_index('ix_trip_pois_trip', table_name='trip_pois')
    op.drop_table('trip_pois')
    op.drop_index('ix_itineraries_trip_day', table_name='itineraries')
    op.drop_table('itineraries')
    op.drop_index('ix_trips_user', table_name='trips')
    op.drop_index('ix_trips_share', table_name='trips')
    op.drop_table('trips')
    op.drop_index('ix_pois_wikidata', table_name='pois')
    op.drop_index('ix_pois_type', table_name='pois')
    op.drop_index('ix_pois_coordinates', table_name='pois', postgresql_using='gist')
    op.drop_index('ix_pois_city', table_name='pois')
    op.drop_table('pois')
    op.drop_table('users')
    op.drop_index('ix_cities_country', table_name='cities')
    op.drop_index('ix_cities_coordinates', table_name='cities', postgresql_using='gist')
    op.drop_table('cities')
