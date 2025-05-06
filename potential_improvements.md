# Potential Improvements for Email Parser

## TESTING NOTE
* This has only been tested on Mac with Python 3.13.3
* Further testing WAS unnecessary due to project scope (Personal project)
* Now that others are interested in my project, I will be testing on my Windows and Linux machines.

## Code Structure Improvements

* proper class separation by moving the email validation and similarity checking logic into separate utility classes
* Create a dedicated EmailAddress class to encapsulate email validation and formatting logic
* Implement the Strategy pattern for different email parsing strategies
* Extract configuration parameters into a separate config file

## Performance

* Parallel processsing for large directories, finding a way to decrease memory usage as well while checking for duplicates on these larger lists
* Implement batch database operations instead of file writes for better performance
* Eliminating tldextract dependency. This would require a list of TLDs carried with the program.

## Feature Enhancements

* Support for .eml and other formats from Thunderbird that don't require importexporttools
* Support for other sources of input files
* Support for obfuscated emails (myname [at] mydomain -dot- com)
* Support for phone numbers with country codes
* Extraction of potential or known names
* ability to configure with a "pattern" file for systems dedicated to email ingest ([[Email=emaildomain.com, Name="name Name"]] style patterns from automated forms, etc.)
* bad domains list for known single-use email providers
* Extraction of "base" email from dedicated email names such as spam+actualemail@domain.com
* database useage or connection to CRMs
* Include email data column - date/time first seen/last seen
* fuzzy matching for domain names to catch typos

## Error Handling & Logging

* Add proper logging with different levels (DEBUG, INFO, ERROR)
* Add progress tracking with ETA for large processing jobs
* Implement retry for failures

## Testing & Documentation

* Include performance benchmarks
* Add example usage scenarios
* More comments in code

## Code Quality

* Reduce code duplication
* Better method and variable naming

## Data Handling Improvements

* Add input 'sanitization' to prevent errors on ingest from bad characters/corruption
* proper error handling for malicious input
* Add rate limiting for resource-intensive operations

## User Experience

* Implement resume capability for interrupted operations
* Add test-run mode that provides no output file
* Include error messages
* Gui if wanted. Potentially packaging with a hosted SPA for end-users
* Compile to executable for Windows

## Future Considerations

* Consider implementing a REST API interface
* Add support for cloud storage/webresource
* Consider implementing a GUI interface
* Direct mail server access
* Popular CRM integration for exclude lists and existing emails