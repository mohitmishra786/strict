import pytest
from strict.integrity.schemas import Region, RegionConfig, GeoRoutingConfig
from strict.core.geo_engine import GeoRoutingEngine


class TestGeoRouting:
    @pytest.fixture
    def geo_config(self) -> GeoRoutingConfig:
        return GeoRoutingConfig(
            regions=(
                RegionConfig(
                    region=Region.US_EAST, endpoint="https://us-east.api.strict.io"
                ),
                RegionConfig(
                    region=Region.US_WEST, endpoint="https://us-west.api.strict.io"
                ),
                RegionConfig(
                    region=Region.EU_CENTRAL,
                    endpoint="https://eu-central.api.strict.io",
                ),
                RegionConfig(
                    region=Region.AP_SOUTHEAST,
                    endpoint="https://ap-southeast.api.strict.io",
                    is_active=False,
                ),
            ),
            primary_region=Region.US_EAST,
        )

    def test_geo_routing_logic(self, geo_config: GeoRoutingConfig) -> None:
        engine = GeoRoutingEngine(geo_config)

        # Test mock IP routing
        # 1.2.3.4 would be AP_SOUTHEAST but it is inactive, so should return primary (US_EAST)
        assert engine.get_nearest_region("1.2.3.4").region == Region.US_EAST
        assert engine.get_nearest_region("2.3.4.5").region == Region.EU_CENTRAL
        assert engine.get_nearest_region("3.4.5.6").region == Region.US_WEST
        assert engine.get_nearest_region("8.8.8.8").region == Region.US_EAST

    def test_inactive_region_failover_flow(self, geo_config: GeoRoutingConfig) -> None:
        engine = GeoRoutingEngine(geo_config)

        # Manually request an inactive region's config
        config = engine.get_region_config(Region.AP_SOUTHEAST)
        assert config is not None
        assert config.is_active is False

        # Flow: Caller sees inactive -> calls get_failover_region
        failover = engine.get_failover_region(Region.AP_SOUTHEAST)
        assert failover is not None
        assert failover.is_active is True
        assert failover.region == Region.US_EAST

    def test_failover_logic(self, geo_config: GeoRoutingConfig) -> None:
        engine = GeoRoutingEngine(geo_config)

        # US_EAST fails over to US_WEST (next active region)
        failover = engine.get_failover_region(Region.US_EAST)
        assert failover is not None
        assert failover.region == Region.US_WEST

        # US_WEST fails over to US_EAST (next active region)
        failover = engine.get_failover_region(Region.US_WEST)
        assert failover is not None
        assert failover.region == Region.US_EAST

        # AP_SOUTHEAST is inactive, so it shouldn't be picked for failover
        failover = engine.get_failover_region(Region.EU_CENTRAL)
        assert failover is not None
        assert (
            failover.region == Region.US_EAST
        )  # AP_SOUTHEAST is skipped because is_active=False
