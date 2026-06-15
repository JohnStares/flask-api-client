from __future__ import annotations


from typing import TYPE_CHECKING, Protocol, Dict, Any, Optional

if TYPE_CHECKING:
	from requests import Response
	from requests.cookies import RequestsCookieJar



class CookieManager(Protocol):
	"""This handles all cookie operations"""
	def update_cookies_from_cookie_response(self, cookies: RequestsCookieJar) -> None:
		"""
		This fetches cookies from the response

		Args:
			cookies (RequestsCookieJar): The respone container holding the coookies
		"""
		...

	def get_cookies_for_session(self) -> Dict[str, str]:
		"""
		This pulls cookies from state and make them available to client session on every request
		"""
		...

	def clear_cookies(self) -> None:
		"""
		This clears all saved cookies from state and storage
		"""
		...



class HttpClient(Protocol):
	"""Handles HTTP request making"""
	def request(self, method: str, endpoint: str, **kwargs) -> Response  | dict[str, Any]:
		"""
		A generic request method with auto CSRF inject, extraction and header injection

		Args:
			method (str): The HTTP protocol for making a request. Can be GET, POST, DELETE ...
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		...
	def get(self, endpoint: str, **kwargs) -> Response  | dict[str, Any]:
		"""
		A get request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		...
	def post(self, endpoint: str, **kwargs) -> Response  | dict[str, Any]:
		"""
		A post request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		...
	def put(self, endpoint: str, **kwargs) -> Response  | dict[str, Any]:
		"""
		A put request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		...
	def patch(self, endpoint: str, **kwargs) -> Response  | dict[str, Any]:
		"""
		A patch request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		...
	def delete(self, endpoint: str, **kwargs) -> Response  | dict[str, Any]:
		"""
		A delete request method that calls the request method under the hood

		Args:
			endpoint (str): The other part of the url without the base url
			kwargs (dict[dict[str, Any]]): Pass other arguments to it like params, data, json and other of requests arguments

		Return:
			Reponse | dict[str, Any]: A successfull response data or a dictionary containing details why the request wasn't successful
		"""
		...



class RequestBuilder(Protocol):
	"""Builds and prepares requests"""
	def build_url(self, endpoint: str, resource: Optional[str] = None) -> str:
		"""
		This method handles contruction of the url by removing unneccessary / and merge the base url with the endpoint provided

		Args:
			endpoint (str): The other part of the url without the base url
			resource (Optional[str]): Optional addons to the endpoint. Defaults to None

		Return:
			str: The full url
		"""
		...



class CookieStorageManager(Protocol):
	"""Manages cookies with external storage persistence"""
	def save(self, cookies: dict[str, str]) -> None:
		"""
		This saves the cookies to a storage medium. Useful for improving presistence of cookies and other data

		Args:
			cookies (dict[str, str]): The cookie data to be save. This can also be anything but it must be in a dict format
		"""
		...

	def load(self) -> Dict[str, str]:
		"""Handling reading the data from storage and returning it"""
		...


class _FlaskCookieManager(CookieManager, Protocol):
	""""""
	def get_csrf_header(self, cookie_type: str = "csrf_access") -> Dict[str, str]:
		"""
		This method returns cookies that are of csrf type. An extension of CookieManager to be used for flask project when dealing
		with double submit cookie strategy

		Args:
			cookie_type (str): This indicated the type of csrf token to be sent. NO need to provide the token suffix. Defaults ot csrf_access

		Returns:
			Dict[str, str]: A dict containing the cookie or token
		"""
		...


class HeaderManager(Protocol):
	""""""
	def get_auth_header(self, token_type: str) -> Dict[str, Any]:
		"""
		This method returns the token gotten during sign up to be used for authorization with subseqent request. Useful when you are not using
		cookies rather you are using JWT Auth Bearer

		Args:
			token_type (str): This indicated the type of token to return. In flask we have refresh and access

		Returns:
			Dict[str, str]: The auth token returned
		"""
		...

	def additional_headers(self, header_data: dict[str, Any]) -> Dict[str, Any]:
		"""
		Useful when providing addtional headers that you also want to persist in each request

		Args:
			header_data (dict[str, Any]): A dictionary containing all the headers

		Returns:
			Dict[str, Any]: The headers being returned after saving
		"""
		...

	def update_tokens_from_json(self, json_data: dict[str, str]) -> None:
		"""
		This fetches the JWT tokens right from the json body immediately after sign in

		Args:
			json_data (dict[str, str]): The container or json body where the token will be extracted from.
		"""
		...