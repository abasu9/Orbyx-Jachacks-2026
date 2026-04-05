import { Octokit } from 'octokit';
import * as dotenv from 'dotenv';
dotenv.config();

async function listRepos() {
  const token = process.env.GITHUB_ORG_OAUTH_TOKEN || '';
  const octokit = new Octokit({ auth: token });
  
  try {
    const { data } = await octokit.rest.repos.listForAuthenticatedUser({
      sort: 'updated',
      per_page: 10
    });
    console.log("Accessible Repositories:");
    data.forEach(repo => console.log(`- ${repo.full_name}`));
  } catch (e: any) {
    console.error("Failed to list repos:", e.message);
  }
}

listRepos();
