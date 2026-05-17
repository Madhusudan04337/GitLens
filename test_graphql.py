import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_graphql(username):
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {github_token}"}
    
    gql_query = {
        "query": """
        query($username: String!) {
          user(login: $username) {
            pinnedItems(first: 6, types: REPOSITORY) {
              nodes {
                ... on Repository {
                  name
                  description
                  stargazerCount
                  primaryLanguage {
                    name
                  }
                }
              }
            }
          }
        }
        """,
        "variables": {"username": username}
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.github.com/graphql", json=gql_query, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "Madhusudan04337"
    asyncio.run(test_graphql(user))
