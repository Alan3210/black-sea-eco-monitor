def refresh_eea_station_data(
    *,
    discovered_urls=None,
    downloaded_files=None,
    observations=None,
):
    return {
        "status": "success",
        "files_discovered": len(discovered_urls or []),
        "files_downloaded": len(downloaded_files or []),
        "stations_count": len(observations or []),
    }
