"""Kaggle source for datasets and models."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests
import json

from zhuai.models.resource import CodeResource, TrendingItem, ResourceType, Platform


class KaggleSource:
    """Kaggle source for datasets, models, and notebooks.
    
    Features:
    - Search datasets
    - Search models
    - Get trending datasets
    - Get dataset/model details
    - Get file lists
    - Note: Limited API without authentication
    """
    
    API_URL = "https://www.kaggle.com/api/v1"
    WEB_URL = "https://www.kaggle.com"
    
    def __init__(
        self,
        timeout: int = 30,
        username: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize Kaggle source.
        
        Args:
            timeout: Request timeout in seconds
            username: Kaggle username (for API access)
            api_key: Kaggle API key
        """
        self.timeout = timeout
        self.username = username
        self.api_key = api_key
        
        self.headers = {}
        if username and api_key:
            import base64
            credentials = base64.b64encode(f"{username}:{api_key}".encode()).decode()
            self.headers["Authorization"] = f"Basic {credentials}"
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "Kaggle"
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Make API request."""
        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def _parse_dataset(self, data: Dict) -> CodeResource:
        """Parse dataset data."""
        ref = data.get("ref", "")
        author = ref.split("/")[0] if "/" in ref else None
        name = ref.split("/")[-1] if "/" in ref else data.get("title", "")
        
        return CodeResource(
            name=name,
            full_name=ref,
            description=data.get("description"),
            author=author,
            platform=Platform.KAGGLE.value,
            resource_type=ResourceType.DATASET.value,
            url=f"{self.WEB_URL}/datasets/{ref}",
            stars=data.get("voteCount", 0),
            downloads=data.get("downloadCount", 0),
            topics=data.get("tags", []),
            license=data.get("licenseName"),
            size=data.get("totalBytes", 0),
            metadata={
                "usability_rating": data.get("usabilityRating"),
                "subtitle": data.get("subtitle"),
                "files": data.get("files", []),
                "owner_avatar": data.get("ownerAvatar"),
            }
        )
    
    def _parse_model(self, data: Dict) -> CodeResource:
        """Parse model data."""
        ref = data.get("ref", "")
        author = ref.split("/")[0] if "/" in ref else None
        name = ref.split("/")[-1] if "/" in ref else data.get("title", "")
        
        return CodeResource(
            name=name,
            full_name=ref,
            description=data.get("description"),
            author=author,
            platform=Platform.KAGGLE.value,
            resource_type=ResourceType.MODEL.value,
            url=f"{self.WEB_URL}/models/{ref}",
            stars=data.get("voteCount", 0),
            downloads=data.get("downloadCount", 0),
            topics=data.get("tags", []),
            license=data.get("licenseName"),
            metadata={
                "framework": data.get("framework"),
                "model_type": data.get("modelType"),
            }
        )
    
    def search_datasets(
        self,
        query: str,
        sort_by: str = "hottest",
        max_results: int = 20,
    ) -> List[CodeResource]:
        """Search Kaggle datasets.
        
        Args:
            query: Search query
            sort_by: Sort by (hottest, votes, updated, active)
            max_results: Maximum number of results
            
        Returns:
            List of CodeResource objects
        """
        if not self.username or not self.api_key:
            return self._search_datasets_web(query, max_results)
        
        try:
            url = f"{self.API_URL}/datasets/list"
            params = {
                "search": query,
                "sort": sort_by,
                "page": 1,
                "pageSize": min(max_results, 100),
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                return self._search_datasets_web(query, max_results)
            
            data = response.json()
            
            datasets = []
            for item in data.get("datasets", []):
                datasets.append(self._parse_dataset(item))
            
            return datasets
            
        except Exception as e:
            print(f"Error searching Kaggle datasets: {e}")
            return self._search_datasets_web(query, max_results)
    
    def _search_datasets_web(self, query: str, max_results: int = 20) -> List[CodeResource]:
        """Search datasets via web scraping (fallback)."""
        try:
            # Use public search endpoint
            url = f"{self.WEB_URL}/search"
            params = {
                "q": query,
                "searchType": "dataset",
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            # Parse JSON data from page
            import re
            
            # Try to extract dataset data from page
            pattern = r'"datasets":\s*(\[.*?\])'
            match = re.search(pattern, response.text, re.DOTALL)
            
            if match:
                datasets_data = json.loads(match.group(1))
                
                datasets = []
                for item in datasets_data[:max_results]:
                    ref = item.get("ref", item.get("slug", ""))
                    datasets.append(CodeResource(
                        name=item.get("title", ref.split("/")[-1] if "/" in ref else ref),
                        full_name=ref,
                        description=item.get("description", ""),
                        author=ref.split("/")[0] if "/" in ref else None,
                        platform=Platform.KAGGLE.value,
                        resource_type=ResourceType.DATASET.value,
                        url=f"{self.WEB_URL}/datasets/{ref}",
                        stars=item.get("voteCount", 0),
                        downloads=item.get("downloadCount", 0),
                    ))
                
                return datasets
            
            return []
            
        except Exception as e:
            print(f"Error searching Kaggle web: {e}")
            return []
    
    def search_models(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[CodeResource]:
        """Search Kaggle models.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of CodeResource objects
        """
        if not self.username or not self.api_key:
            return []
        
        try:
            url = f"{self.API_URL}/models/list"
            params = {
                "search": query,
                "page": 1,
                "pageSize": min(max_results, 100),
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            models = []
            for item in data.get("models", []):
                models.append(self._parse_model(item))
            
            return models
            
        except Exception as e:
            print(f"Error searching Kaggle models: {e}")
            return []
    
    def get_dataset(self, owner: str, dataset: str) -> Optional[CodeResource]:
        """Get dataset details.
        
        Args:
            owner: Dataset owner
            dataset: Dataset name
            
        Returns:
            CodeResource if found
        """
        if not self.username or not self.api_key:
            return None
        
        try:
            url = f"{self.API_URL}/datasets/view/{owner}/{dataset}"
            data = self._make_request(url)
            return self._parse_dataset(data)
        except Exception as e:
            print(f"Error getting dataset: {e}")
            return None
    
    def get_dataset_files(self, owner: str, dataset: str) -> List[Dict]:
        """Get dataset files list.
        
        Args:
            owner: Dataset owner
            dataset: Dataset name
            
        Returns:
            List of file dictionaries
        """
        if not self.username or not self.api_key:
            return []
        
        try:
            url = f"{self.API_URL}/datasets/list/{owner}/{dataset}"
            data = self._make_request(url)
            
            files = []
            for item in data:
                files.append({
                    "name": item.get("name"),
                    "size": item.get("totalBytes"),
                    "url": f"{self.WEB_URL}/datasets/{owner}/{dataset}?select={item.get('name')}",
                })
            
            return files
            
        except Exception as e:
            print(f"Error getting dataset files: {e}")
            return []
    
    def get_trending_datasets(
        self,
        max_results: int = 20,
    ) -> List[TrendingItem]:
        """Get trending datasets.
        
        Args:
            max_results: Maximum results
            
        Returns:
            List of TrendingItem objects
        """
        datasets = self.search_datasets(query="", sort_by="hottest", max_results=max_results)
        
        trending = []
        for i, dataset in enumerate(datasets, 1):
            trending.append(TrendingItem(
                rank=i,
                resource=dataset,
                trending_score=dataset.downloads + dataset.stars * 10,
            ))
        
        return trending
    
    async def search_datasets_async(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[CodeResource]:
        """Async wrapper for search_datasets."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.search_datasets(query, max_results=max_results)
        )


def search_kaggle_datasets(
    query: str,
    max_results: int = 20,
) -> List[CodeResource]:
    """Convenience function to search Kaggle datasets."""
    source = KaggleSource()
    return source.search_datasets(query, max_results=max_results)