#!/usr/bin/env python3
"""Collect and resolve GitHub pull-request review feedback via gh."""

import argparse
import json
import subprocess
import sys
from typing import Any


THREADS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      headRefName
      baseRefName
      reviewThreads(first: 100, after: $after) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          originalLine
          diffSide
          comments(first: 100) {
            nodes { id body author { login } createdAt url }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

COMMENTS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      comments(first: 100, after: $after) {
        nodes { id body author { login } createdAt url }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

REVIEWS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviews(first: 100, after: $after) {
        nodes { id body state author { login } submittedAt }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

RESOLVE_MUTATION = """
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}
"""


def gh_api(query: str, **variables: Any) -> dict[str, Any]:
    command = ["gh", "api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        if value is None:
            continue
        command.extend(["-F", f"{name}={value}"])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout)


def repository() -> tuple[str, str]:
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Could not determine GitHub repository")
    owner, repo = result.stdout.strip().split("/", 1)
    return owner, repo


def pages(query: str, connection: str, owner: str, repo: str, number: int) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    after = None
    while True:
        response = gh_api(query, owner=owner, repo=repo, number=number, after=after)
        pull_request = response["data"]["repository"]["pullRequest"]
        if pull_request is None:
            raise RuntimeError(f"Pull request #{number} was not found")
        result = pull_request[connection]
        nodes.extend(result["nodes"])
        if not result["pageInfo"]["hasNextPage"]:
            return nodes
        after = result["pageInfo"]["endCursor"]


def collect(owner: str, repo: str, number: int) -> dict[str, Any]:
    response = gh_api(THREADS_QUERY, owner=owner, repo=repo, number=number)
    pull_request = response["data"]["repository"]["pullRequest"]
    if pull_request is None:
        raise RuntimeError(f"Pull request #{number} was not found")
    thread_connection = pull_request.pop("reviewThreads")
    threads = thread_connection["nodes"]
    after = thread_connection["pageInfo"]["endCursor"]
    while thread_connection["pageInfo"]["hasNextPage"]:
        response = gh_api(THREADS_QUERY, owner=owner, repo=repo, number=number, after=after)
        thread_connection = response["data"]["repository"]["pullRequest"]["reviewThreads"]
        threads.extend(thread_connection["nodes"])
        after = thread_connection["pageInfo"]["endCursor"]
    pull_request["reviewThreads"] = threads
    pull_request["conversationComments"] = pages(COMMENTS_QUERY, "comments", owner, repo, number)
    pull_request["reviewSummaries"] = [
        review for review in pages(REVIEWS_QUERY, "reviews", owner, repo, number) if review["body"].strip()
    ]
    return pull_request


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="GitHub repository as OWNER/REPO (defaults to current repository)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list", help="Write feedback JSON for pull requests")
    list_parser.add_argument("--pr", type=int, action="append", required=True, help="Pull request number; repeat per PR")
    resolve_parser = subparsers.add_parser("resolve", help="Resolve verified review threads")
    resolve_parser.add_argument("thread_ids", nargs="+", help="GitHub review-thread node IDs")
    args = parser.parse_args()

    try:
        owner, repo = args.repo.split("/", 1) if args.repo else repository()
        if args.command == "list":
            print(json.dumps({"repository": f"{owner}/{repo}", "pullRequests": [collect(owner, repo, number) for number in args.pr]}, indent=2))
            return
        outcomes = []
        for thread_id in args.thread_ids:
            response = gh_api(RESOLVE_MUTATION, threadId=thread_id)
            outcomes.append(response["data"]["resolveReviewThread"]["thread"])
        print(json.dumps({"resolved": outcomes}, indent=2))
    except (RuntimeError, KeyError, ValueError) as error:
        print(f"review_feedback.py: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
