This module enhances data fetching capabilities by implementing custom DataLoader
logic using the Strawberry DataLoader utility, and defining a structure for 
dependency injection fields. It supports dynamic resolution of fields across 
related data models with configurable foreign key relationships.

Classes:

**Dl:** A class to define relationships between data fields across different models
that may or may not be directly linked via foreign keys.

**GraphemyDataLoader:** Extends Strawberry's DataLoader to support custom filtering
logic and data manipulation based on incoming requests and provided filter criteria.

Functions:

**dict_to_tuple:** Converts dictionaries, possibly containing nested dictionaries or lists,
into a tuple format, suitable for consistent hashing and comparisons.

::: DL