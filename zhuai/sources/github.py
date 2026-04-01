"""GitHub source for repository search, trending, and documentation extraction."""

import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import requests

from zhuai.models.resource import CodeResource, TrendingItem, ResourceType, Platform


class GitHubSource:
    """GitHub repository source with search, trending, and README extraction.
    
    Features:
    - Search repositories by keyword
    - Get trending repositories
    - Extract README content
    - Get repository details
    - Search by language, topic, stars
    """
    
    API_URL = "https://api.github.com"
    TRENDING_URL = "https://github.com/trending"
    
    def __init__(
        self,
        timeout: int = 30,
        token: Optional[str] = None,
    ):
        """Initialize GitHub source.
        
        Args:
            timeout: Request timeout in seconds
            token: GitHub personal access token (optional, increases rate limit)
        """
        self.timeout = timeout
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "GitHub"
    
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
    
    def _parse_repo(self, data: Dict) -> CodeResource:
        """Parse repository data from API response."""
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
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            description=data.get("description"),
            author=data.get("owner", {}).get("login"),
            platform=Platform.GITHUB.value,
            resource_type=ResourceType.CODE.value,
            url=data.get("html_url"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            watchers=data.get("watchers_count", 0),
            language=data.get("language"),
            license=data.get("license", {}).get("spdx_id") if data.get("license") else None,
            topics=data.get("topics", []),
            created_at=created_at,
            updated_at=updated_at,
            open_issues=data.get("open_issues_count", 0),
            size=data.get("size", 0),
            metadata={
                "id": data.get("id"),
                "node_id": data.get("node_id"),
                "default_branch": data.get("default_branch"),
                "archived": data.get("archived", False),
                "disabled": data.get("disabled", False),
                "fork": data.get("fork", False),
                "homepage": data.get("homepage"),
            }
        )
    
    def search(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
        sort: str = "stars",
        order: str = "desc",
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Search GitHub repositories.
        
        Args:
            query: Search query
            language: Filter by programming language
            min_stars: Minimum number of stars
            sort: Sort by (stars, forks, updated)
            order: Sort order (asc, desc)
            max_results: Maximum number of results
            
        Returns:
            List of CodeResource objects
        """
        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language}"
        if min_stars:
            search_query += f" stars:>={min_stars}"
        
        params = {
            "q": search_query,
            "sort": sort,
            "order": order,
            "per_page": min(max_results, 100),
        }
        
        try:
            url = f"{self.API_URL}/search/repositories"
            data = self._make_request(url, params)
            
            repos = []
            for item in data.get("items", []):
                repos.append(self._parse_repo(item))
            
            return repos
            
        except Exception as e:
            print(f"Error searching GitHub: {e}")
            return []
    
    def get_trending(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        max_results: int = 25,
    ) -> List[TrendingItem]:
        """Get trending repositories.
        
        Args:
            language: Filter by programming language
            since: Time period (daily, weekly, monthly)
            max_results: Maximum number of results
            
        Returns:
            List of TrendingItem objects
        """
        try:
            url = f"{self.API_URL}/search/repositories"
            
            # Build trending query
            query = "stars:>100"
            if language:
                query += f" language:{language}"
            
            # Date filter based on since
            if since == "daily":
                date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                query += f" created:>{date}"
            elif since == "weekly":
                date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                query += f" pushed:>{date}"
            elif since == "monthly":
                date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                query += f" pushed:>{date}"
            
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(max_results, 100),
            }
            
            data = self._make_request(url, params)
            
            trending = []
            for i, item in enumerate(data.get("items", []), 1):
                resource = self._parse_repo(item)
                trending.append(TrendingItem(
                    rank=i,
                    resource=resource,
                    trending_score=resource.popularity_score,
                ))
            
            return trending
            
        except Exception as e:
            print(f"Error getting trending: {e}")
            return []
    
    def get_repo(self, owner: str, repo: str) -> Optional[CodeResource]:
        """Get repository details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            CodeResource if found
        """
        try:
            url = f"{self.API_URL}/repos/{owner}/{repo}"
            data = self._make_request(url)
            return self._parse_repo(data)
        except Exception as e:
            print(f"Error getting repo {owner}/{repo}: {e}")
            return None
    
    def get_readme(self, owner: str, repo: str, branch: str = "main") -> Optional[str]:
        """Get README content.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: main)
            
        Returns:
            README content as string
        """
        readme_names = ["README.md", "README.rst", "README.txt", "README", "readme.md"]
        
        for name in readme_names:
            try:
                # Try raw content URL
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{name}"
                response = requests.get(raw_url, timeout=self.timeout)
                if response.status_code == 200:
                    return response.text
            except:
                continue
        
        # Try API endpoint
        try:
            url = f"{self.API_URL}/repos/{owner}/{repo}/readme"
            data = self._make_request(url)
            
            if data.get("content"):
                import base64
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
        except:
            pass
        
        return None
    
    def get_readme_html(self, owner: str, repo: str) -> Optional[str]:
        """Get README as HTML.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            README HTML content
        """
        try:
            url = f"{self.API_URL}/repos/{owner}/{repo}/readme"
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.github.v3.html"
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.text
        except:
            pass
        
        return None
    
    def get_releases(self, owner: str, repo: str, max_results: int = 10) -> List[Dict]:
        """Get repository releases.
        
        Args:
            owner: Repository owner
            repo: Repository name
            max_results: Maximum number of releases
            
        Returns:
            List of release dictionaries
        """
        try:
            url = f"{self.API_URL}/repos/{owner}/{repo}/releases"
            params = {"per_page": max_results}
            data = self._make_request(url, params)
            
            releases = []
            for release in data:
                releases.append({
                    "tag": release.get("tag_name"),
                    "name": release.get("name"),
                    "published_at": release.get("published_at"),
                    "body": release.get("body"),
                    "html_url": release.get("html_url"),
                    "assets": [
                        {
                            "name": a.get("name"),
                            "url": a.get("browser_download_url"),
                            "size": a.get("size"),
                        }
                        for a in release.get("assets", [])
                    ],
                })
            
            return releases
            
        except Exception as e:
            print(f"Error getting releases: {e}")
            return []
    
    def get_contributors(self, owner: str, repo: str, max_results: int = 30) -> List[Dict]:
        """Get repository contributors.
        
        Args:
            owner: Repository owner
            repo: Repository name
            max_results: Maximum number of contributors
            
        Returns:
            List of contributor dictionaries
        """
        try:
            url = f"{self.API_URL}/repos/{owner}/{repo}/contributors"
            params = {"per_page": max_results}
            data = self._make_request(url, params)
            
            contributors = []
            for c in data:
                contributors.append({
                    "login": c.get("login"),
                    "avatar_url": c.get("avatar_url"),
                    "contributions": c.get("contributions"),
                    "html_url": c.get("html_url"),
                })
            
            return contributors
            
        except Exception as e:
            print(f"Error getting contributors: {e}")
            return []
    
    def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        max_results: int = 30,
    ) -> List[Dict]:
        """Get repository issues.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            max_results: Maximum number of issues
            
        Returns:
            List of issue dictionaries
        """
        try:
            url = f"{self.API_URL}/repos/{owner}/{repo}/issues"
            params = {
                "state": state,
                "per_page": max_results,
                "sort": "updated",
            }
            data = self._make_request(url, params)
            
            issues = []
            for issue in data:
                if "pull_request" not in issue:  # Skip PRs
                    issues.append({
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "state": issue.get("state"),
                        "created_at": issue.get("created_at"),
                        "updated_at": issue.get("updated_at"),
                        "html_url": issue.get("html_url"),
                        "user": issue.get("user", {}).get("login"),
                        "labels": [l.get("name") for l in issue.get("labels", [])],
                        "comments": issue.get("comments"),
                    })
            
            return issues
            
        except Exception as e:
            print(f"Error getting issues: {e}")
            return []
    
    def get_topics(self, owner: str, repo: str) -> List[str]:
        """Get repository topics.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of topics
        """
        try:
            url = f"{self.API_URL}/repos/{owner}/{repo}/topics"
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.github.mercy-preview+json"
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return data.get("names", [])
        except:
            pass
        
        return []
    
    def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        max_results: int = 30,
    ) -> List[Dict]:
        """Search code within repositories.
        
        Args:
            query: Search query
            language: Filter by language
            max_results: Maximum number of results
            
        Returns:
            List of code search results
        """
        search_query = query
        if language:
            search_query += f" language:{language}"
        
        params = {
            "q": search_query,
            "per_page": min(max_results, 100),
        }
        
        try:
            url = f"{self.API_URL}/search/code"
            data = self._make_request(url, params)
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "repository": item.get("repository", {}).get("full_name"),
                    "html_url": item.get("html_url"),
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching code: {e}")
            return []
    
    async def search_async(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
        max_results: int = 30,
    ) -> List[CodeResource]:
        """Async wrapper for search."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.search(query, language, min_stars, max_results=max_results)
        )
    
    async def get_trending_async(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        max_results: int = 25,
    ) -> List[TrendingItem]:
        """Async wrapper for get_trending."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.get_trending(language, since, max_results)
        )


def search_github(
    query: str,
    language: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_results: int = 30,
    token: Optional[str] = None,
) -> List[CodeResource]:
    """Convenience function to search GitHub.
    
    Args:
        query: Search query
        language: Filter by language
        min_stars: Minimum stars
        max_results: Maximum results
        token: GitHub token
        
    Returns:
        List of CodeResource objects
    """
    source = GitHubSource(token=token)
    return source.search(query, language, min_stars, max_results=max_results)


def get_github_trending(
    language: Optional[str] = None,
    since: str = "daily",
) -> List[TrendingItem]:
    """Convenience function to get trending repos.
    
    Args:
        language: Filter by language
        since: Time period (daily, weekly, monthly)
        
    Returns:
        List of TrendingItem objects
    """
    source = GitHubSource()
    return source.get_trending(language, since)


def get_github_readme(owner: str, repo: str) -> Optional[str]:
    """Convenience function to get README.
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        README content
    """
    source = GitHubSource()
    return source.get_readme(owner, repo)