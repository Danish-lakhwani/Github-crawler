import os
import sys
import time
import argparse
import requests
import json
from datetime import datetime, timezone
from tqdm import tqdm
from src.db import upsert_repos

GITHUB_GRAPHQL = 'https://api.github.com/graphql'

SEARCH_QUERY = 'stars:>0'

GRAPHQL_SEARCH = '''
query($q: String!, $first: Int!, $after: String) {
  search(query: $q, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo { endCursor hasNextPage }
    nodes {
      ... on Repository {
        id
        name
        nameWithOwner
        url
        stargazerCount
        owner { login }
      }
    }
  }
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
}
'''

def graphql_request(token, payload):
    headers = {'Authorization': f'bearer {token}', 'Accept': 'application/json'}
    resp = requests.post(GITHUB_GRAPHQL, json=payload, headers=headers, timeout=60)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise RuntimeError(f'GraphQL request failed: {resp.status_code} {resp.text}')

def iso_to_epoch(iso):
    return int(datetime.fromisoformat(iso.replace('Z','+00:00')).timestamp())

def crawl(token, target=100000, batch_size=100):
    assert batch_size <= 100, 'GitHub GraphQL search first max is 100'
    cursor = None
    total = 0
    max_iters = (target // batch_size) + 10
    it = 0

    pbar = tqdm(total=target, desc='repos')

    while total < target and it < max_iters:
        it += 1
        variables = {'q': SEARCH_QUERY, 'first': batch_size, 'after': cursor}
        payload = {'query': GRAPHQL_SEARCH, 'variables': variables}

        try:
            data = graphql_request(token, payload)
        except RuntimeError as e:
            print('Request failed, backing off...', e, file=sys.stderr)
            time.sleep(10 + it * 2)
            continue

        if 'errors' in data:
            print('GraphQL errors:', data['errors'], file=sys.stderr)
            if 'rateLimit' in data.get('data', {}) and data['data']['rateLimit'].get('resetAt'):
                reset = data['data']['rateLimit']['resetAt']
                secs = iso_to_epoch(reset) - int(datetime.now(timezone.utc).timestamp())
                if secs > 0:
                    print(f'Rate limited; sleeping {secs} seconds')
                    time.sleep(secs + 2)
                    continue
            time.sleep(5)
            continue

        rate = data.get('data', {}).get('rateLimit')
        if rate:
            remaining = rate.get('remaining', 0)
            resetAt = rate.get('resetAt')
            if remaining is not None and remaining < 100:
                if resetAt:
                    secs = iso_to_epoch(resetAt) - int(datetime.now(timezone.utc).timestamp())
                    if secs > 0:
                        print(f'Approaching rate limit (remaining={remaining}), sleeping {secs}s')
                        time.sleep(secs + 2)

        search = data.get('data', {}).get('search')
        if not search:
            print('No search results; breaking', file=sys.stderr)
            break

        nodes = search.get('nodes', [])
        rows = []
        for node in nodes:
            if not node:
                continue
            node_id = node.get('id')
            name = node.get('name')
            full = node.get('nameWithOwner')
            url = node.get('url')
            owner = node.get('owner', {}).get('login')
            stars = node.get('stargazerCount', 0)
            metadata = json.dumps({'fetched_at': datetime.now(timezone.utc).isoformat()})
            rows.append((node_id, name, owner, full, url, stars, metadata))

        if rows:
            try:
                upsert_repos(rows)
            except Exception as e:
                print('DB upsert failed:', e, file=sys.stderr)

        n = len(rows)
        total += n
        pbar.update(n)

        pageInfo = search.get('pageInfo', {})
        cursor = pageInfo.get('endCursor') if pageInfo.get('hasNextPage') else None

        if not cursor:
            print('No next cursor — search exhausted; restarting with a different query?')
            break

        time.sleep(0.5)

    pbar.close()
    print(f'Done: total={total}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=int, default=100000)
    parser.add_argument('--batch-size', type=int, default=100)
    args = parser.parse_args()

    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print('Error: GITHUB_TOKEN env var is required', file=sys.stderr)
        sys.exit(2)

    crawl(token, target=args.target, batch_size=args.batch_size)
