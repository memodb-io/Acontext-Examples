import dotenv from 'dotenv';
import { generateText, tool } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { z } from 'zod';
import { AcontextClient } from '@acontext/acontext';

dotenv.config();

// Initialize Acontext client
const acontextClient = new AcontextClient({
  apiKey: process.env.ACONTEXT_API_KEY || 'sk-ac-your-root-api-bearer-token',
  baseUrl: process.env.ACONTEXT_BASE_URL || 'http://localhost:8029/api/v1',
  timeout: 60000,
});

// Tool implementations
function getWeather(city: string): string {
  return `The weather in ${city} is sunny`;
}

function bookFlight(fromCity: string, toCity: string, date: string): string {
  return `Flight booked successfully for '${fromCity}' to '${toCity}' on '${date}'`;
}

function executeTool(toolName: string, toolArgs: Record<string, any>): string {
  if (toolName === 'get_weather') {
    return getWeather(toolArgs.city);
  } else if (toolName === 'book_flight') {
    return bookFlight(toolArgs.from_city, toolArgs.to_city, toolArgs.date);
  } else {
    return `Unknown tool: ${toolName}`;
  }
}

// Tool definitions using Vercel AI SDK
// Tools must include an execute function that performs the actual tool logic
const tools = {
  get_weather: tool({
    description: 'Returns weather info for the specified city.',
    inputSchema: z.object({
      city: z.string().describe('The city to get weather for'),
    }),
    execute: async ({ city }: { city: string }) => {
      return getWeather(city);
    },
  }),
  book_flight: tool({
    description: 'Book a flight.',
    inputSchema: z.object({
      from_city: z.string().describe('The departure city'),
      to_city: z.string().describe('The destination city'),
      date: z.string().describe('The date of the flight'),
    }),
    execute: async ({ from_city, to_city, date }: { from_city: string; to_city: string; date: string }) => {
      return bookFlight(from_city, to_city, date);
    },
  }),
};

// Create OpenAI provider instance with configuration
const openaiProvider = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL,
});

function createModel() {
  return openaiProvider('gpt-4o-mini');
}

async function appendMessage(
  message: any,
  conversation: any[],
  sessionId: string
): Promise<any[]> {
  conversation.push(message);
  await acontextClient.sessions.storeMessage(sessionId, message, {
    format: 'openai',
  });
  return conversation;
}

async function runAgent(
  conversation: any[]
): Promise<[string, any[]]> {
  // Separate system message from conversation messages
  // Filter out system messages and tool messages, build initial message list
  // Vercel AI SDK v5 only accepts 'user' and 'assistant' roles in messages
  let messagesToSend: any[] = conversation.filter((msg: any) => {
    const role = msg.role;
    return role === 'user' || role === 'assistant';
  });
  const systemMessage = conversation.find((msg: any) => msg.role === 'system')?.content || 'You are a helpful assistant';

  const newMessages: any[] = [];
  const maxIterations = 10;
  let iteration = 0;
  let finalContent = '';

  while (iteration < maxIterations) {
    iteration += 1;

    const model = createModel();

    // Convert messages to Vercel AI SDK format
    // Ensure content is always a string (not array) for user and assistant messages
    // Vercel AI SDK only accepts 'user' and 'assistant' roles in messages array
    // Filter out internal messages that shouldn't be sent to Acontext
    const currentMessages = messagesToSend
      .filter((msg: any) => {
        // Only include user and assistant messages, and exclude internal messages
        const role = msg.role;
        return (role === 'user' || role === 'assistant') && !msg._internal;
      })
      .map((msg: any) => {
        // Ensure content is a string, not an array
        let content = msg.content;
        if (Array.isArray(content)) {
          // If content is an array, extract text from it
          content = content.map((item: any) =>
            typeof item === 'string' ? item : item.text || item.content || ''
          ).join(' ');
        }
        if (typeof content !== 'string') {
          content = String(content || '');
        }

        // Return only role and content (Vercel AI SDK format)
        return {
          role: msg.role,
          content: content,
        };
      });

    // Also include internal messages for the current generateText call
    // These are tool results converted to user messages
    const internalMessages = messagesToSend
      .filter((msg: any) => msg._internal === true)
      .map((msg: any) => ({
        role: msg.role,
        content: String(msg.content || ''),
      }));

    // Combine regular messages with internal messages
    const allMessages = [...currentMessages, ...internalMessages];

    const result = await generateText({
      model,
      system: systemMessage,
      messages: allMessages,
      tools,
    });

    // Convert result to message format
    const messageDict: any = {
      role: 'assistant',
      content: result.text,
    };

    // Handle tool calls
    const toolCallsWithFunction: Array<{
      id: string;
      function: { name: string; arguments: string };
    }> = [];

    if (result.toolCalls && result.toolCalls.length > 0) {
      messageDict.tool_calls = result.toolCalls.map((tc: any) => {
        // Get arguments from tool call - Vercel AI SDK may use different field names
        let args = tc.args;
        if (args === undefined || args === null) {
          // Try alternative field names that Vercel AI SDK might use
          args = tc.parameters || tc.input || {};
        }

        // Ensure args is an object, not a string
        if (typeof args === 'string') {
          try {
            args = JSON.parse(args);
          } catch {
            args = {};
          }
        }

        // Ensure args is always an object (not null or undefined)
        if (!args || typeof args !== 'object') {
          args = {};
        }

        // Convert to JSON string - always return a valid JSON string
        const argsString = JSON.stringify(args);

        // Store function info for execution
        toolCallsWithFunction.push({
          id: tc.toolCallId,
          function: {
            name: tc.toolName,
            arguments: argsString,
          },
        });

        return {
          id: tc.toolCallId,
          type: 'function',
          function: {
            name: tc.toolName,
            arguments: argsString,
          },
        };
      });
    }

    // Add assistant message (filter system if any)
    const assistantMsg = { ...messageDict };
    if (assistantMsg.role !== 'system') {
      messagesToSend.push(assistantMsg);
    }
    newMessages.push(messageDict);

    // If there are no tool calls, we're done
    if (!result.toolCalls || result.toolCalls.length === 0) {
      finalContent = result.text || '';
      break;
    }

    // Execute tool calls manually
    // Even though tools have execute functions, we still need to handle tool results
    // and pass them back to the model in a format it can understand
    const toolResults: Array<{ toolName: string; result: string; toolCallId: string }> = [];

    for (const toolCallInfo of toolCallsWithFunction) {
      const functionName = toolCallInfo.function.name;
      const functionArgsStr = toolCallInfo.function.arguments || '{}';
      const functionArgs = JSON.parse(functionArgsStr);

      // Execute the function
      const functionResult = executeTool(functionName, functionArgs);
      toolResults.push({ toolName: functionName, result: functionResult, toolCallId: toolCallInfo.id });

      // Create tool message for Acontext compatibility
      const toolMessage = {
        role: 'tool' as const,
        tool_call_id: toolCallInfo.id,
        content: functionResult,
      };
      newMessages.push(toolMessage);
    }

    // If we have tool results, we need to continue the conversation
    // Vercel AI SDK doesn't support 'tool' role in messages, so we convert tool results
    // to a user message format for the next iteration, but we mark it so it won't be sent to Acontext
    if (toolResults.length > 0) {
      const toolResultsText = toolResults
        .map(tr => `${tr.toolName} returned: ${tr.result}`)
        .join('\n');

      // Add tool results as a user message for the next generateText call
      // This is an internal message, not sent to Acontext
      const toolResultUserMessage = {
        role: 'user' as const,
        content: `Tool execution results:\n${toolResultsText}`,
        // Mark as internal so it won't be sent to Acontext
        _internal: true,
      };
      messagesToSend.push(toolResultUserMessage);

      // Continue the loop to get the model's response based on tool results
      // Don't break here, let the loop continue
    }
  }

  return [finalContent, newMessages];
}

async function session1(sessionId: string): Promise<void> {
  // Build conversation history using OpenAI message format
  // This format works with both OpenAI and Acontext
  let conversation: any[] = [];

  // First interaction - ask for trip plan
  console.log('\n=== First interaction: Planning trip ===');
  const userMsg1 = {
    role: 'user',
    content:
      "I'd like to have a 3-day trip in Finland. I like to see the nature. Give me the plan",
  };
  conversation = await appendMessage(userMsg1, conversation, sessionId);

  const [responseContent, newMessages] = await runAgent(conversation);
  console.log(`\nAssistant: ${responseContent}`);

  for (const msg of newMessages) {
    conversation = await appendMessage(msg, conversation, sessionId);
  }

  // Second interaction - check weather
  console.log('\n\n=== Second interaction: Checking weather ===');
  conversation = await appendMessage(
    {
      role: 'user',
      content: 'The plan sounds good, check the weather there',
    },
    conversation,
    sessionId
  );

  const [responseContent2, newMessages2] = await runAgent(conversation);
  console.log(`\nAssistant: ${responseContent2}`);

  for (const msg of newMessages2) {
    conversation = await appendMessage(msg, conversation, sessionId);
  }

  // Third interaction - book flight
  console.log('\n\n=== Third interaction: Booking flight ===');
  conversation = await appendMessage(
    {
      role: 'user',
      content:
        'The weather is good, I am in Shanghai now, let\'s book the flight, you should just call the tool and don\'t ask me for more information. Remember, I only want the cheapest flight.',
    },
    conversation,
    sessionId
  );

  const [responseContent3, newMessages3] = await runAgent(conversation);
  console.log(`\nAssistant: ${responseContent3}`);

  for (const msg of newMessages3) {
    conversation = await appendMessage(msg, conversation, sessionId);
  }

  await appendMessage(
    {
      role: 'user',
      content: 'cool, everything is done, thank you!',
    },
    conversation,
    sessionId
  );

  console.log(
    `Saved ${conversation.length} messages in conversation, waiting for tasks extraction...`
  );

  // Flush and get tasks
  await acontextClient.sessions.flush(sessionId);
  const tasksResponse = await acontextClient.sessions.getTasks(sessionId);

  console.log('\n=== Extracted Tasks ===');
  for (const task of tasksResponse.items) {
    console.log(`\nTask #${task.order}:`);
    console.log(`  ID: ${task.id}`);
    console.log(`  Title: ${task.data.task_description}`);
    console.log(`  Status: ${task.status}`);

    // Show progress updates if available
    if (task.data.progresses) {
      console.log(`  Progress updates: ${task.data.progresses.length}`);
      for (const progress of task.data.progresses) {
        console.log(`    - ${progress}`);
      }
    }

    // Show user preferences if available
    if (task.data.user_preferences) {
      console.log('  User preferences:');
      for (const pref of task.data.user_preferences) {
        console.log(`    - ${pref}`);
      }
    }
  }
}

async function session2(sessionId: string): Promise<void> {
  const messages = await acontextClient.sessions.getMessages(sessionId, {
    format: 'openai',
  });
  const conversation: any[] = messages.items;
  conversation.push({
    role: 'user',
    content: 'Summarize the conversation so far',
  });

  const [responseContent] = await runAgent(conversation);
  console.log(`\nAssistant: ${responseContent}`);
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main(): Promise<void> {
  const space = await acontextClient.spaces.create();
  const spaceId = space.id;
  console.log(`Created space: ${spaceId}`);

  const session = await acontextClient.sessions.create({ spaceId });
  const sessionId = session.id;
  console.log(`Created session: ${sessionId}`);

  console.log('\n=== Session 1 ===');
  await session1(sessionId);

  console.log('\n=== Session 2, get messages from Acontext and continue ===');
  await session2(sessionId);

  console.log('\n=== Experiences from Acontext ===');
  console.log('Waiting for the agent learning');
  while (true) {
    const status = await acontextClient.sessions.getLearningStatus(sessionId);
    if (status.not_space_digested_count === 0) {
      break;
    }
    await sleep(1000);
    process.stdout.write('.');
  }
  console.log('\n');
  const experienceResult = await acontextClient.spaces.experienceSearch(
    spaceId,
    {
      query: 'travel with flight',
      mode: 'fast',
    }
  );
  console.log(JSON.stringify(experienceResult, null, 2));
}

main().catch(console.error);
