format_project:
	@python -m pip install black
	@black canalservice
	@black orders
