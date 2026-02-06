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