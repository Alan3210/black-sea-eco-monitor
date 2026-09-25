from backend.services.eea_station_provider import discover_eea_parquet_urls
from backend.services.eea_parquet_downloader import EEAParquetDownloader


def refresh_eea_station_observations(
    countries=("BG",),
    pollutants=None,
    session=None,
):
    urls = discover_eea_parquet_urls(
        countries=countries,
        pollutants=pollutants,
        session=session,
    )

    downloader = EEAParquetDownloader(
        session=session,
    )

    files = downloader.download_urls(urls)

    return {
        "status": "success",
        "files_discovered": len(urls),
        "files_downloaded": len(files),
    }
