from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251103_add_performance_indexes"
down_revision = "7dae1f22c3a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_routes_origin_dest_active', 'routes', ['origin', 'destination', 'is_active'])
    op.create_index('ix_routes_provider_id', 'routes', ['provider_id'])
    op.create_index('ix_schedules_route_id', 'schedules', ['route_id'])
    op.create_index('ix_schedules_provider_id', 'schedules', ['provider_id'])
    op.create_index('ix_schedules_departure_time_active', 'schedules', ['departure_time', 'is_active'])
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'])
    op.create_index('ix_bookings_schedule_id', 'bookings', ['schedule_id'])
    op.create_index('ix_bookings_payment_status', 'bookings', ['payment_status'])
    op.create_index('ix_insurance_policies_user_id', 'insurance_policies', ['user_id'])
    op.create_index('ix_insurance_policies_booking_id', 'insurance_policies', ['booking_id'])
    op.create_index('ix_wifi_codes_booking_id', 'wifi_codes', ['booking_id'])


def downgrade() -> None:
    op.drop_index('ix_wifi_codes_booking_id', table_name='wifi_codes')
    op.drop_index('ix_insurance_policies_booking_id', table_name='insurance_policies')
    op.drop_index('ix_insurance_policies_user_id', table_name='insurance_policies')
    op.drop_index('ix_bookings_payment_status', table_name='bookings')
    op.drop_index('ix_bookings_schedule_id', table_name='bookings')
    op.drop_index('ix_bookings_user_id', table_name='bookings')
    op.drop_index('ix_schedules_departure_time_active', table_name='schedules')
    op.drop_index('ix_schedules_provider_id', table_name='schedules')
    op.drop_index('ix_schedules_route_id', table_name='schedules')
    op.drop_index('ix_routes_provider_id', table_name='routes')
    op.drop_index('ix_routes_origin_dest_active', table_name='routes')


