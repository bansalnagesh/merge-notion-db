# Notion Database Merger

Easily **merge Notion Database** entries with this Python-based tool! This script simplifies the process of consolidating multiple Notion databases into a single merged database while preserving properties, schema, and data integrity.

## Features
- **Merge Notion Database Schemas**: Automatically detect and merge properties from multiple databases.
- **Preserve Select & Multi-Select Options**: Ensures that all select and multi-select values are retained.
- **Consolidate Data**: Copy and transform pages from source databases to the merged database.
- **Handle Conflicting Properties**: Automatically resolves property name conflicts by renaming them.
- **Async Operations**: Powered by Python's asyncio for fast and efficient database operations.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/bansalnagesh/merge-notion-db.git
   cd merge-notion-db
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Prerequisites

- A Notion integration token. You can generate one by [creating a Notion integration](https://developers.notion.com/docs/getting-started#step-1-create-an-integration).
- The Notion databases to be merged should be shared with the integration.

## Setup

1. Create an environment variable for your Notion token:
   ```bash
   export NOTION_TOKEN=your_notion_integration_token
   ```

2. Ensure you have the IDs of the Notion databases you want to merge and the parent page ID where the new merged database will be created.

## Usage

### Run the Script

1. Run the script:
   ```bash
   python merge_notion_db.py
   ```

2. Provide inputs when prompted:
   - **Parent Page ID**: The ID of the page where the merged database will be created.
   - **Merged Database Title**: A title for the newly created database.
   - **Source Database IDs**: Comma-separated IDs of the databases to merge.

### Example

If you want to merge three databases (`db1`, `db2`, `db3`) into a new database titled `Merged Database` under a parent page with ID `parent123`:

- Input `parent123` as the parent page ID.
- Input `Merged Database` as the title.
- Input `db1,db2,db3` as the source database IDs.

## Key Functions

### `merge_databases`
This is the main function to **merge Notion Database** entries. It:
- Creates a new database with a unified schema.
- Copies data from all source databases.

### `create_merged_database`
Handles schema merging and creates the new merged database in the specified parent page.

### `copy_data`
Transfers pages from the source databases to the new merged database, ensuring data compatibility.

### `merge_schemas`
Resolves property conflicts and creates a consolidated schema for the merged database.

## How It Works

1. **Schema Retrieval**: Extracts the schema from each source database.
2. **Schema Merging**: Combines the schemas, handling conflicts like duplicate property names.
3. **Data Consolidation**: Copies pages from source databases, updating select and multi-select properties.
4. **Merged Database Creation**: Creates a new database with the unified schema and imports data.

## Benefits

- Save time when managing multiple Notion databases.
- Ensure consistency in database properties.
- Reduce manual effort and potential errors.

## Troubleshooting

- **Invalid Token**: Ensure the NOTION_TOKEN environment variable is set and valid.
- **Access Denied**: Make sure the Notion integration has access to the source databases.
- **Missing Property**: Check that the source databases have consistent property configurations.

## Contributing

We welcome contributions! Feel free to submit issues or pull requests to improve the script.

## License

This project is licensed under the MIT License.

---

Start merging your Notion DBs today with this powerful and efficient tool!

---

For more information on how to merge Notion Database entries, check out our [documentation](https://developers.notion.com/docs) or [contact us](mailto:support@notionmerger.com).

