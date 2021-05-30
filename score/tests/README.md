## Standards for OMM Testing
---
### Folder and file name in snakecase
1. Folders Naming Conventions
	- unit_test
	- integration_test

2. File Naming Conventions
	- Integration tests
		- test_integrate_*.py
	- Unit tests
		- test_unit_*.py

### How to run tests

- Assuming you're in score directory.

To run different test cases in tests/actions/tasks.py

```shell
python3 -m unittest tests.integration_test.test_integrate_omm_cases.OMMTestCases
```

