"""ModelScope source for models and datasets."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests

from zhuai.models.resource import CodeResource, TrendingItem, ResourceType, Platform


class ModelScopeSource:
    """ModelScope source for models and datasets.
    
    ModelScope is Alibaba's model platform (modelscope.cn).
    
    Features:
    - Search models
    - Search datasets
    - Get trending models
    - Get model details
    - Get README/documentation
    """
    
    API_URL = "https://modelscope.cn/api/v1"
    WEB_URL = "https://modelscope.cn"
    
    def __init__(
        self,
        timeout: int = 30,
        token: Optional[str] = None,
    ):
        """Initialize ModelScope source.
        
        Args:
            timeout: Request timeout in seconds
            token: ModelScope token (optional)
        """
        self.timeout = timeout
        self.token = token
        
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "ModelScope"
    
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
    
    def _parse_model(self, data: Dict) -> CodeResource:
        """Parse model data."""
        name = data.get("name", data.get("model_name", ""))
        namespace = data.get("namespace", data.get("owner", ""))
        full_name = f"{namespace}/{name}" if namespace else name
        
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except:
                pass
        
        updated_at = None
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            except:
                pass
        
        return CodeResource(
            name=name,
            full_name=full_name,
            description=data.get("description", data.get("short_description")),
            author=namespace,
            platform=Platform.MODELSCOPE.value,
            resource_type=ResourceType.MODEL.value,
            url=f"{self.WEB_URL}/models/{full_name}",
            stars=data.get("stars", 0),
            downloads=data.get("downloads", data.get("download_count", 0)),
            likes=data.get("likes", data.get("like_count", 0)),
            topics=data.get("tags", []),
            license=data.get("license"),
            created_at=created_at,
            updated_at=updated_at,
            metadata={
                "task": data.get("task"),
                "framework": data.get("framework"),
                "model_type": data.get("model_type"),
                "visibility": data.get("visibility"),
                "sdk": data.get("sdk"),
            }
        )
    
    def _parse_dataset(self, data: Dict) -> CodeResource:
        """Parse dataset data."""
        name = data.get("name", data.get("dataset_name", ""))
        namespace = data.get("namespace", data.get("owner", ""))
        full_name = f"{namespace}/{name}" if namespace else name
        
        return CodeResource(
            name=name,
            full_name=full_name,
            description=data.get("description"),
            author=namespace,
            platform=Platform.MODELSCOPE.value,
            resource_type=ResourceType.DATASET.value,
            url=f"{self.WEB_URL}/datasets/{full_name}",
            stars=data.get("stars", 0),
            downloads=data.get("downloads", 0),
            topics=data.get("tags", []),
            license=data.get("license"),
            size=data.get("size", 0),
            metadata={
                "visibility": data.get("visibility"),
            }
        )
    
    def search_models(
        self,
        query: str,
        task: Optional[str] = None,
        framework: Optional[str] = None,
        sort: str = "downloads",
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Search ModelScope models.
        
        Args:
            query: Search query
            task: Filter by task (e.g., text-generation, image-classification)
            framework: Filter by framework (e.g., pytorch, tensorflow)
            sort: Sort by (downloads, stars, updated)
            max_results: Maximum number of results
            
        Returns:
            List of CodeResource objects
        """
        params = {
            "Name": query,
            "PageSize": min(max_results, 100),
            "PageNumber": 1,
            "SortBy": sort,
        }
        
        if task:
            params["Task"] = task
        if framework:
            params["Framework"] = framework
        
        try:
            url = f"{self.API_URL}/models"
            data = self._make_request(url, params)
            
            models = []
            for item in data.get("Data", {}).get("Models", []):
                models.append(self._parse_model(item))
            
            return models
            
        except Exception as e:
            print(f"Error searching ModelScope models: {e}")
            return []
    
    def search_datasets(
        self,
        query: str,
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Search ModelScope datasets.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of CodeResource objects
        """
        params = {
            "Name": query,
            "PageSize": min(max_results, 100),
            "PageNumber": 1,
        }
        
        try:
            url = f"{self.API_URL}/datasets"
            data = self._make_request(url, params)
            
            datasets = []
            for item in data.get("Data", {}).get("Datasets", []):
                datasets.append(self._parse_dataset(item))
            
            return datasets
            
        except Exception as e:
            print(f"Error searching ModelScope datasets: {e}")
            return []
    
    def get_model(self, model_id: str) -> Optional[CodeResource]:
        """Get model details.
        
        Args:
            model_id: Model ID (e.g., "owner/model-name")
            
        Returns:
            CodeResource if found
        """
        try:
            url = f"{self.API_URL}/models/{model_id}"
            data = self._make_request(url)
            
            if data.get("Data"):
                return self._parse_model(data["Data"])
            
            return None
            
        except Exception as e:
            print(f"Error getting model {model_id}: {e}")
            return None
    
    def get_dataset(self, dataset_id: str) -> Optional[CodeResource]:
        """Get dataset details.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            CodeResource if found
        """
        try:
            url = f"{self.API_URL}/datasets/{dataset_id}"
            data = self._make_request(url)
            
            if data.get("Data"):
                return self._parse_dataset(data["Data"])
            
            return None
            
        except Exception as e:
            print(f"Error getting dataset {dataset_id}: {e}")
            return None
    
    def get_readme(self, model_id: str) -> Optional[str]:
        """Get model README content.
        
        Args:
            model_id: Model ID
            
        Returns:
            README content
        """
        try:
            url = f"{self.API_URL}/models/{model_id}/repo/files?Revision=master&FilePath=README.md"
            data = self._make_request(url)
            
            if data.get("Data"):
                return data["Data"].get("Content")
            
        except:
            pass
        
        return None
    
    def get_model_files(self, model_id: str) -> List[Dict]:
        """Get model files list.
        
        Args:
            model_id: Model ID
            
        Returns:
            List of file dictionaries
        """
        try:
            url = f"{self.API_URL}/models/{model_id}/repo/files"
            params = {"Revision": "master"}
            data = self._make_request(url, params)
            
            files = []
            for item in data.get("Data", []):
                files.append({
                    "name": item.get("Name"),
                    "path": item.get("Path"),
                    "type": item.get("Type"),
                    "size": item.get("Size"),
                })
            
            return files
            
        except Exception as e:
            print(f"Error getting model files: {e}")
            return []
    
    def get_trending_models(
        self,
        task: Optional[str] = None,
        max_results: int = 25,
    ) -> List[TrendingItem]:
        """Get trending models.
        
        Args:
            task: Filter by task
            max_results: Maximum results
            
        Returns:
            List of TrendingItem objects
        """
        models = self.search_models(
            query="",
            task=task,
            sort="downloads",
            max_results=max_results,
        )
        
        trending = []
        for i, model in enumerate(models, 1):
            trending.append(TrendingItem(
                rank=i,
                resource=model,
                trending_score=model.downloads + model.stars * 10,
            ))
        
        return trending
    
    def get_trending_datasets(
        self,
        max_results: int = 25,
    ) -> List[TrendingItem]:
        """Get trending datasets.
        
        Args:
            max_results: Maximum results
            
        Returns:
            List of TrendingItem objects
        """
        datasets = self.search_datasets(query="", max_results=max_results)
        
        trending = []
        for i, dataset in enumerate(datasets, 1):
            trending.append(TrendingItem(
                rank=i,
                resource=dataset,
                trending_score=dataset.downloads + dataset.stars * 10,
            ))
        
        return trending
    
    async def search_models_async(
        self,
        query: str,
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Async wrapper for search_models."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.search_models(query, max_results=max_results)
        )
    
    async def search_datasets_async(
        self,
        query: str,
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Async wrapper for search_datasets."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.search_datasets(query, max_results=max_results)
        )


def search_modelscope_models(
    query: str,
    max_results: int = 30,
) -> List[CodeResource]:
    """Convenience function to search ModelScope models."""
    source = ModelScopeSource()
    return source.search_models(query, max_results=max_results)


def search_modelscope_datasets(
    query: str,
    max_results: int = 30,
) -> List[CodeResource]:
    """Convenience function to search ModelScope datasets."""
    source = ModelScopeSource()
    return source.search_datasets(query, max_results=max_results)