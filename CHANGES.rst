Changes
=======
Version 0.11.0 (released 2025-12-17)
----------------------------
- build(docker): upgrade XRootD to 5.9.1
- ci(codecov): fix Codecov and update GitHub Actions to latest versions
- build(docker): change local development server to port 8000
- ci(pytest): fix code coverage reporting
- ci(codecov): configure a threshold for code coverage reporting

Version 0.10.2 (released 2025-11-26)
----------------------------
- bug: add casting to string to fix mismatching types in a query

Version 0.10.1 (released 2025-11-24)
----------------------------
- bug: fix counting failed transfers

Version 0.10.0 (released 2025-11-20)
----------------------------
- fix: use always http protocol instead of xrootd for transfers
- fix: remove warnings from the startup
- fix: Add missing file to the record stage templates
- fix(oai-pmh): openaire uses dc description instead of datacite description
- fix: change message of datasets with a single file or event
- fix: improve querying transfer requests to prevent running out of memory
- fix: Change the templates to allow case insensitive searches
- ui: improvements to displaying dates
- cold: add information about failed transfers to the transfer requests table
- fix: update datacite to schema43

Version 0.9.1 (released 2025-10-28)
----------------------------
- dependency: update xrootd version

Version 0.9.0 (released 2025-10-28)
----------------------------
- fix: ensure latex is displayed properly in search results
- ui: display dates on record detail page
- docker: bind the port to the localhost
- fix: ensure sorting works properly for transfer requests table
- Search: Return empty set instead of dict when type keyword is unknown

Version 0.8.0 (released 2025-10-08)
----------------------------
- fixtures: Add news describing the cold storage
- kpi: Collect statistics on record staging requests
- cold: improve display of transfer requests
- cold: Ensure that requests without any transfers do not get stuck.
- bug: Fix the aggregation of file downloads (#172)

Version 0.7.0 (released 2025-10-01)
---------------------------
- cold: improve the statistics of the transfer requests

Version 0.6.0 (released 2025-09-29)
---------------------------
- cold: Add possibility to request only one dataset
- cold: keep the status of the record in REQUESTED until all files have been staged
- fix: Records without files are marked as online
- build: update dependencies to ensure building succeeds locally
- mail: added missing configuration and created test for sending email
- build: remove deprecated pytest-runner and update test setup
- oai2d: Change the percolator for DELPHI
- fixtures: add mode to delete entries
- fix: added backward compatibility for the year facet
- fix: ensure subscribing to a transfer works without errors

Version 0.5.0 (released 2025-08-18)
---------------------------
- Specifying the maximum number of transfers from the CLI
- UI: Created a new year facet (#171)
- fix: commit changes in clear-hot after all steps are completed (#191)
- ui: improve hover over links containing LaTeX formatting
- fixtures: prettify output messages
- XrootD: Automatically read version from environment/container
- test: added tests for cold storage
- fix: ignore subagg if agg is not in the request arguments
- XrootD: Bumped version from 5.8.3 to 5.8.4
- search: create parameter for search query to not return files and file indices

Version 0.4.8 (released 2025-07-10)
---------------------------
- ui: fix facet of number of events, fix templates to display the title 'Files and Indices' if there are files or indices
- cold: New option '-v' to verify files in opendata cold list
- sitemap: Split the sitemap into chunks of 500 entries
- fix: fixing false positive in cold_storage if the file exists.
- dependencies: Updating gevent dependency

Version 0.4.6 (released 2025-06-23)
---------------------------
- ui: fix link to index files and files bigger than the download warning threshold
- cold: staging and archiving requests that do not require transfers do not count for the threshold limit

Version 0.4.3 (released 2025-06-05)
----------------------------
- cold: Reduce the number of options for index files with only online files
Version 0.4.2 (released 2025-06-03)

----------------------------
- cold: Records without any files or file indices will be marked as Online

Version 0.4.1 (released 2025-05-26)
----------------------------
- Bug in the celery task for the requests

Version 0.4.0 (released 2025-05-26)
----------------------------
- First version with Cold Storage Support
- UI to request staging from tape
- New celery tasks to check for requests and the status of transfers

Version 0.3.0 (released 2025-03-31)
----------------------------
- dependencies: Moved to Flask 3
- openaire: Setting up oai2d server
- cold_data: Store multiple uri for a single file
- facets: Changing the availability toggle by a multiple option

Version 0.2.11 (released 2025-02-19)
----------------------------
- ui: fixed bug in selecting the file to download from file indices
- Requests: Add header for user/bot detection
- build(docker): remove obsoleted compose version attribute
- Authors: Updated list
- xrootd: Increase version number

Version 0.2.10 (released 2025-01-29)
----------------------------
- stats: collect stats on record views and file downloads.
- API: Added an endpoint to get the latest news articles as an RSS document
- Style: improved url highlighting
- View: Return the experiment of a record page as a custom HTTP header alongside the rendered template.

Version 0.2.9 (released 2025-01-10)
----------------------------
- template: Remove anniversary banner


Version 0.2.8 (released 2024-12-20)
----------------------------

- content: doc for the 10 year anniversary
- bug fixes: fix to download big files and keeping the original name of files within an index

Version 0.2.7 (released 2024-12-10)
----------------------------

- files: add support to keep file indices in the database
- templates: add banner for the 10th year anniversary
- experiments: add TOTEM and DELPHI. Add configuration variable to exclude experiments from templates


Version 0.1.5 (released 2024-07-09)
----------------------------

- templates: display notes for author records

Version 0.1.4 (released 2024-07-08)
----------------------------

- templates: Add DELPHI to the 'focus on' section


Version 0.1.0 (released 2024-06-26)
----------------------------

- upgrade minimum version of invenio-mail to v2.1.1
- tests: add checks to ensure npm modules are installed
