import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import readline from 'readline';
import OpenAI from 'openai';
import { AcontextClient, FileUpload, SANDBOX_TOOLS } from '@acontext/acontext';

dotenv.config();

// Initialize OpenAI client
const oaiClient = new OpenAI({
  baseURL: process.env.OPENAI_BASE_URL,
  apiKey: process.env.OPENAI_API_KEY,
});

// Parse command line arguments
const args = process.argv.slice(2);
if (args.length < 1) {
  console.log('Usage: npm run dev -- <path_to_zip_file> [model_name]');
  process.exit(1);
}

const ZIP_PATH = args[0];
const MODEL_NAME = args[1] || 'gpt-4.1';

// Initialize Acontext client
const client = new AcontextClient({
  apiKey: process.env.ACONTEXT_API_KEY,
  // baseUrl: 'http://localhost:8029/api/v1',
});

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function prompt(question: string): Promise<string> {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer);
    });
  });
}

async function main(): Promise<void> {
  // Read the skill zip file
  const skillBin = fs.readFileSync(ZIP_PATH);
  const name = path.basename(ZIP_PATH);

  console.log(`Uploading skill: ${name}...`);

  // Upload the skill
  const skillResult = await client.skills.create({
    file: new FileUpload({
      filename: name,
      content: skillBin,
    }),
  });
  const skillName = skillResult.name;
  const skillId = skillResult.id;
  console.log(`Skill uploaded: ${skillName} (${skillId})`);

  // Create sandbox and disk
  console.log('Creating sandbox and disk...');
  const sandbox = await client.sandboxes.create();
  const disk = await client.disks.create();
  console.log(`Sandbox: ${sandbox.sandbox_id}, Disk: ${disk.id}`);

  try {
    // Create tool context with mounted skills
    const ctx = await SANDBOX_TOOLS.formatContext(
      client,
      sandbox.sandbox_id,
      disk.id,
      [skillId]
    );

    const tools = SANDBOX_TOOLS.toOpenAIToolSchema() as unknown as OpenAI.Chat.Completions.ChatCompletionTool[];
    const systemPrompt = `You are a helpful assistant with access to a secure sandbox environment.
You can execute bash commands, run Python scripts, and export files for the user.

${ctx.getContextPrompt()}`;

    let messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [];
    const maxIterations = 20;

    console.log('\n--- Sandbox Ready ---');
    console.log("Type your requests (or 'quit' to exit, 'reset' to clear history)");
    console.log('-'.repeat(50));

    // Main interaction loop
    while (true) {
      let userInput: string;
      try {
        userInput = (await prompt('\nYou: ')).trim();
      } catch {
        console.log('\nExiting...');
        break;
      }

      if (!userInput) {
        continue;
      }

      if (userInput.toLowerCase() === 'quit') {
        break;
      }

      if (userInput.toLowerCase() === 'reset') {
        messages = [];
        console.log('Conversation history cleared.');
        continue;
      }

      // Add user message
      messages.push({ role: 'user', content: userInput });
      console.log('\nAgent working...');

      // Agentic loop
      for (let iteration = 0; iteration < maxIterations; iteration++) {
        console.log(`\n[Iteration ${iteration + 1}]`);

        const response = await oaiClient.chat.completions.create({
          model: MODEL_NAME,
          messages: [{ role: 'system', content: systemPrompt }, ...messages],
          tools: tools.length > 0 ? tools : undefined,
          tool_choice: 'auto',
        });

        const assistantMessage = response.choices[0].message;

        // Check if we're done (no tool calls)
        if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
          const finalResponse = assistantMessage.content || '';
          messages.push({ role: 'assistant', content: finalResponse });
          console.log(`\nAgent: ${finalResponse}`);
          break;
        }

        // Process tool calls - filter for function type tool calls
        const functionToolCalls = assistantMessage.tool_calls.filter(
          (tc): tc is OpenAI.Chat.Completions.ChatCompletionMessageToolCall & { type: 'function' } =>
            tc.type === 'function'
        );

        messages.push({
          role: 'assistant',
          content: assistantMessage.content,
          tool_calls: functionToolCalls.map((tc) => ({
            id: tc.id,
            type: 'function' as const,
            function: {
              name: tc.function.name,
              arguments: tc.function.arguments,
            },
          })),
        });

        for (const toolCall of functionToolCalls) {
          const toolName = toolCall.function.name;
          const toolArgs = JSON.parse(toolCall.function.arguments);

          console.log(`  Tool: ${toolName}`);
          console.log(`  Args: ${JSON.stringify(toolArgs, null, 2)}`);

          // Execute the tool
          let result: string;
          try {
            result = await SANDBOX_TOOLS.executeTool(ctx, toolName, toolArgs);
          } catch (e) {
            result = JSON.stringify({ error: String(e) });
          }

          const displayResult = result.length > 200 ? `${result.slice(0, 200)}...` : result;
          console.log(`  Result: ${displayResult}`);

          // Add tool result to messages
          messages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            content: result,
          });
        }

        // Check if we've reached max iterations
        if (iteration === maxIterations - 1) {
          console.log('Max iterations reached. Task may be incomplete.');
        }
      }
    }
  } finally {
    // Cleanup: kill the sandbox
    console.log('\nCleaning up sandbox...');
    await client.sandboxes.kill(sandbox.sandbox_id);
    rl.close();
    console.log('Done.');
  }
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
