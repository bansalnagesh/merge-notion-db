import os
import asyncio
from abc import ABC
from typing import List, Dict, Set
from notion_client import AsyncClient


class NotionDatabaseMerger(ABC):
    def __init__(self, notion_token: str):
        self.notion = AsyncClient(auth=notion_token)
        super().__init__()

    async def get_database_schema(self, database_id: str) -> Dict[str, Dict]:
        database = await self.notion.databases.retrieve(database_id=database_id)
        return database.get('properties', {})

    async def get_select_options(self, database_id: str) -> Dict[str, Set[str]]:
        schema = await self.get_database_schema(database_id)
        select_options = {}

        for prop_name, prop_config in schema.items():
            if prop_config['type'] in ['select', 'multi_select']:
                options = {option['name'] for option in prop_config.get('select', {}).get('options', [])}
                select_options[prop_name] = options

        return select_options

    async def merge_select_options(self, schemas: List[Dict[str, Dict]]) -> Dict[str, List[Dict[str, str]]]:
        merged_options = {}

        for schema in schemas:
            for prop_name, prop_config in schema.items():
                if prop_config['type'] in ['select', 'multi_select']:
                    if prop_name not in merged_options:
                        merged_options[prop_name] = []

                    options = prop_config.get('select', {}).get('options', [])
                    existing_names = {opt['name'] for opt in merged_options[prop_name]}
                    for option in options:
                        if option['name'] not in existing_names:
                            merged_options[prop_name].append({'name': option['name']})
                            existing_names.add(option['name'])

        return merged_options

    async def merge_schemas(self, schemas: List[Dict[str, Dict]]) -> tuple[Dict[str, Dict], Dict[str, List[int]]]:
        merged_schema = {}
        property_sources = {}

        for idx, schema in enumerate(schemas):
            for prop_name, prop_config in schema.items():
                if prop_name not in merged_schema:
                    merged_schema[prop_name] = prop_config
                    property_sources[prop_name] = [idx]
                else:
                    if merged_schema[prop_name]['type'] == prop_config['type']:
                        property_sources[prop_name].append(idx)
                    else:
                        new_name = f"{prop_name}_db{idx + 1}"
                        merged_schema[new_name] = prop_config
                        property_sources[new_name] = [idx]

        return merged_schema, property_sources

    async def update_select_options(self, database_id: str, property_name: str, options: List[str]):
        current_schema = await self.get_database_schema(database_id)
        property_schema = current_schema.get(property_name, {})

        if property_schema.get('type') in ['select', 'multi_select']:
            current_options = {
                opt['name'] for opt in
                property_schema.get('select', {}).get('options', [])
            }

            new_options = [{'name': opt} for opt in options if opt not in current_options]
            if new_options:
                await self.notion.databases.update(
                    database_id=database_id,
                    properties={
                        property_name: {
                            property_schema['type']: {
                                'options': new_options
                            }
                        }
                    }
                )

    async def create_merged_database(self, source_db_ids: List[str], title: str, parent_page_id: str) -> tuple[str, Dict[str, List[int]]]:
        schemas = []
        for db_id in source_db_ids:
            schema = await self.get_database_schema(db_id)
            schemas.append(schema)

        merged_schema, property_sources = await self.merge_schemas(schemas)

        new_db = await self.notion.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": title}}],
            properties=merged_schema
        )

        return new_db["id"], property_sources

    async def copy_data(self, source_db_id: str, target_db_id: str, db_index: int, property_sources: Dict[str, List[int]]):
        pages = []
        start_cursor = None
        source_schema = await self.get_database_schema(source_db_id)
        special_properties = {
            name: config['type']
            for name, config in source_schema.items()
            if config['type'] in ['select', 'multi_select', 'url']
        }

        while True:
            response = await self.notion.databases.query(
                database_id=source_db_id,
                start_cursor=start_cursor
            )
            pages.extend(response["results"])

            if not response.get("has_more"):
                break

            start_cursor = response.get("next_cursor")

        select_options_to_add: Dict[str, Set[str]] = {}

        for page in pages:
            for prop_name, prop_type in special_properties.items():
                if prop_name not in page["properties"]:
                    continue

                prop_data = page["properties"][prop_name]

                if prop_type == 'select':
                    if prop_name not in select_options_to_add:
                        select_options_to_add[prop_name] = set()
                    value = prop_data.get("select", {})
                    if value and value.get("name"):
                        select_options_to_add[prop_name].add(value["name"])

                elif prop_type == 'multi_select':
                    if prop_name not in select_options_to_add:
                        select_options_to_add[prop_name] = set()
                    values = prop_data.get("multi_select", [])
                    for value in values:
                        if value.get("name"):
                            select_options_to_add[prop_name].add(value["name"])

        for prop_name, options in select_options_to_add.items():
            await self.update_select_options(target_db_id, prop_name, list(options))

        for page in pages:
            properties = {}

            for target_prop, source_dbs in property_sources.items():
                if db_index in source_dbs:
                    original_prop = target_prop.split('_db')[0]
                    if original_prop in page["properties"]:
                        properties[target_prop] = page["properties"][original_prop]

            try:
                transformed_properties = {}
                for prop_name, prop_value in properties.items():
                    if not prop_value:
                        continue

                    prop_type = prop_value.get('type')
                    if prop_type == 'select':
                        select_value = prop_value.get('select')
                        if select_value and select_value.get('name'):
                            transformed_properties[prop_name] = {
                                'select': {'name': select_value['name']}
                            }
                    elif prop_type == 'multi_select':
                        multi_select = prop_value.get('multi_select', [])
                        if multi_select:
                            transformed_properties[prop_name] = {
                                'multi_select': [{'name': item['name']} for item in multi_select if item.get('name')]
                            }
                    elif prop_type == 'url':
                        url_value = prop_value.get('url')
                        if url_value:
                            transformed_properties[prop_name] = {'url': url_value}
                    else:
                        transformed_properties[prop_name] = prop_value

                if transformed_properties:
                    await self.notion.pages.create(
                        parent={"database_id": target_db_id},
                        properties=transformed_properties
                    )
            except Exception as e:
                print(f"Error copying page: {str(e)}, Property values: {properties}")

    async def merge_databases(self, db_ids: List[str], target_title: str, parent_page_id: str) -> str:
        merged_db_id, property_sources = await self.create_merged_database(
            source_db_ids=db_ids,
            title=target_title,
            parent_page_id=parent_page_id
        )

        for idx, db_id in enumerate(db_ids):
            await self.copy_data(
                source_db_id=db_id,
                target_db_id=merged_db_id,
                db_index=idx,
                property_sources=property_sources
            )

        return merged_db_id


async def main():
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        raise ValueError("Please set the NOTION_TOKEN environment variable.")

    parent_page_id = input("Enter the parent page ID for the new database: ")
    target_title = input("Enter the title for the merged database: ")

    source_db_ids = input("Enter the source database IDs, separated by commas: ").split(',')

    merger = NotionDatabaseMerger(notion_token)
    merged_db_id = await merger.merge_databases
