"""
CLI for the search_tool package.
"""
import argparse
import asyncio
from .search import SearchTool
from .config import SearchConfig, SearchEngine
from .exceptions import ConfigurationError, SearchEngineError


async def run_search():
    parser = argparse.ArgumentParser(
        description='Search the web using various engines.'
    )
    parser.add_argument(
        '--engine',
        '-e',
        choices=['google', 'ddg', 'brave'],
        default='google',
        help='The search engine to use (google, ddg, brave).',
    )
    parser.add_argument('query', nargs='+', help='The search query.')
    parser.add_argument(
        '--num-results', type=int, default=10, help='Number of results to fetch.'
    )
    parser.add_argument(
        '--headless',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Run browser in headless mode.',
    )

    args = parser.parse_args()

    engine_name_str = args.engine.lower()
    search_query = ' '.join(args.query)

    try:
        selected_engine = SearchEngine(engine_name_str)
    except ValueError:
        print(
            f"Error: Invalid search engine '{args.engine}'. Supported engines are: {[e.value for e in SearchEngine]}"
        )
        return

    print(
        f'Searching with {selected_engine.value} for: "{search_query}" (Headless: {args.headless}, Num Results: {args.num_results})'
    )

    config = SearchConfig(
        search_engine=selected_engine,
        num_results=args.num_results,
        headless=args.headless,
    )

    search_tool_instance = SearchTool(config)

    try:
        results_obj = await search_tool_instance.search(search_query)
        if results_obj and results_obj.web_results:
            print('\nSearch Results:')
            for i, result in enumerate(results_obj.web_results, 1):
                print(f'{i}. {result.title}')
                print(f'   URL: {result.url}')
                if result.description:
                    print(f'   Description: {result.description}')
                print('-' * 20)
        else:
            print('No results found.')
    except SearchEngineError as e:
        print(f"Search Engine Error: {e}")
    except ConfigurationError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        await search_tool_instance.close()


def main():
    asyncio.run(run_search())


if __name__ == "__main__":
    main()
