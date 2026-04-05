import { Octokit } from 'octokit';

export interface GithubMetrics {
  total_prs: number;
  merged_prs: number;
  merge_rate: number;
  avg_pr_size: number;
  review_participation_rate: number;
  commit_frequency_per_week: number;
  active_days_ratio: number;
  top_languages: string[];
  high_impact_pr_ratio: number;
}

export async function fetchGithubMetrics(username: string, org: string, token: string): Promise<GithubMetrics> {
  const octokit = new Octokit({ auth: token });

  const headers = {
    'X-GitHub-Api-Version': '2026-03-10'
  };

  try {
    // 1. Fetch total PRs
    const totalPrsResponse = await octokit.rest.search.issuesAndPullRequests({
      q: `is:pr author:${username} org:${org}`,
      per_page: 30, // fetch some PRs for sampling
      headers
    });
    const total_prs = totalPrsResponse.data.total_count;

    // 2. Fetch merged PRs
    const mergedPrsResponse = await octokit.rest.search.issuesAndPullRequests({
      q: `is:pr author:${username} org:${org} is:merged`,
      per_page: 1,
      headers
    });
    const merged_prs = mergedPrsResponse.data.total_count;
    const merge_rate = total_prs > 0 ? merged_prs / total_prs : 0;

    // 3. Fetch reviewed PRs (for participation rate)
    // How many PRs in the org did this user review?
    const reviewedPrsResponse = await octokit.rest.search.issuesAndPullRequests({
      q: `is:pr reviewed-by:${username} org:${org}`,
      per_page: 1,
      headers
    });
    const reviewed_prs = reviewedPrsResponse.data.total_count;

    // An estimate of review participation rate (reviewed / total PRs in org is hard to get,
    // so we compare it against their own PRs or use a reasonable proxy for MVP)
    const review_participation_rate = total_prs > 0 ? Math.min(reviewed_prs / total_prs, 1) : 0;

    // 4. Fetch commits to calculate frequency and active days
    const commitsResponse = await octokit.rest.search.commits({
      q: `author:${username} org:${org}`,
      sort: 'author-date',
      order: 'desc',
      per_page: 100, // sample up to 100 recent commits
      headers
    });

    const total_commits = commitsResponse.data.total_count;
    const commit_frequency_per_week = Math.round(total_commits / 52); // Estimate over a year for MVP

    // Calculate active days ratio from sampled commits
    const commitDates = new Set(
      commitsResponse.data.items.map((item: any) => {
        const date = new Date(item.commit.author.date);
        return date.toISOString().split('T')[0];
      })
    );
    const active_days = commitDates.size;
    // Assuming a 90 day sample period for active days ratio
    const active_days_ratio = Math.min(active_days / 90, 1);

    // 5. Sample PR data for sizes and impact
    let total_additions = 0;
    let high_impact_count = 0;
    const languages = new Set<string>();

    const prItems = totalPrsResponse.data.items;

    // Process PR samples to gather detailed stats
    for (const item of prItems) {
      if (item.repository_url) {
        // Extract repo name from url (e.g. https://api.github.com/repos/org/repo)
        const parts = item.repository_url.split('/');
        const repoName = parts[parts.length - 1];

        try {
          const prDetails = await octokit.rest.pulls.get({
            owner: org,
            repo: repoName,
            pull_number: item.number,
            headers
          });

          const size = prDetails.data.additions + prDetails.data.deletions;
          total_additions += size;

          if (size > 500) {
            high_impact_count++;
          }

          if (prDetails.data.base?.repo?.language) {
            languages.add(prDetails.data.base.repo.language);
          }
        } catch (e) {
          // Ignore if PR details cannot be fetched
        }
      }
    }

    const avg_pr_size = prItems.length > 0 ? Math.round(total_additions / prItems.length) : 0;
    const high_impact_pr_ratio = prItems.length > 0 ? high_impact_count / prItems.length : 0;

    return {
      total_prs,
      merged_prs,
      merge_rate: Number(merge_rate.toFixed(2)),
      avg_pr_size,
      review_participation_rate: Number(review_participation_rate.toFixed(2)),
      commit_frequency_per_week,
      active_days_ratio: Number(active_days_ratio.toFixed(2)),
      top_languages: Array.from(languages).filter(Boolean).slice(0, 3),
      high_impact_pr_ratio: Number(high_impact_pr_ratio.toFixed(2)),
    };
  } catch (error) {
    console.error('Error fetching GitHub metrics:', error);
    // Return a fallback or throw if necessary for the MVP
    throw new Error('Failed to aggregate GitHub metrics');
  }
}
