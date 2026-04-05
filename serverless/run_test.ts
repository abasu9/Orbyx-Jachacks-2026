import { handler } from './user-report-generator/index.js';

async function runTest() {
  const req = {
    json: async () => ({
      id: "8ba9c5c8-dacb-4c81-a1ef-b40d7998a5fd"
    })
  } as unknown as Request;
  
  try {
    console.log("Invoking handler for ID: 8ba9c5c8-dacb-4c81-a1ef-b40d7998a5fd...");
    const res = await handler(req);
    console.log("Status Code:", res.status);
    
    let body;
    try {
        body = await res.json();
    } catch {
        body = await res.text();
    }
    console.log("Response Body:", body);
  } catch (err) {
    console.error("Execution Error:", err);
  }
}

runTest();
