from typing import List, Optional
from strict.integrity.schemas import Region, RegionConfig, GeoRoutingConfig


class GeoRoutingEngine:
    """Engine for determining the best region for a request."""

    def __init__(self, config: GeoRoutingConfig):
        self.config = config

    def get_nearest_region(self, client_ip: str) -> RegionConfig:
        """Determine the nearest region based on client IP.

        In a real implementation, this would use a GeoIP database.
        For now, we use a simple mock logic.
        """
        # Mock logic based on IP prefixes (very simplified)
        if client_ip.startswith("1."):
            region_name = Region.AP_SOUTHEAST
        elif client_ip.startswith("2."):
            region_name = Region.EU_CENTRAL
        elif client_ip.startswith("3."):
            region_name = Region.US_WEST
        else:
            region_name = Region.US_EAST

        return self.get_region_config(region_name) or self.get_primary_region()

    def get_region_config(self, region: Region) -> Optional[RegionConfig]:
        """Get configuration for a specific region."""
        for r in self.config.regions:
            if r.region == region:
                return r
        return None

    def get_primary_region(self) -> RegionConfig:
        """Get the primary region configuration."""
        return self.get_region_config(self.config.primary_region)

    def get_failover_region(self, current_region: Region) -> Optional[RegionConfig]:
        """Determine the next region to failover to."""
        if not self.config.failover_enabled:
            return None

        # Failover to the next active region in the list
        for r in self.config.regions:
            if r.region != current_region and r.is_active:
                return r
        return None
