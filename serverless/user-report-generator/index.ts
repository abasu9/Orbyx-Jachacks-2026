import { createClient } from '@insforge/sdk';
import * as dotenv from 'dotenv';
import { fetchGithubMetrics } from './github';

// Load environment variables from .env file
dotenv.config();

// Initialize the Insforge client using environment variables
const insforgeUrl = process.env.INSFORGE_URL || '';
const insforgeKey = process.env.INSFORGE_ANON_KEY || ''; // Typically use a service role key for serverless backends
const githubToken = process.env.GITHUB_ORG_OAUTH_TOKEN || '';
const githubOrg = process.env.GITHUB_ORG || '';

const insforge = createClient({
  baseUrl: insforgeUrl,
  anonKey: insforgeKey
});

// Corrected response types for Insforge AI SDK
export interface ToolCall {
  id: string;
  type: 'function';
  function: { name: string; arguments: string };
}

export interface UrlCitationAnnotation {
  type: 'url_citation';
  urlCitation: {
    url: string;
    title?: string;
    content?: string;
    startIndex?: number;
    endIndex?: number;
  };
}

export interface AiResponse {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: [{
    index: number;
    message: {
      role: 'assistant';
      content: string;
      tool_calls?: ToolCall[];
      annotations?: UrlCitationAnnotation[];
    };
    finish_reason: string;
  }];
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number; };
}

export interface User {
  id: string;
  name: string;
  apr: number[];
  pip: number;
  joiningDate: string;
  rank: number;
  gh_username: string;
  report_id?: string;
}

/**
 * Serverless function handler.
 * Expected input in body: { "id": "uuid" }
 */
export async function handler(request: Request): Promise<Response> {
  try {
    const { id } = await request.json();
    if (!id) {
      return new Response(JSON.stringify({ error: 'id is required in the request body' }), { status: 400 });
    }
    if (!githubToken || !githubOrg) {
      return new Response(JSON.stringify({ error: 'GITHUB_ORG_OAUTH_TOKEN or GITHUB_ORG is not set in environment' }), { status: 500 });
    }

    // 1. Fetch user info from Insforge PostgreSQL
    const { data, error: userError } = await insforge.database
      .from('users')
      .select('*')
      .eq('id', id)
      .single();

    const user = data as User | null;

    if (userError || !user) {
      return new Response(JSON.stringify({ error: 'User not found or database error' }), { status: 404 });
    }

    if (!user.gh_username) {
      return new Response(JSON.stringify({ error: 'User record is missing a gh_username' }), { status: 400 });
    }

    // 2. Fetch Github Contribution History
    const githubMetrics = await fetchGithubMetrics(user.gh_username, githubOrg, githubToken);

    // 3. Call an AI model using Insforge AI sdk
    // We define a strict JSON schema for the AI to return in the prompt.
    const prompt = `
      You are an engineering performance analyst.

      You are given structured contribution metrics for a software engineer within an organization over a fixed time window.

      Your task is to produce an objective, evidence-based evaluation of the engineer.
      Use third person addressing eg. "John demonstrates a steady pattern of commits with a commit frequency per week of 7"

      GitHub Username: ${JSON.stringify(user)}
      GitHub Metrics: ${JSON.stringify(githubMetrics)}

      STRICT RULES:
      - Use ONLY the provided metrics. Do NOT assume or infer missing data.
      - If a signal is missing (e.g., review timing), explicitly acknowledge the limitation.
      - Do NOT generalize beyond what the data supports.
      - Avoid vague or generic statements.
      - Every assessment must be justified using specific metrics.
      - Be concise, analytical, and neutral in tone.

      EVALUATION DIMENSIONS:

      1. Impact
        - Use: total_prs, merged_prs, merge_rate, high_impact_pr_ratio
        - Focus on delivery effectiveness and contribution to main codebase

      2. Code Quality Signals
        - Use: avg_pr_size, merge_rate
        - Large PRs may indicate risk unless offset by high merge rate

      3. Collaboration
        - Use: review_participation_rate
        - Do NOT assume responsiveness or speed

      4. Consistency
        - Use: commit_frequency_per_week, active_days_ratio
        - Evaluate regularity vs bursty behavior

      5. Seniority Signal
        - Infer cautiously using:
          - high_impact_pr_ratio
          - review_participation_rate
          - merge_rate
        - Do NOT overstate confidence

      EDGE CASE HANDLING:
      - If metrics are borderline or conflicting, reflect that uncertainty
      - If values are low across the board, state low impact clearly
      - If values are high but narrow (e.g., high commits but low reviews), call out imbalance

      OUTPUT REQUIREMENTS:
      - Return ONLY valid JSON
      - Follow the exact schema provided
      - Do NOT include any extra fields
      - Do NOT include explanations outside JSON

      Provide your response strictly in the following JSON format without any markdown formatting or extra text:
      {
        "summary": "string",

        "impact_assessment": {
          "level": "low | medium | high",
          "justification": "string"
        },

        "code_quality_signals": {
          "assessment": "string",
          "risk_flags": ["string"]
        },

        "collaboration": {
          "assessment": "string",
          "review_strength": "low | medium | high"
        },

        "consistency": {
          "assessment": "string",
          "pattern": "sporadic | steady | highly_consistent"
        },

        "seniority_signal": {
          "level": "junior | mid | senior | staff",
          "confidence": 0.0
        },

        "strengths": ["string"],
        "weaknesses": ["string"],
      }
    `;

    const aiResponse = (await insforge.ai.chat.completions.create({
      model: 'openai/gpt-4o-mini', // Or any supported model
      messages: [{ role: 'user', content: prompt }],
    })) as AiResponse;

    // Extract and parse the JSON string returned by the AI
    let aiContent = aiResponse.choices[0].message.content;

    // Clean up potential markdown formatting if the AI still included it
    if (aiContent.startsWith('```json')) {
      aiContent = aiContent.replace(/```json/g, '').replace(/```/g, '').trim();
    }

    let jsonInsights;
    try {
        jsonInsights = JSON.parse(aiContent);
    } catch (parseError) {
        return new Response(JSON.stringify({ error: 'Failed to parse AI response as JSON', content: aiContent }), { status: 500 });
    }

    // 4. Save the JSON file in the insforge storage bucket
    // Convert the parsed JSON to a Blob for uploading
    const jsonBlob = new Blob([JSON.stringify(jsonInsights, null, 2)], { type: 'application/json' });
    const newReportId = `${user.id}-${Date.now()}.json`;

    // If the user already has a report_id, remove the old file first
    if (user.report_id) {
      await insforge.storage.from('reports').remove(user.report_id);
    }

    const { data: storageData, error: storageError } = await insforge.storage
      .from('reports') // Target your specific bucket here
      .upload(newReportId, jsonBlob);

    if (storageError) {
      return new Response(JSON.stringify({ error: 'Failed to save to storage', details: storageError }), { status: 500 });
    }

    // Update the user's report_id in the database
    const { error: dbUpdateError } = await insforge.database
      .from('users')
      .update({ report_id: newReportId })
      .eq('id', user.id);

    if (dbUpdateError) {
      return new Response(JSON.stringify({ error: 'Failed to update user record with new report_id', details: dbUpdateError }), { status: 500 });
    }

    // Return successful response back to the invoker
    return new Response(JSON.stringify({
      message: 'Successfully generated and stored user evaluation',
      storagePath: newReportId,
      githubMetrics: githubMetrics,
      evaluation: jsonInsights
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });

  } catch (error: any) {
    return new Response(JSON.stringify({ error: 'Internal Server Error', details: error.message }), { status: 500 });
  }
}
