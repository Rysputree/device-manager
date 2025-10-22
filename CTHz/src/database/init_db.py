from src.database.connection import engine, Base

# Import all model modules to register metadata
from src.auth.models import User  # noqa: F401
from src.groups.models import Group  # noqa: F401
from src.stations.models import Station  # noqa: F401
from src.devices.models import Device, DeviceConfiguration  # noqa: F401
from src.policies.models import Policy  # noqa: F401
from src.monitoring.models import Alert  # noqa: F401
from src.storage.models import ArchiveServer  # noqa: F401
from src.integrations.models import Integration  # noqa: F401
from src.monitoring.audit import AuditLog  # noqa: F401
from src.cluster.models import DeviceMetadata, PairedDevice, PairingToken  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized")
