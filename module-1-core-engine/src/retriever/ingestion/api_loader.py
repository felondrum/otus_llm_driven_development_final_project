# Загрузчик API

from typing import List, Dict, Any, Optional
import aiohttp
from common.logging import logger, log_info
from .file_loader import get_file_loader


class APILoader:
    """Loader for ingesting data from APIs."""

    def __init__(self):
        self.file_loader = get_file_loader()

    async def load_from_api(
        self,
        url: str,
        method: str = "GET",
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> List[Dict[str, Any]]:
        """Load data from API endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method, url=url, params=params, headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"API error: {response.status}")
                        return []

                    data = await response.json()

                    # Convert to chunks
                    if isinstance(data, list):
                        return [
                            {
                                "text": str(item),
                                "metadata": {"source": url, "type": "api"},
                            }
                            for item in data
                        ]
                    elif isinstance(data, dict):
                        return [
                            {
                                "text": str(data),
                                "metadata": {"source": url, "type": "api"},
                            }
                        ]

                    return []

        except Exception as e:
            logger.error(f"Failed to load from API {url}: {e}")
            return []

    async def load_with_pagination(
        self,
        base_url: str,
        page_param: str = "page",
        page_size: int = 100,
        max_pages: int = 10,
    ) -> List[Dict[str, Any]]:
        """Load data with pagination support."""
        all_chunks = []

        for page in range(1, max_pages + 1):
            url = f"{base_url}?{page_param}={page}&limit={page_size}"
            chunks = await self.load_from_api(url)

            if not chunks:
                break

            all_chunks.extend(chunks)

            # Optional: check if we've reached the end
            # based on response metadata

            if len(chunks) < page_size:
                break

        log_info("Loaded from paginated API", pages=page, chunks=len(all_chunks))
        return all_chunks


# Global loader instance
_api_loader: Optional[APILoader] = None


def get_api_loader() -> APILoader:
    """Get global API loader instance."""
    global _api_loader
    if _api_loader is None:
        _api_loader = APILoader()
    return _api_loader
