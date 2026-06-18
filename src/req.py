from __future__ import annotations

from requests import Response, Session
from requests.cookies import RequestsCookieJar
from requests.exceptions import HTTPError, Timeout, ConnectionError, TooManyRedirects, RequestException

from typing import Any, Dict, Optional
from pathlib import Path
import json

from src.protocols import (
	HttpClient, CookieStorageManager, RequestBuilder, _FlaskCookieManager, HeaderManager
)


class FlaskCookieManager(_FlaskCookieManager):
	"""A flask cookie manager than handles cookies persistance"""
	def __init__(self, cookie_storage: CookieStorageManager) -> None:
		self.cookies = {}
		self.csrf_cookies = {}
		self.cookie_storage = cookie_storage

		# Load cookies from storage
		for cookie_name, value in self.cookie_storage.load().items():
			if "csrf" in cookie_name:
				self.csrf_cookies[cookie_name] = value
			else:
				self.cookies[cookie_name] = value


	def update_cookies_from_cookie_response(self, cookies: RequestsCookieJar) -> None:
		allowed_cookie_names = {"access_token_cookie", "refresh_token_cookie", "csrf_access_token", "csrf_refresh_token"}

		for cookie_name in allowed_cookie_names:
			if cookie_name in cookies:
				if "csrf" in cookie_name:
					self.csrf_cookies[cookie_name] = cookies[cookie_name]
				else:
					self.cookies[cookie_name] = cookies[cookie_name]

		self.cookie_storage.save({**self.csrf_cookies, **self.cookies})

	def get_cookies_for_session(self) -> Dict[str, str]:
		return {**self.csrf_cookies, **self.cookies}

	def get_csrf_header(self, cookie_type: str = "csrf_access") -> Dict[str, str]:
		headers = {}
		complete_cookie_name = cookie_type + "_token"

		csrf_cookie = self.csrf_cookies.get(complete_cookie_name)

		headers.update({"X-CSRF-TOKEN": csrf_cookie})

		return headers

	def clear_cookies(self) -> None:
		self.cookies.clear()
		self.csrf_cookies.clear()

		self.cookie_storage.save({**self.csrf_cookies, **self.cookies})



class FlaskHeaderManager(HeaderManager):
	"""A flask headers manager"""
	def __init__(self, storage: CookieStorageManager) -> None:
		self.headers = {}
		self.storage = storage

		# Load saved header data
		self.__load_headers_from_storage()

	def update_tokens_from_json(self, json_data: dict[str, str]) -> None:
		allowed_token_name = {"access_token", "refresh_token"}

		for token_name in allowed_token_name:
			if token_name in json_data:
				self.headers[token_name] = json_data[token_name]


		self.storage.save(self.headers)


	def get_auth_header(self, token_type: str) -> Dict[str, Any]:
		""""""
		headers = {}

		token_type = token_type + "_token"

		if token_type in self.headers:
			headers["Authorization"] = f"Bearer {self.headers[token_type]}"

		return headers


	def additional_headers(self, header_data: dict[str, Any]) -> Dict[str, Any]:
		self.headers.update(header_data)

		return header_data


	def __load_headers_from_storage(self) -> None:
		"""A helper method for retrieving headers from storage"""
		headers = self.storage.load()

		# Filter so non-header data doesn't mix with that of header\
		allowed_token_name = {"access_token", "refresh_token"}

		for token_name in allowed_token_name:
			if token_name in headers:
				self.headers[token_name] = headers[token_name]

		

class FileCookieStorage(CookieStorageManager):
	"""Handles saving cookies and other data to disk"""
	def __init__(self, file_path: str | Path) -> None:
		self.file_path = self.__ensure_path_exists(file_path)

	def save(self, cookies: dict[str, str]) -> None:
		with open(self.file_path, "w") as f:
			json.dump(cookies, f, indent=4)


	def load(self) -> Dict[str, str]:
		with open(self.file_path, "r") as f:
			try:
				data = json.load(f)

			except json.JSONDecodeError:
				return {}

		return data

	def __ensure_path_exists(self, file_path: str | Path) -> Path:
		""" A helper method that ensures a file is always there before it is being used
		
		Args:
			file_path (str | Path): The path to the file either in a string version or a Path obj

		Returns:
			Path: A path obj pointing to the where the file exists
		"""
		path = Path(file_path)

		if not path.exists():
			path.touch()

		return path



class RequestURLBuilder(RequestBuilder):
	"""Handles constructing a url"""
	def __init__(self, base_url: str) -> None:
		self.base_url = self.__build_base_url(base_url)


	def build_url(self, endpoint: str, resource: Optional[str] = None) -> str:
		if endpoint.startswith("/"):
			endpoint = endpoint.lstrip("/")

		if endpoint.endswith("/"):
			endpoint = endpoint.rstrip("/")


		url = f"{self.base_url}/{endpoint}"

		if resource:
			if resource.startswith("/"):
				resource = resource.lstrip("/")

			url = f"{url}/{resource}"

		return url 


	# Helper methods
	def __build_base_url(self, base_url: str) -> str:
		"""
		Strips trailing slashes (/) from the base url

		Args:
			base_url (str): The base url of the server

		Returns:
			str: A base url without trailing slashes
		"""
		if base_url.endswith("/"):
			base_url = base_url.rstrip("/")

		return base_url


class SessionClient(HttpClient):
	"""A client that makes http requests using requests.Session()"""
	def __init__(self, cookie_manager: _FlaskCookieManager, url_builder: RequestBuilder, header_manager: HeaderManager) -> None:
		self.cookie_manager = cookie_manager
		self.url_builder = url_builder
		self.header_manager = header_manager
		self.session = Session()

		# Load cookies to session
		self.__sync_cookies_to_session()

	def request(self, method: str, endpoint: str, **kwargs) -> Response | dict[str, Any]:
		url = self.url_builder.build_url(endpoint)

		csrf_token_type: str = kwargs.pop("csrf_cookie_type", None) or "csrf_access"
		auth_header = kwargs.pop("AUTH_HEADER", None)

		if auth_header:
			token_type = kwargs.pop("token_type", None) or "access"
			kwargs["headers"] = self.header_manager.get_auth_header(token_type)
		else:
			if method.upper() != "GET":
				kwargs["headers"] = self.cookie_manager.get_csrf_header(csrf_token_type)

		try:
			response = self.session.request(method, url, **kwargs)

			response.raise_for_status()


			if response.cookies:
				self.cookie_manager.update_cookies_from_cookie_response(response.cookies)
				self.__sync_cookies_to_session()

			if self.__a_json_data(response.json()):
				self.header_manager.update_tokens_from_json(response.json())

			return response

		except HTTPError as he:
			return {
				"status_code": response.status_code, # pyright: ignore
				"error": str(he),
				"details": response.json()
			}
		except Timeout as t:
			return {
				"status_code": response.status_code, # pyright: ignore
				"error": str(t),
				"details": response.json()
			}
		except ConnectionError as ce:
			return {
				"status_code": response.status_code, # pyright: ignore
				"error": str(ce),
				"details": response.json()
			}
		except TooManyRedirects as tmr:
			return {
				"status_code": response.status_code, # pyright: ignore
				"error": str(tmr),
				"details": response.json()
			}
		except RequestException as re:
			return {
				"status_code": response.status_code, # pyright: ignore
				"error": str(re),
				"details": response.json()
			}
		except Exception as e:
			return {
				"error": str(e)
			}

	def get(self, endpoint: str, **kwargs) -> Response | dict[str, Any]:
		return self.request("GET", endpoint, **kwargs)

	def post(self, endpoint: str, **kwargs) -> Response | dict[str, Any]:
		return self.request("POST", endpoint, **kwargs)

	def put(self, endpoint: str, **kwargs) -> Response | dict[str, Any]:
		return self.request("PUT", endpoint, **kwargs)

	def patch(self, endpoint: str, **kwargs) -> Response | dict[str, Any]:
		return self.request("PATCH", endpoint, **kwargs)

	def delete(self, endpoint: str, **kwargs) -> Response | dict[str, Any]:
		return self.request("DELETE", endpoint, **kwargs)


	def __sync_cookies_to_session(self) -> None:
		"""Ensures that session is always with the right cookies"""
		for cookie_name, value in self.cookie_manager.get_cookies_for_session().items():
			self.session.cookies.set(cookie_name, value)

	def __a_json_data(self, json_data: dict[str, str]) -> bool:
		"""
		A helper method that checks if tokens are present in a json body

		Args:
			json_data (dict[str, str]): The json body to confirm if tokens exists in it

		Returns:
			bool: True if any of the token exits else False 
		"""
		return "refresh_token" in json_data or "access_token" in json_data



class FlaskAPIClient:
	"""An api client deisgned to work with flask applications"""
	def __init__(self, base_url: str, file_path: str | Path):
		self.cookie_storage = FileCookieStorage(file_path)
		self.cookie_manager = FlaskCookieManager(self.cookie_storage)
		self.url_builder = RequestURLBuilder(base_url)
		self.header_manager = FlaskHeaderManager(self.cookie_storage)
		self.session_client = SessionClient(self.cookie_manager, self.url_builder, self.header_manager)


	def request(self, method: str, endpoint: str, **kwargs) -> Response | Dict[str, str]:
		"""
		A generic request method with auto CSRF inject, extraction and header injection

		Args:
			method (str): The HTTP protocol for making a request. Can be GET, POST, DELETE ...
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		return self.session_client.request(method, endpoint, **kwargs)

	def get(self, endpoint: str, **kwargs) -> Response | Dict[str, str]:
		"""
		A get request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		return self.session_client.get(endpoint, **kwargs)

	def post(self, endpoint: str, **kwargs) -> Response | Dict[str, str]:
		"""
		A post request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		return self.session_client.post(endpoint, **kwargs)

	def put(self, endpoint: str, **kwargs) -> Response | Dict[str, str]:
		"""
		A put request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		return self.session_client.put(endpoint, **kwargs)

	def patch(self, endpoint: str, **kwargs) -> Response | Dict[str, str]:
		"""
		A patch request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		return self.session_client.patch(endpoint, **kwargs)

	def delete(self, endpoint: str, **kwargs) -> Response | Dict[str, str]:
		"""
		A delete request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		return self.session_client.delete(endpoint, **kwargs)

	def clear_cookies(self) -> None:
		"""Handles clearing cookies from state and storage"""
		self.cookie_manager.clear_cookies()