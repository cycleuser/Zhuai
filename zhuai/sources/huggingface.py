"""Hugging Face source for models and datasets."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests

from zhuai.models.resource import CodeResource, TrendingItem, ResourceType, Platform


class HuggingFaceSource:
    """Hugging Face source for models and datasets.
    
    Features:
    - Search models
    - Search datasets
    - Get trending models
    - Get model/dataset details
    - Get README/documentation
    - Support HF Mirror
    """
    
    API_URL = "https://huggingface.co/api"
    HF_URL = "https://huggingface.co"
    HF_MIRROR_URL = "https://hf-mirror.com"
    
    def __init__(
        self,
        timeout: int = 30,
        token: Optional[str] = None,
        use_mirror: bool = False,
    ):
        """Initialize Hugging Face source.
        
        Args:
            timeout: Request timeout in seconds
            token: HF token (optional, for private repos)
            use_mirror: Use hf-mirror.com instead of huggingface.co
        """
        self.timeout = timeout
        self.token = token
        self.use_mirror = use_mirror
        self.base_url = self.HF_MIRROR_URL if use_mirror else self.HF_URL
        
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "HuggingFace" if not self.use_mirror else "HuggingFace Mirror"
    
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
        """Parse model data from API response."""
        model_id = data.get("id", data.get("modelId", ""))
        author = model_id.split("/")[0] if "/" in model_id else None
        name = model_id.split("/")[-1] if "/" in model_id else model_id
        
        created_at = None
        if data.get("createdAt"):
            try:
                created_at = datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
            except:
                pass
        
        updated_at = None
        if data.get("lastModified"):
            try:
                updated_at = datetime.fromisoformat(data["lastModified"].replace("Z", "+00:00"))
            except:
                pass
        
        downloads = data.get("downloads", 0)
        likes = data.get("likes", 0)
        
        tags = data.get("tags", [])
        pipeline_tag = data.get("pipeline_tag")
        if pipeline_tag and pipeline_tag not in tags:
            tags.insert(0, pipeline_tag)
        
        return CodeResource(
            name=name,
            full_name=model_id,
            description=data.get("cardData", {}).get("description") or data.get("description"),
            author=author,
            platform=Platform.HUGGINGFACE.value,
            resource_type=ResourceType.MODEL.value,
            url=f"{self.base_url}/{model_id}",
            stars=likes,
            downloads=downloads,
            likes=likes,
            language=data.get("cardData", {}).get("language", [None])[0] if data.get("cardData", {}).get("language") else None,
            license=data.get("cardData", {}).get("license"),
            topics=tags,
            created_at=created_at,
            updated_at=updated_at,
            download_url=f"{self.base_url}/{model_id}/resolve/main",
            metadata={
                "pipeline_tag": pipeline_tag,
                "library_name": data.get("cardData", {}).get("library_name"),
                "task": data.get("task"),
                "tags": tags,
                "private": data.get("private", False),
                "gated": data.get("gated", False),
            }
        )
    
    def _parse_dataset(self, data: Dict) -> CodeResource:
        """Parse dataset data from API response."""
        dataset_id = data.get("id", data.get("datasetId", ""))
        author = dataset_id.split("/")[0] if "/" in dataset_id else None
        name = dataset_id.split("/")[-1] if "/" in dataset_id else dataset_id
        
        created_at = None
        if data.get("createdAt"):
            try:
                created_at = datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
            except:
                pass
        
        downloads = data.get("downloads", 0)
        likes = data.get("likes", 0)
        
        tags = data.get("tags", [])
        
        return CodeResource(
            name=name,
            full_name=dataset_id,
            description=data.get("cardData", {}).get("description") or data.get("description"),
            author=author,
            platform=Platform.HUGGINGFACE.value,
            resource_type=ResourceType.DATASET.value,
            url=f"{self.base_url}/datasets/{dataset_id}",
            stars=likes,
            downloads=downloads,
            likes=likes,
            license=data.get("cardData", {}).get("license"),
            topics=tags,
            created_at=created_at,
            download_url=f"{self.base_url}/datasets/{dataset_id}/resolve/main",
            metadata={
                "tags": tags,
                "private": data.get("private", False),
            }
        )
    
    def search_models(
        self,
        query: str,
        author: Optional[str] = None,
        task: Optional[str] = None,
        library: Optional[str] = None,
        language: Optional[str] = None,
        sort: str = "downloads",
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Search Hugging Face models.
        
        Args:
            query: Search query
            author: Filter by author/organization
            task: Filter by task (e.g., text-generation, image-classification)
            library: Filter by library (e.g., pytorch, tensorflow)
            language: Filter by language
            sort: Sort by (downloads, likes, modified)
            max_results: Maximum number of results
            
        Returns:
            List of CodeResource objects
        """
        params = {
            "search": query,
            "sort": sort,
            "direction": -1,
            "limit": min(max_results, 1000),
        }
        
        if author:
            params["author"] = author
        if task:
            params["filter"] = task
        if library:
            params["library"] = library
        if language:
            params["language"] = language
        
        try:
            url = f"{self.API_URL}/models"
            data = self._make_request(url, params)
            
            models = []
            for item in data:
                models.append(self._parse_model(item))
            
            return models
            
        except Exception as e:
            print(f"Error searching HF models: {e}")
            return []
    
    def search_datasets(
        self,
        query: str,
        author: Optional[str] = None,
        language: Optional[str] = None,
        sort: str = "downloads",
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Search Hugging Face datasets.
        
        Args:
            query: Search query
            author: Filter by author/organization
            language: Filter by language
            sort: Sort by (downloads, likes, modified)
            max_results: Maximum number of results
            
        Returns:
            List of CodeResource objects
        """
        params = {
            "search": query,
            "sort": sort,
            "direction": -1,
            "limit": min(max_results, 1000),
        }
        
        if author:
            params["author"] = author
        if language:
            params["language"] = language
        
        try:
            url = f"{self.API_URL}/datasets"
            data = self._make_request(url, params)
            
            datasets = []
            for item in data:
                datasets.append(self._parse_dataset(item))
            
            return datasets
            
        except Exception as e:
            print(f"Error searching HF datasets: {e}")
            return []
    
    def get_model(self, model_id: str) -> Optional[CodeResource]:
        """Get model details.
        
        Args:
            model_id: Model ID (e.g., "bert-base-uncased" or "google/flan-t5-xl")
            
        Returns:
            CodeResource if found
        """
        try:
            url = f"{self.API_URL}/models/{model_id}"
            data = self._make_request(url)
            return self._parse_model(data)
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
            return self._parse_dataset(data)
        except Exception as e:
            print(f"Error getting dataset {dataset_id}: {e}")
            return None
    
    def get_readme(self, repo_id: str, repo_type: str = "model") -> Optional[str]:
        """Get README/Model Card content.
        
        Args:
            repo_id: Repository ID
            repo_type: Repository type (model, dataset, space)
            
        Returns:
            README content
        """
        try:
            if repo_type == "dataset":
                url = f"{self.base_url}/datasets/{repo_id}/raw/main/README.md"
            else:
                url = f"{self.base_url}/{repo_id}/raw/main/README.md"
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.text
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
            url = f"{self.API_URL}/models/{model_id}/tree/main"
            data = self._make_request(url)
            
            files = []
            for item in data:
                files.append({
                    "path": item.get("path"),
                    "type": item.get("type"),
                    "size": item.get("size"),
                    "url": f"{self.base_url}/{model_id}/blob/main/{item.get('path')}",
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
                trending_score=model.downloads + model.likes * 10,
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
        datasets = self.search_datasets(
            query="",
            sort="downloads",
            max_results=max_results,
        )
        
        trending = []
        for i, dataset in enumerate(datasets, 1):
            trending.append(TrendingItem(
                rank=i,
                resource=dataset,
                trending_score=dataset.downloads + dataset.likes * 10,
            ))
        
        return trending
    
    def get_model_card(self, model_id: str) -> Optional[Dict]:
        """Get full model card with metadata.
        
        Args:
            model_id: Model ID
            
        Returns:
            Model card dictionary
        """
        try:
            model = self.get_model(model_id)
            readme = self.get_readme(model_id)
            
            return {
                "model": model.to_dict() if model else None,
                "readme": readme,
                "files": self.get_model_files(model_id),
            }
        except Exception as e:
            print(f"Error getting model card: {e}")
            return None
    
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


class HFMirrorSource(HuggingFaceSource):
    """Hugging Face Mirror source (hf-mirror.com).
    
    Use this for faster access in China.
    """
    
    def __init__(self, timeout: int = 30, token: Optional[str] = None):
        """Initialize HF Mirror source."""
        super().__init__(timeout, token, use_mirror=True)


def search_hf_models(
    query: str,
    task: Optional[str] = None,
    max_results: int = 30,
) -> List[CodeResource]:
    """Convenience function to search HF models."""
    source = HuggingFaceSource()
    return source.search_models(query, task=task, max_results=max_results)


def search_hf_datasets(
    query: str,
    max_results: int = 30,
) -> List[CodeResource]:
    """Convenience function to search HF datasets."""
    source = HuggingFaceSource()
    return source.search_datasets(query, max_results=max_results)