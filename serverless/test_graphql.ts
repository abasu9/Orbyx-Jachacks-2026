import { Octokit } from 'octokit';
import * as dotenv from 'dotenv';
dotenv.config();

async function testGH() {
  const token = process.env.GITHUB_ORG_OAUTH_TOKEN || '';
  const org = process.env.GITHUB_ORG || '';
  const username = 'vinayakrb';
  
  const octokit = new Octokit({ auth: token });
  
  try {
    console.log("Testing GraphQL search...");
    const res = await octokit.graphql(`
      query($searchQuery: String!) {
        search(query: $searchQuery, type: ISSUE, first: 10) {
          issueCount
          nodes {
            ... on PullRequest {
              title
              repository {
                name
              }
            }
          }
        }
      }
    `, {
      searchQuery: `is:pr author:${username} org:${org}`
    });
    console.log("GraphQL success!", JSON.stringify(res, null, 2));
  } catch (e: any) {
    console.error("GraphQL failed:", e.message);
  }
}

testGH();
