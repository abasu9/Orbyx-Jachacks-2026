import { createClient } from '@insforge/sdk';
import * as dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Initialize the Insforge client using environment variables
const insforgeUrl = process.env.INSFORGE_URL || '';
const insforgeKey = process.env.INSFORGE_SERVICE_ROLE_KEY || ''; // Typically use a service role key for serverless backends

const insforge = createClient({
  baseUrl: insforgeUrl,
  anonKey: insforgeKey
});

/**
 * Serverless function handler.
 * Expected input in body: { "userId": "uuid-of-the-user" }
 */
export async function handler(request: Request): Promise<Response> {
  try {
    const { userId } = await request.json();

    if (!userId) {
      return new Response(JSON.stringify({ error: 'userId is required' }), { status: 400 });
    }

    // 1. Fetch user info from Insforge PostgreSQL
    const { data: user, error: userError } = await insforge.database
      .from('users')
      .select('*')
      .eq('id', userId)
      .single();

    if (userError || !user) {
      return new Response(JSON.stringify({ error: 'User not found or database error' }), { status: 404 });
    }

    // 2. Call an AI model using Insforge AI sdk
    // We define a strict JSON schema for the AI to return in the prompt.
    const prompt = `
      Analyze the following user profile and provide an evaluation.
      User data: ${JSON.stringify(user)}
      
      Provide your response strictly in the following JSON format without any markdown formatting or extra text:
      {
        "evaluationSummary": "string",
        "performanceScore": "number (1-10)",
        "recommendedAction": "string"
      }
    `;

    const { data: aiResponse, error: aiError } = await insforge.ai.chat.completions.create({
      model: 'gpt-4-turbo', // Or any supported model
      messages: [{ role: 'user', content: prompt }]
    });

    if (aiError) {
      return new Response(JSON.stringify({ error: 'AI generation failed', details: aiError }), { status: 500 });
    }

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

    // 3. Save the JSON file in the insforge storage bucket
    // Convert the parsed JSON to a Blob for uploading
    const jsonBlob = new Blob([JSON.stringify(jsonInsights, null, 2)], { type: 'application/json' });
    const filePath = `user-evaluations/${userId}}.json`;

    const { data: storageData, error: storageError } = await insforge
      .storage
      .from('evaluations-bucket') // Target your specific bucket here
      .upload(filePath, jsonBlob);

    if (storageError) {
      return new Response(JSON.stringify({ error: 'Failed to save to storage', details: storageError }), { status: 500 });
    }

    // Return successful response back to the invoker
    return new Response(JSON.stringify({
      message: 'Successfully generated and stored user evaluation',
      storagePath: filePath,
      evaluation: jsonInsights
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });

  } catch (error: any) {
    return new Response(JSON.stringify({ error: 'Internal Server Error', details: error.message }), { status: 500 });
  }
}
