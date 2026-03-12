import fs from 'fs';
import { AcontextClient, ClaudeAgentStorage } from '@acontext/acontext';
import { query } from '@anthropic-ai/claude-agent-sdk';

const client = new AcontextClient({ apiKey: 'sk-ac-your-api-key' });
const storage = new ClaudeAgentStorage({ client });

const q = query({
    prompt: 'What is the capital of France?',
    options: {
        extraArgs: { "replay-user-messages": null }, // include UserMessage in stream
    }
});
for await (const message of q) {
    await storage.saveMessage(message);
}

// Get the session ID from storage
const sessionId = storage.sessionId!;
console.log(`Session ID: ${sessionId}`);

// Create a learning space and trigger learning
const space = await client.learningSpaces.create();
await client.learningSpaces.learn({ spaceId: space.id, sessionId });
console.log(`Created learning space: ${space.id}`);

// Wait for learning to complete
console.log('Waiting for learning to complete...');
const learnResult = await client.learningSpaces.waitForLearning({ spaceId: space.id, sessionId });
console.log(`Learning status: ${learnResult.status}`);

// List learned skills
const skills = await client.learningSpaces.listSkills(space.id);
console.log(`\n=== Learned Skills (${skills.length}) ===`);
for (const skill of skills) {
    console.log(`  - ${skill.name}: ${skill.description}`);
    console.log(`    files: ${skill.file_index.map((f: any) => f.path)}`);
}

// Download all skill files
const downloadDir = './skills_output';
if (fs.existsSync(downloadDir)) {
    fs.rmSync(downloadDir, { recursive: true });
}

console.log(`\nDownloading skills to ${downloadDir}/`);
for (const skill of skills) {
    const resp = await client.skills.download(skill.id, { path: `${downloadDir}/${skill.name}` });
    console.log(`  ${resp.name} -> ${resp.dirPath}`);
    for (const f of resp.files) {
        console.log(`    ${f}`);
    }
}