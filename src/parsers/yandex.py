import time

import dotenv
from loguru import logger
from more_itertools import flatten
from yandex_ai_studio_sdk import AIStudio
from yandex_ai_studio_sdk._search_api.enums import SortMode, GroupMode, FixTypoMode, FamilyMode

from src.parsers.yandex_models import WEBSearchResult
from src.utils.func import rate_limited

dotenv.load_dotenv()

sdk = AIStudio()
sdk.setup_default_logging("error")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 YaBrowser/25.2.0.0 Safari/537.36"
search = sdk.search_api.web(
    search_type="ru",
    family_mode=FamilyMode.NONE,
    fix_typo_mode=FixTypoMode.ON,
    group_mode=GroupMode.FLAT,
    sort_mode=SortMode.BY_RELEVANCE,
    docs_in_group=1,
    groups_on_page=50,
    max_passages=5,
    user_agent=USER_AGENT,
)


def yandex_parse_results(pages):
    data = flatten(map(lambda x: flatten(x.groups), pages))
    data = list(map(WEBSearchResult.from_yandex, data))
    return data


@rate_limited(10)
def yandex_submit(query: str, page: int, timeout: int = 60, **kwargs):
    return search.run_deferred(query, format="parsed", page=page, timeout=timeout, **kwargs)


@rate_limited(5)
def yandex_op_is_finished(operation):
    try:
        return operation.get_status(timeout=0.5).is_finished
    except:
        return False


@rate_limited(5)
def yandex_op_result(operation):
    try:
        return operation.get_result(timeout=1)
    except:
        return None


@rate_limited(1)
def do_yandex_gen(query, pages=3, offset=0, timeout=60):
    logger.info(f"Initiating search for {query[:20]}... up to {pages} pages")
    operations = []
    for i in range(pages):
        operations.append(yandex_submit(query, page=offset + i, timeout=timeout))
    ts = time.time()
    done = [False for _ in range(pages)]
    while not all(done) and (time.time() - ts) < timeout:
        next_done = {i
                     for i, op in enumerate(operations)
                     if not done[i] and yandex_op_is_finished(op)}
        for i in next_done:
            done[i] = True
            yield yandex_op_result(operations[i])
            logger.info(f"Done page {i}")


@rate_limited(5)
def do_yandex(query, pages=3, offset=0, timeout=60):
    logger.info(f"Initiating search for {query[:20]}... up to {pages} pages")
    operations = []
    for i in range(pages):
        operations.append(yandex_submit(query, page=offset + i, timeout=timeout))

    ts = time.time()
    done = [False for _ in range(pages)]
    results = [None for _ in range(pages)]
    while not all(done) and (time.time() - ts) < timeout:
        next_done = {i
                     for i, op in enumerate(operations)
                     if not done[i] and yandex_op_is_finished(op)}
        for i in next_done:
            done[i] = True
            results[i] = yandex_op_result(operations[i])
        if next_done:
            logger.info(f"Done {sum(done)}/{pages} pages")

    logger.info("Search done")
    results = filter(lambda i: i, results)
    return yandex_parse_results(results)
